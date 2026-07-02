from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.crypto import decrypt_secret
from app.db.models import ApiAccount


@dataclass
class ActiveCredentials:
    account: ApiAccount
    api_key: str
    api_secret: str


def get_active_api_account(db: Session) -> ApiAccount:
    account = db.scalar(select(ApiAccount).where(ApiAccount.is_active.is_(True)))
    if not account:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active API account is configured.")
    return account


def get_active_credentials(db: Session) -> ActiveCredentials:
    account = get_active_api_account(db)
    if not account.tabdeal_api_key_encrypted or not account.tabdeal_api_secret_encrypted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active API account has no Tabdeal credentials.")
    return ActiveCredentials(
        account=account,
        api_key=decrypt_secret(account.tabdeal_api_key_encrypted),
        api_secret=decrypt_secret(account.tabdeal_api_secret_encrypted),
    )
