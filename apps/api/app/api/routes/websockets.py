import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import decode_session_token
from app.db.database import SessionLocal
from app.db.models import AiDecision, BotDecision, BotRun, Notification, Position, ScriptLog, ScriptRun, SystemLog, WatchTask
from app.services.ws_manager import ws_manager

router = APIRouter(tags=["websockets"])


async def _ensure_ws_auth(websocket: WebSocket) -> bool:
    token = websocket.cookies.get(get_settings().session_cookie_name)
    user_id = decode_session_token(token) if token else None
    if not user_id:
        await websocket.close(code=4401)
        return False
    return True


@router.websocket("/ws/ai-decisions")
async def ws_ai_decisions(websocket: WebSocket) -> None:
    if not await _ensure_ws_auth(websocket):
        return
    await websocket.accept()
    seen_id = 0
    try:
        while True:
            with SessionLocal() as db:
                rows = db.scalars(select(AiDecision).where(AiDecision.id > seen_id).order_by(AiDecision.id.asc()).limit(20)).all()
                for row in rows:
                    seen_id = max(seen_id, row.id)
                    await websocket.send_json({"type": "ai_decision", "payload": {"id": row.id, "symbol": row.symbol, "action": row.action, "confidence": row.confidence, "reason": row.reason}})
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        return


@router.websocket("/ws/bots/{bot_run_id}")
async def ws_bot_run(websocket: WebSocket, bot_run_id: int) -> None:
    if not await _ensure_ws_auth(websocket):
        return
    await websocket.accept()
    seen_decision_id = 0
    seen_watch_id = 0
    try:
        while True:
            with SessionLocal() as db:
                run = db.get(BotRun, bot_run_id)
                await websocket.send_json({"type": "bot_status", "payload": {"bot_run_id": bot_run_id, "status": run.status if run else "UNKNOWN", "error_message": run.error_message if run else None}})
                decisions = db.scalars(select(BotDecision).where(BotDecision.bot_run_id == bot_run_id, BotDecision.id > seen_decision_id).order_by(BotDecision.id.asc())).all()
                for row in decisions:
                    seen_decision_id = max(seen_decision_id, row.id)
                    await websocket.send_json({"type": "bot_decision", "payload": {"id": row.id, "symbol": row.symbol, "action": row.action, "confidence": row.confidence, "reason": row.reason, "executed": row.executed}})
                watch_rows = db.scalars(select(WatchTask).where(WatchTask.bot_run_id == bot_run_id, WatchTask.id > seen_watch_id).order_by(WatchTask.id.asc())).all()
                for row in watch_rows:
                    seen_watch_id = max(seen_watch_id, row.id)
                    await websocket.send_json({"type": "watch_task", "payload": {"id": row.id, "symbol": row.symbol, "status": row.status, "watch_type": row.type, "trigger_price": row.trigger_price}})
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        return


@router.websocket("/ws/positions")
async def ws_positions(websocket: WebSocket) -> None:
    if not await _ensure_ws_auth(websocket):
        return
    await websocket.accept()
    seen_notification_id = 0
    try:
        while True:
            with SessionLocal() as db:
                positions = db.scalars(select(Position).where(Position.status == "OPEN").order_by(Position.opened_at.desc()).limit(20)).all()
                await websocket.send_json(
                    {
                        "type": "positions",
                        "payload": [
                            {"id": item.id, "symbol": item.symbol, "current_price": item.current_price, "take_profit": item.take_profit, "stop_loss": item.stop_loss}
                            for item in positions
                        ],
                    }
                )
                notifications = db.scalars(select(Notification).where(Notification.id > seen_notification_id).order_by(Notification.id.asc()).limit(20)).all()
                for item in notifications:
                    seen_notification_id = max(seen_notification_id, item.id)
                    if item.type in {"tp_hit", "sl_hit", "position_closed", "close_failed"}:
                        await websocket.send_json({"type": "position_event", "payload": {"id": item.id, "title": item.title, "message": item.message}})
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        return


@router.websocket("/ws/scripts/{run_id}")
async def ws_script_run(websocket: WebSocket, run_id: int) -> None:
    if not await _ensure_ws_auth(websocket):
        return
    await ws_manager.connect("scripts", websocket, topic=str(run_id))
    try:
        with SessionLocal() as db:
            run = db.get(ScriptRun, run_id)
            if run:
                await websocket.send_json(
                    {
                        "channel": "scripts",
                        "event": "script_run_state",
                        "payload": {
                            "id": run.id,
                            "status": run.status,
                            "pid": run.pid,
                            "started_at": run.started_at.isoformat(),
                            "stopped_at": run.stopped_at.isoformat() if run.stopped_at else None,
                            "exit_code": run.exit_code,
                            "error_message": run.error_message,
                        },
                    }
                )
                logs = db.scalars(select(ScriptLog).where(ScriptLog.script_run_id == run_id).order_by(ScriptLog.created_at.asc(), ScriptLog.id.asc())).all()
                for item in logs[-200:]:
                    await websocket.send_json(
                        {
                            "channel": "scripts",
                            "event": "script_log",
                            "payload": {
                                "id": item.id,
                                "script_run_id": item.script_run_id,
                                "stream": item.stream,
                                "line": item.line,
                                "created_at": item.created_at.isoformat(),
                            },
                        }
                    )
        while True:
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        await ws_manager.disconnect("scripts", websocket, topic=str(run_id))


@router.websocket("/ws/notifications")
async def ws_notifications(websocket: WebSocket) -> None:
    if not await _ensure_ws_auth(websocket):
        return
    await ws_manager.connect("notifications", websocket)
    try:
        with SessionLocal() as db:
            latest = db.scalars(select(Notification).order_by(Notification.created_at.desc()).limit(20)).all()
            for item in reversed(latest):
                await websocket.send_json(
                    {
                        "channel": "notifications",
                        "event": "notification_snapshot",
                        "payload": {
                            "id": item.id,
                            "type": item.type,
                            "severity": item.severity,
                            "title": item.title,
                            "message": item.message,
                            "is_read": item.is_read,
                            "metadata_json": item.metadata_json,
                            "created_at": item.created_at.isoformat(),
                        },
                    }
                )
        while True:
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        await ws_manager.disconnect("notifications", websocket)


@router.websocket("/ws/system-logs")
async def ws_system_logs(websocket: WebSocket) -> None:
    if not await _ensure_ws_auth(websocket):
        return
    await ws_manager.connect("system_logs", websocket)
    try:
        with SessionLocal() as db:
            latest = db.scalars(select(SystemLog).order_by(SystemLog.created_at.desc()).limit(50)).all()
            for item in reversed(latest):
                await websocket.send_json(
                    {
                        "channel": "system_logs",
                        "event": "system_log_snapshot",
                        "payload": {
                            "id": item.id,
                            "level": item.level,
                            "source": item.source,
                            "message": item.message,
                            "metadata_json": item.metadata_json,
                            "created_at": item.created_at.isoformat(),
                        },
                    }
                )
        while True:
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        await ws_manager.disconnect("system_logs", websocket)
