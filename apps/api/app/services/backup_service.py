from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ApiAccount, SystemSetting


class BackupService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.settings.backups_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, db: Session) -> dict:
        timestamp = datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S")
        backup_id = f"backup-{timestamp}"
        target_dir = self.settings.backups_dir / backup_id
        target_dir.mkdir(parents=True, exist_ok=True)

        sqlite_path = self._sqlite_path()
        if sqlite_path and sqlite_path.exists():
            shutil.copy2(sqlite_path, target_dir / sqlite_path.name)

        config_payload = {
            "api_accounts": [self._sanitize_account(item) for item in db.scalars(select(ApiAccount).order_by(ApiAccount.id.asc())).all()],
            "system_settings": [{"key": row.key, "value_json": row.value_json} for row in db.scalars(select(SystemSetting)).all()],
            "created_at": datetime.now(tz=UTC).isoformat(),
        }
        (target_dir / "config.json").write_text(json.dumps(config_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"id": backup_id, "files": [item.name for item in target_dir.iterdir()], "created_at": config_payload["created_at"]}

    def list_backups(self) -> list[dict]:
        rows = []
        for item in sorted(self.settings.backups_dir.glob("backup-*"), reverse=True):
            rows.append(
                {
                    "id": item.name,
                    "created_at": datetime.fromtimestamp(item.stat().st_mtime, tz=UTC).isoformat(),
                    "files": [child.name for child in item.iterdir()],
                }
            )
        return rows

    def resolve_backup(self, backup_id: str) -> Path:
        path = (self.settings.backups_dir / backup_id).resolve()
        if self.settings.backups_dir.resolve() not in path.parents or not path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found.")
        return path

    def restore_backup(self, backup_id: str) -> dict:
        backup_dir = self.resolve_backup(backup_id)
        sqlite_path = self._sqlite_path()
        if sqlite_path is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Restore supports SQLite only in Phase 5.")
        sqlite_candidates = list(backup_dir.glob("*.db"))
        if not sqlite_candidates:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Backup has no SQLite snapshot.")
        shutil.copy2(sqlite_candidates[0], sqlite_path)
        return {"restored": True, "backup_id": backup_id}

    def download_target(self, backup_id: str) -> Path:
        return self.resolve_backup(backup_id)

    def _sqlite_path(self) -> Path | None:
        database_url = self.settings.database_url
        if database_url.startswith("sqlite:///./"):
            return Path(database_url.replace("sqlite:///./", "./")).resolve()
        if database_url.startswith("sqlite:///"):
            return Path(database_url.replace("sqlite:///", "")).resolve()
        return None

    @staticmethod
    def _sanitize_account(account: ApiAccount) -> dict:
        return {
            "id": account.id,
            "name": account.name,
            "openai_model": account.openai_model,
            "is_active": account.is_active,
            "read_only": account.read_only,
            "real_trading_allowed": account.real_trading_allowed,
            "has_tabdeal_api_key": bool(account.tabdeal_api_key_encrypted),
            "has_tabdeal_api_secret": bool(account.tabdeal_api_secret_encrypted),
            "has_openai_api_key": bool(account.openai_api_key_encrypted),
        }


backup_service = BackupService()
