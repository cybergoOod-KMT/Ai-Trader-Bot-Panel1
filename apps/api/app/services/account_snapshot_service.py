from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Position
from app.services.account_service import get_active_credentials
from app.services.tabdeal_client import TabdealClient


async def build_account_snapshot(db: Session) -> dict:
    credentials = get_active_credentials(db)
    payload = await TabdealClient(credentials.api_key, credentials.api_secret).get_account()
    open_positions = db.scalars(select(Position).where(Position.status == "OPEN")).all()
    return {
        "api_account_id": credentials.account.id,
        "balances": payload.get("balances", []),
        "can_trade_real": credentials.account.real_trading_allowed and not credentials.account.read_only,
        "open_positions": [
            {
                "id": item.id,
                "symbol": item.symbol,
                "quantity": item.quantity,
                "entry_price": item.entry_price,
                "current_price": item.current_price,
                "take_profit": item.take_profit,
                "stop_loss": item.stop_loss,
            }
            for item in open_positions
        ],
    }
