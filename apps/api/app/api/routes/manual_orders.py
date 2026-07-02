from types import SimpleNamespace

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import ManualOrder, User
from app.schemas.orders import (
    ConfirmRealOrderRequest,
    ManualOrderCreateResponse,
    ManualOrderPreviewResponse,
    ManualOrderRequest,
    ManualOrderResponse,
)
from app.services.order_manager import OrderManager
from app.services.system_log_service import create_system_log

router = APIRouter(prefix="/manual-orders", tags=["manual-orders"])


def serialize_manual_order(order: ManualOrder) -> ManualOrderResponse:
    return ManualOrderResponse.model_validate(order)


@router.post("/preview", response_model=ManualOrderPreviewResponse)
async def preview_manual_order(
    payload: ManualOrderRequest,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ManualOrderPreviewResponse:
    preview = await OrderManager().preview_order(db, payload)
    return ManualOrderPreviewResponse(**{k: preview[k] for k in ("symbol", "normalized_quantity", "normalized_price", "estimated_value", "market_snapshot", "risk", "technical_guard")})


@router.post("", response_model=ManualOrderCreateResponse)
async def create_manual_order(
    payload: ManualOrderRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ManualOrderCreateResponse:
    payload_with_idempotency = SimpleNamespace(**payload.model_dump(), idempotency_key=idempotency_key)
    result = await OrderManager().create_order(db, payload_with_idempotency, request=request, actor_user=current_user)
    return ManualOrderCreateResponse(
        order=serialize_manual_order(result["order"]),
        preview=ManualOrderPreviewResponse(**{k: result["preview"][k] for k in ("symbol", "normalized_quantity", "normalized_price", "estimated_value", "market_snapshot", "risk", "technical_guard")}),
        confirm_token=result["confirm_token"],
    )


@router.post("/{order_id}/confirm-real", response_model=ManualOrderResponse)
async def confirm_real_order(
    order_id: int,
    payload: ConfirmRealOrderRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ManualOrderResponse:
    order = await OrderManager().confirm_real_order(db, order_id, payload.confirm_token, request=request, actor_user=current_user)
    return serialize_manual_order(order)


@router.delete("/{order_id}/cancel", response_model=ManualOrderResponse)
async def cancel_manual_order(
    order_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ManualOrderResponse:
    order = await OrderManager().cancel_order(db, order_id, request=request, actor_user=current_user)
    return serialize_manual_order(order)


@router.get("", response_model=list[ManualOrderResponse])
def list_manual_orders(
    symbol: str | None = Query(default=None),
    mode: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ManualOrderResponse]:
    query = select(ManualOrder).order_by(ManualOrder.created_at.desc())
    if symbol:
        query = query.where(ManualOrder.symbol == symbol.upper())
    if mode:
        query = query.where(ManualOrder.mode == mode.upper())
    rows = db.scalars(query.offset(offset).limit(limit)).all()
    return [serialize_manual_order(item) for item in rows]


@router.get("/{order_id}", response_model=ManualOrderResponse)
def get_manual_order(
    order_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ManualOrderResponse:
    order = db.get(ManualOrder, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manual order not found.")
    return serialize_manual_order(order)
