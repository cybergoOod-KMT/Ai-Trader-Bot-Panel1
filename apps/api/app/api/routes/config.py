from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.crypto import decrypt_secret, encrypt_secret
from app.db.database import get_db
from app.db.models import ApiAccount, User
from app.schemas.api_accounts import ApiAccountCreate, ApiAccountResponse, ApiAccountUpdate, ConnectionTestResponse
from app.services.audit_service import create_audit_log
from app.services.notification_service import create_notification
from app.services.openai_client import OpenAIConnectionClient, OpenAIConnectionError
from app.services.system_log_service import create_system_log
from app.services.tabdeal_client import TabdealClient

router = APIRouter(prefix="/api-accounts", tags=["api-accounts"])


def mask_secret(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"


def normalize_secret_input(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def to_response(account: ApiAccount) -> ApiAccountResponse:
    tabdeal_api_key = decrypt_secret(account.tabdeal_api_key_encrypted) if account.tabdeal_api_key_encrypted else None
    tabdeal_api_secret = decrypt_secret(account.tabdeal_api_secret_encrypted) if account.tabdeal_api_secret_encrypted else None
    openai_api_key = decrypt_secret(account.openai_api_key_encrypted) if account.openai_api_key_encrypted else None
    return ApiAccountResponse(
        id=account.id,
        name=account.name,
        openai_model=account.openai_model,
        is_active=account.is_active,
        read_only=account.read_only,
        real_trading_allowed=account.real_trading_allowed,
        has_tabdeal_api_key=bool(tabdeal_api_key),
        tabdeal_api_key_masked=mask_secret(tabdeal_api_key),
        has_tabdeal_api_secret=bool(tabdeal_api_secret),
        tabdeal_api_secret_masked=mask_secret(tabdeal_api_secret),
        has_openai_api_key=bool(openai_api_key),
        openai_api_key_masked=mask_secret(openai_api_key),
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


def ensure_single_active_account(db: Session, active_id: int | None) -> None:
    if active_id is None:
        return
    db.execute(update(ApiAccount).where(ApiAccount.id != active_id).values(is_active=False))


@router.get("", response_model=list[ApiAccountResponse])
def list_api_accounts(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ApiAccountResponse]:
    accounts = db.scalars(select(ApiAccount).order_by(ApiAccount.created_at.desc())).all()
    return [to_response(account) for account in accounts]


@router.post("", response_model=ApiAccountResponse, status_code=status.HTTP_201_CREATED)
def create_api_account(
    payload: ApiAccountCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiAccountResponse:
    account = ApiAccount(
        name=payload.name.strip(),
        tabdeal_api_key_encrypted=encrypt_secret(tabdeal_api_key) if (tabdeal_api_key := normalize_secret_input(payload.tabdeal_api_key)) else None,
        tabdeal_api_secret_encrypted=encrypt_secret(tabdeal_api_secret) if (tabdeal_api_secret := normalize_secret_input(payload.tabdeal_api_secret)) else None,
        openai_api_key_encrypted=encrypt_secret(openai_api_key) if (openai_api_key := normalize_secret_input(payload.openai_api_key)) else None,
        openai_model=normalize_optional_text(payload.openai_model) or get_settings().openai_default_model,
        is_active=payload.is_active,
        read_only=payload.read_only,
        real_trading_allowed=payload.real_trading_allowed,
    )
    db.add(account)
    try:
        db.flush()
        if payload.is_active:
            ensure_single_active_account(db, account.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account name already exists.")
    db.refresh(account)
    create_system_log(db, "INFO", "api_accounts", "API account created.", {"account_id": account.id, "by": current_user.username})
    create_audit_log(db, "api_account.create", "ApiAccount", str(account.id), actor_user=current_user, after={"name": account.name, "is_active": account.is_active}, request=request)
    return to_response(account)


@router.patch("/{account_id}", response_model=ApiAccountResponse)
def update_api_account(
    account_id: int,
    payload: ApiAccountUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiAccountResponse:
    account = db.get(ApiAccount, account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API account not found.")

    before = {"name": account.name, "is_active": account.is_active, "read_only": account.read_only, "real_trading_allowed": account.real_trading_allowed}
    update_data = payload.model_dump(exclude_unset=True)
    for field in ("is_active", "read_only", "real_trading_allowed"):
        if field in update_data:
            setattr(account, field, update_data[field])

    if "name" in update_data and update_data["name"] is not None:
        account.name = update_data["name"].strip()
    if "openai_model" in update_data:
        account.openai_model = normalize_optional_text(update_data["openai_model"]) or get_settings().openai_default_model

    tabdeal_api_key = normalize_secret_input(update_data.get("tabdeal_api_key")) if "tabdeal_api_key" in update_data else None
    tabdeal_api_secret = normalize_secret_input(update_data.get("tabdeal_api_secret")) if "tabdeal_api_secret" in update_data else None
    openai_api_key = normalize_secret_input(update_data.get("openai_api_key")) if "openai_api_key" in update_data else None

    if "tabdeal_api_key" in update_data and tabdeal_api_key is not None:
        account.tabdeal_api_key_encrypted = encrypt_secret(tabdeal_api_key)
    if "tabdeal_api_secret" in update_data and tabdeal_api_secret is not None:
        account.tabdeal_api_secret_encrypted = encrypt_secret(tabdeal_api_secret)
    if "openai_api_key" in update_data and openai_api_key is not None:
        account.openai_api_key_encrypted = encrypt_secret(openai_api_key)

    try:
        db.add(account)
        db.flush()
        if account.is_active:
            ensure_single_active_account(db, account.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account name already exists.")
    db.refresh(account)
    create_system_log(db, "INFO", "api_accounts", "API account updated.", {"account_id": account.id, "by": current_user.username})
    create_audit_log(db, "api_account.update", "ApiAccount", str(account.id), actor_user=current_user, before=before, after={"name": account.name, "is_active": account.is_active, "read_only": account.read_only, "real_trading_allowed": account.real_trading_allowed}, request=request)
    return to_response(account)


@router.delete("/{account_id}")
def delete_api_account(
    account_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    account = db.get(ApiAccount, account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API account not found.")
    db.delete(account)
    db.commit()
    create_system_log(db, "INFO", "api_accounts", "API account deleted.", {"account_id": account_id, "by": current_user.username})
    create_audit_log(db, "api_account.delete", "ApiAccount", str(account_id), actor_user=current_user, before={"name": account.name}, request=request)
    return {"success": True}


def get_account_or_404(db: Session, account_id: int) -> ApiAccount:
    account = db.get(ApiAccount, account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API account not found.")
    return account


async def _run_tabdeal_test(db: Session, account: ApiAccount, operation: str) -> ConnectionTestResponse:
    if not account.tabdeal_api_key_encrypted or not account.tabdeal_api_secret_encrypted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tabdeal credentials are not configured.")
    client = TabdealClient(
        api_key=decrypt_secret(account.tabdeal_api_key_encrypted),
        api_secret=decrypt_secret(account.tabdeal_api_secret_encrypted),
    )
    try:
        if operation == "ping":
            data = await client.ping()
            message = "Tabdeal ping succeeded."
        elif operation == "account":
            data = await client.get_account()
            message = "Tabdeal account authentication succeeded."
        else:
            symbol = f"BTC{get_settings().default_quote_asset}"
            data = await client.get_open_orders(symbol)
            message = "Tabdeal trade permission test succeeded."
        create_system_log(db, "INFO", "tabdeal", message, {"account_id": account.id})
        return ConnectionTestResponse(success=True, message=message, details=data if isinstance(data, dict) else {"result": data})
    except Exception as exc:  # noqa: BLE001
        message = f"Tabdeal test failed: {operation}"
        create_system_log(db, "ERROR", "tabdeal", message, {"account_id": account.id, "error": str(exc)})
        create_notification(db, "api_test_failed", "خطا در تست Tabdeal", f"{account.name}: {operation} failed", {"account_id": account.id})
        return ConnectionTestResponse(success=False, message=f"{message}. {exc}", details=None)


@router.post("/{account_id}/test-tabdeal-ping", response_model=ConnectionTestResponse)
async def test_tabdeal_ping(
    account_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConnectionTestResponse:
    return await _run_tabdeal_test(db, get_account_or_404(db, account_id), "ping")


@router.post("/{account_id}/test-tabdeal-account", response_model=ConnectionTestResponse)
async def test_tabdeal_account(
    account_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConnectionTestResponse:
    return await _run_tabdeal_test(db, get_account_or_404(db, account_id), "account")


@router.post("/{account_id}/test-tabdeal-trade-auth", response_model=ConnectionTestResponse)
async def test_tabdeal_trade_auth(
    account_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConnectionTestResponse:
    return await _run_tabdeal_test(db, get_account_or_404(db, account_id), "trade_auth")


@router.post("/{account_id}/test-openai", response_model=ConnectionTestResponse)
async def test_openai(
    account_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConnectionTestResponse:
    account = get_account_or_404(db, account_id)
    if not account.openai_api_key_encrypted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OpenAI API key is not configured.")
    try:
        client = OpenAIConnectionClient(
            api_key=decrypt_secret(account.openai_api_key_encrypted),
            model=account.openai_model,
        )
        data = await client.test_connection()
        create_system_log(db, "INFO", "openai", "OpenAI test succeeded.", {"account_id": account.id, "model": account.openai_model})
        return ConnectionTestResponse(success=True, message="OpenAI test succeeded.", details=data)
    except OpenAIConnectionError as exc:
        create_system_log(db, "ERROR", "openai", "OpenAI test failed.", {"account_id": account.id, "error": str(exc)})
        create_notification(db, "openai_test_failed", "خطا در تست OpenAI", f"{account.name}: OpenAI test failed", {"account_id": account.id})
        return ConnectionTestResponse(success=False, message=f"OpenAI test failed. {exc}", details=None)
    except Exception:
        create_system_log(db, "ERROR", "openai", "OpenAI test failed.", {"account_id": account.id, "error": "unexpected_error"})
        create_notification(db, "openai_test_failed", "خطا در تست OpenAI", f"{account.name}: OpenAI test failed", {"account_id": account.id})
        return ConnectionTestResponse(success=False, message="OpenAI test failed. Unexpected upstream error.", details=None)
