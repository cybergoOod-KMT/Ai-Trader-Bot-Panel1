from __future__ import annotations

import asyncio
import subprocess
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import ScriptFile, ScriptLog, ScriptRun
from app.services.notification_service import create_notification
from app.services.system_log_service import create_system_log
from app.services.ws_manager import ws_manager


class ScriptRunnerService:
    def __init__(self) -> None:
        self.root_dir = Path(__file__).resolve().parents[2] / "scripts" / "trading"
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self._processes: dict[int, subprocess.Popen[str]] = {}
        self._lock = threading.Lock()

    def scan_scripts(self) -> list[ScriptFile]:
        self.root_dir.mkdir(parents=True, exist_ok=True)
        discovered: dict[str, Path] = {}
        for path in self.root_dir.rglob("*.py"):
            if path.is_file():
                relative = path.resolve().relative_to(self.root_dir.resolve()).as_posix()
                discovered[relative] = path

        with SessionLocal() as db:
            existing = {item.relative_path: item for item in db.scalars(select(ScriptFile)).all()}
            for relative, path in discovered.items():
                item = existing.get(relative)
                if item:
                    item.name = path.name
                    item.detected_at = datetime.now(tz=UTC)
                    db.add(item)
                else:
                    db.add(ScriptFile(name=path.name, relative_path=relative, enabled=True))
            db.commit()
            return db.scalars(select(ScriptFile).order_by(ScriptFile.relative_path.asc())).all()

    def list_scripts(self) -> list[ScriptFile]:
        with SessionLocal() as db:
            return db.scalars(select(ScriptFile).order_by(ScriptFile.relative_path.asc())).all()

    def update_script(self, script_id: int, enabled: bool) -> ScriptFile:
        with SessionLocal() as db:
            script = db.get(ScriptFile, script_id)
            if not script:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script file not found.")
            script.enabled = enabled
            db.add(script)
            db.commit()
            db.refresh(script)
            create_system_log(db, "INFO", "scripts", "Script enabled state updated.", {"script_id": script.id, "enabled": enabled})
            return script

    def orphan_existing_runs(self) -> None:
        with SessionLocal() as db:
            runs = db.scalars(select(ScriptRun).where(ScriptRun.status == "RUNNING")).all()
            for run in runs:
                run.status = "ORPHANED"
                run.stopped_at = datetime.now(tz=UTC)
                run.error_message = "Backend restarted before the process state could be recovered."
                db.add(run)
                db.add(ScriptLog(script_run_id=run.id, stream="SYSTEM", line="Run marked as ORPHANED after backend restart."))
            db.commit()

    def list_runs(self) -> list[ScriptRun]:
        with SessionLocal() as db:
            return db.scalars(select(ScriptRun).order_by(ScriptRun.started_at.desc())).all()

    def list_logs(self, run_id: int) -> list[ScriptLog]:
        with SessionLocal() as db:
            return db.scalars(select(ScriptLog).where(ScriptLog.script_run_id == run_id).order_by(ScriptLog.created_at.asc(), ScriptLog.id.asc())).all()

    def get_run(self, run_id: int) -> ScriptRun:
        with SessionLocal() as db:
            item = db.get(ScriptRun, run_id)
            if not item:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script run not found.")
            return item

    def start_script(self, script_id: int) -> ScriptRun:
        with SessionLocal() as db:
            script = db.get(ScriptFile, script_id)
            if not script:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script file not found.")
            if not script.enabled:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This script is disabled.")
            script_path = self._resolve_script_path(script.relative_path)
            run = ScriptRun(script_file_id=script.id, status="RUNNING")
            db.add(run)
            db.commit()
            db.refresh(run)
            db.add(ScriptLog(script_run_id=run.id, stream="SYSTEM", line=f"Starting script {script.relative_path}"))
            db.commit()

            process = subprocess.Popen(
                ["python", str(script_path)],
                cwd=str(script_path.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                shell=False,
            )
            run.pid = process.pid
            db.add(run)
            db.commit()
            db.refresh(run)
            create_system_log(db, "INFO", "scripts", "Script started.", {"script_id": script.id, "run_id": run.id, "pid": process.pid})
            create_notification(db, "SCRIPT", "اسکریپت اجرا شد", f"{script.name} اجرا شد.", {"script_id": script.id, "run_id": run.id}, severity="SUCCESS")
            run_id = run.id

        with self._lock:
            self._processes[run_id] = process
        self._start_stream_reader(run_id, "STDOUT", process.stdout)
        self._start_stream_reader(run_id, "STDERR", process.stderr)
        self._start_waiter(run_id, process)
        return self.get_run(run_id)

    def stop_run(self, run_id: int) -> ScriptRun:
        process = self._get_live_process(run_id)
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        return self.get_run(run_id)

    def restart_run(self, run_id: int) -> ScriptRun:
        with SessionLocal() as db:
            run = db.get(ScriptRun, run_id)
            if not run:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script run not found.")
            script = db.get(ScriptFile, run.script_file_id)
            if not script:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script file not found.")
        live = self._processes.get(run_id)
        if live and live.poll() is None:
            self.stop_run(run_id)
        return self.start_script(script.id)

    def send_stdin(self, run_id: int, value: str) -> ScriptRun:
        process = self._get_live_process(run_id)
        if not process.stdin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This process does not accept stdin.")
        process.stdin.write(value + "\n")
        process.stdin.flush()
        self._store_log(run_id, "SYSTEM", f"STDIN> {value[:200]}")
        return self.get_run(run_id)

    def _resolve_script_path(self, relative_path: str) -> Path:
        candidate = (self.root_dir / relative_path).resolve()
        root = self.root_dir.resolve()
        if root not in candidate.parents and candidate != root:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Script path is outside scripts/trading.")
        if candidate.suffix.lower() != ".py" or not candidate.is_file():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only Python files inside scripts/trading can run.")
        return candidate

    def _get_live_process(self, run_id: int) -> subprocess.Popen[str]:
        with self._lock:
            process = self._processes.get(run_id)
        if not process or process.poll() is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This script run is not active.")
        return process

    def _start_stream_reader(self, run_id: int, stream_name: str, handle) -> None:
        if handle is None:
            return

        def reader() -> None:
            for line in iter(handle.readline, ""):
                cleaned = line.rstrip("\r\n")
                if cleaned:
                    self._store_log(run_id, stream_name, cleaned)
            handle.close()

        thread = threading.Thread(target=reader, daemon=True, name=f"script-{run_id}-{stream_name.lower()}-{uuid.uuid4().hex[:6]}")
        thread.start()

    def _start_waiter(self, run_id: int, process: subprocess.Popen[str]) -> None:
        def waiter() -> None:
            exit_code = process.wait()
            with self._lock:
                self._processes.pop(run_id, None)
            with SessionLocal() as db:
                run = db.get(ScriptRun, run_id)
                if not run:
                    return
                run.stopped_at = datetime.now(tz=UTC)
                run.exit_code = exit_code
                if run.status == "ORPHANED":
                    final_status = "ORPHANED"
                elif exit_code == 0:
                    final_status = "STOPPED"
                else:
                    final_status = "ERROR"
                    run.error_message = f"Process exited with code {exit_code}."
                run.status = final_status
                db.add(run)
                db.add(ScriptLog(script_run_id=run.id, stream="SYSTEM", line=f"Process exited with code {exit_code}"))
                db.commit()
                db.refresh(run)
                severity = "ERROR" if final_status == "ERROR" else "INFO"
                create_system_log(db, severity, "scripts", "Script process stopped.", {"run_id": run.id, "exit_code": exit_code, "status": final_status})
                if final_status == "ERROR":
                    create_notification(db, "SCRIPT", "اجرای اسکریپت با خطا متوقف شد", run.error_message or "Unknown script runner error.", {"run_id": run.id}, severity="ERROR")
            asyncio.run(ws_manager.publish("scripts", "script_run_finished", {"run_id": run_id, "exit_code": exit_code, "status": final_status}, topic=str(run_id)))

        thread = threading.Thread(target=waiter, daemon=True, name=f"script-{run_id}-waiter")
        thread.start()

    def _store_log(self, run_id: int, stream_name: str, line: str) -> None:
        with SessionLocal() as db:
            item = ScriptLog(script_run_id=run_id, stream=stream_name, line=line[:4000])
            db.add(item)
            db.commit()
            db.refresh(item)
        asyncio.run(
            ws_manager.publish(
                "scripts",
                "script_log",
                {"id": item.id, "script_run_id": run_id, "stream": stream_name, "line": item.line, "created_at": item.created_at.isoformat()},
                topic=str(run_id),
            )
        )


script_runner_service = ScriptRunnerService()
