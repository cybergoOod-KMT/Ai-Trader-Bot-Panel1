from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.database import Base
from app.db.models import ApiAccount
from app.services.risk_manager import RiskManager
from app.services.technical_guard import TechnicalGuardService


def _build_snapshot(**overrides):
    base = {
        "analysis_close": "100",
        "source_price_diff_pct": "0.5",
        "rsi14": "60",
        "ema9": "99",
        "ema21": "98",
        "ema50": "95",
        "macd": "2",
        "macd_signal": "1",
        "macd_histogram": "1",
        "volume_ratio": "2",
        "orderbook_pressure_bid_over_ask": "1.5",
        "support_20": "99.5",
        "resistance_20": "105",
        "atr14": "1",
    }
    base.update(overrides)
    return base


def test_technical_guard_allows_valid_buy() -> None:
    result = TechnicalGuardService().evaluate(_build_snapshot(), "BUY")
    assert result["allowed"] is True


def test_technical_guard_blocks_invalid_buy() -> None:
    result = TechnicalGuardService().evaluate(_build_snapshot(rsi14="80", volume_ratio="1"), "BUY")
    assert result["allowed"] is False
    assert result["reasons"]


def test_risk_manager_blocks_read_only_real_order() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        account = ApiAccount(
            name="demo",
            openai_model="gpt-5",
            is_active=True,
            read_only=True,
            real_trading_allowed=False,
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        result = RiskManager().evaluate_order(
            db=db,
            api_account=account,
            symbol="BTCUSDT",
            side="BUY",
            rules={"quote_asset": "USDT", "base_asset": "BTC", "min_qty": "0.1", "min_notional": "10"},
            quantity="0.2",
            estimated_value="20",
            account_payload={"balances": [{"asset": "USDT", "free": "1000"}]},
            prefer_real_execution=True,
        )
        assert result["allowed"] is False
        assert any("read-only" in reason or "واقعی" in reason for reason in result["reasons"])
