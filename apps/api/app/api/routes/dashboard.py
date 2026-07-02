from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.database import get_db
from app.db.models import AiDecision, ApiAccount, BotConfig, BotDecision, BotRun, Notification, Position, ScriptRun, SystemLog, Trade, User, WatchTask
from app.schemas.dashboard import ActiveApiAccountSummary, DashboardLogItem, DashboardResponse
from app.services.report_service import report_service
from app.services.account_service import get_active_credentials
from app.services.tabdeal_client import TabdealClient

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    active_account = db.scalar(select(ApiAccount).where(ApiAccount.is_active.is_(True)))
    latest_logs = db.scalars(select(SystemLog).order_by(SystemLog.created_at.desc()).limit(8)).all()
    unread_count = len(db.scalars(select(Notification).where(Notification.is_read.is_(False))).all())
    settings = get_settings()

    api_status = "not_configured"
    openai_status = "not_configured"
    active_summary = None
    balances: list[dict] = []
    open_orders: list[dict] = []
    open_positions = [
        {
            "id": item.id,
            "symbol": item.symbol,
            "quantity": item.quantity,
            "entry_price": item.entry_price,
            "current_price": item.current_price,
            "pnl": item.pnl,
            "status": item.status,
        }
        for item in db.scalars(select(Position).where(Position.status == "OPEN").order_by(Position.opened_at.desc()).limit(8)).all()
    ]
    latest_trades = [
        {
            "id": item.id,
            "symbol": item.symbol,
            "side": item.side,
            "quantity": item.quantity,
            "price": item.price,
            "mode": item.mode,
            "created_at": item.created_at.isoformat(),
        }
        for item in db.scalars(select(Trade).order_by(Trade.created_at.desc()).limit(8)).all()
    ]
    active_bots = [
        {"id": item.id, "name": item.name, "mode": item.mode, "strategy_name": item.strategy_name}
        for item in db.scalars(select(BotConfig).where(BotConfig.is_active.is_(True)).order_by(BotConfig.updated_at.desc()).limit(8)).all()
    ]
    active_watches = [
        {"id": item.id, "symbol": item.symbol, "type": item.type, "status": item.status, "trigger_price": item.trigger_price}
        for item in db.scalars(select(WatchTask).where(WatchTask.status == "WATCHING").order_by(WatchTask.updated_at.desc()).limit(8)).all()
    ]
    latest_ai_decisions = [
        {"id": item.id, "symbol": item.symbol, "action": item.action, "confidence": item.confidence, "created_at": item.created_at.isoformat()}
        for item in db.scalars(select(AiDecision).order_by(AiDecision.created_at.desc()).limit(8)).all()
    ]
    latest_strategy_decisions = [
        {"id": item.id, "symbol": item.symbol, "action": item.action, "confidence": item.confidence, "created_at": item.created_at.isoformat()}
        for item in db.scalars(select(BotDecision).order_by(BotDecision.created_at.desc()).limit(8)).all()
    ]
    dry_run_pnl = 0.0
    real_pnl = 0.0
    for item in db.scalars(select(Trade)).all():
        if item.pnl:
            if item.mode.startswith("DRY_RUN"):
                dry_run_pnl += float(item.pnl)
            else:
                real_pnl += float(item.pnl)
    active_runs = db.scalars(select(BotRun).where(BotRun.status == "RUNNING")).all()
    errored_runs = db.scalars(select(BotRun).where(BotRun.status == "ERROR")).all()
    bot_health = {"running": len(active_runs), "error": len(errored_runs)}
    active_script_runs = [
        {"id": item.id, "script_file_id": item.script_file_id, "status": item.status, "started_at": item.started_at.isoformat(), "pid": item.pid}
        for item in db.scalars(select(ScriptRun).where(ScriptRun.status == "RUNNING").order_by(ScriptRun.started_at.desc()).limit(8)).all()
    ]
    latest_notifications = [
        {"id": item.id, "type": item.type, "severity": item.severity, "title": item.title, "message": item.message, "is_read": item.is_read, "created_at": item.created_at.isoformat()}
        for item in db.scalars(select(Notification).order_by(Notification.created_at.desc()).limit(8)).all()
    ]
    pnl_chart = report_service.chart_pnl_series(db)[-20:]

    if active_account:
        has_tabdeal_credentials = bool(
            active_account.tabdeal_api_key_encrypted and active_account.tabdeal_api_secret_encrypted
        )
        has_openai_key = bool(active_account.openai_api_key_encrypted)
        api_status = "configured" if has_tabdeal_credentials else "missing_credentials"
        openai_status = "configured" if has_openai_key else "missing_credentials"
        active_summary = ActiveApiAccountSummary(
            id=active_account.id,
            name=active_account.name,
            read_only=active_account.read_only,
            real_trading_allowed=active_account.real_trading_allowed,
            has_tabdeal_credentials=has_tabdeal_credentials,
            has_openai_api_key=has_openai_key,
        )
        if has_tabdeal_credentials:
            try:
                credentials = get_active_credentials(db)
                client = TabdealClient(credentials.api_key, credentials.api_secret)
                account_payload = await client.get_account()
                balances = [
                    item for item in account_payload.get("balances", []) if float(item.get("free", 0) or 0) > 0 or float(item.get("freeze", 0) or 0) > 0
                ][:8]
                open_orders_payload = await client.get_open_orders()
                if isinstance(open_orders_payload, list):
                    open_orders = open_orders_payload[:8]
                elif isinstance(open_orders_payload, dict):
                    open_orders = (open_orders_payload.get("rows") or open_orders_payload.get("orders") or [])[:8]
            except Exception:
                api_status = "api_error"

    return DashboardResponse(
        api_status=api_status,
        openai_status=openai_status,
        active_api_account=active_summary,
        latest_system_logs=[DashboardLogItem.model_validate(log) for log in latest_logs],
        balances=balances,
        open_orders=open_orders,
        open_positions=open_positions,
        latest_trades=latest_trades,
        active_bots=active_bots,
        active_watches=active_watches,
        latest_ai_decisions=latest_ai_decisions,
        latest_strategy_decisions=latest_strategy_decisions,
        active_script_runs=active_script_runs,
        latest_notifications=latest_notifications,
        pnl_chart=pnl_chart,
        today_dry_run_pnl=f"{dry_run_pnl:.8f}".rstrip("0").rstrip("."),
        today_real_pnl=f"{real_pnl:.8f}".rstrip("0").rstrip("."),
        bot_health=bot_health,
        unread_notifications_count=unread_count,
        real_trading_enabled=settings.real_trading_enabled,
        dry_run_default=settings.dry_run_default,
        phase="phase_5_production",
    )
