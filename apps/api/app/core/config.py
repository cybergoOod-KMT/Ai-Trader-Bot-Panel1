from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    app_env: str = Field(alias="APP_ENV")
    panel_port: int = Field(alias="PANEL_PORT")
    api_port: int = Field(alias="API_PORT")
    database_url: str = Field(alias="DATABASE_URL")
    secret_key: str = Field(alias="SECRET_KEY")
    fernet_key: str = Field(alias="FERNET_KEY")
    admin_username: str = Field(alias="ADMIN_USERNAME")
    admin_password: str = Field(alias="ADMIN_PASSWORD")
    real_trading_enabled: bool = Field(alias="REAL_TRADING_ENABLED")
    dry_run_default: bool = Field(alias="DRY_RUN_DEFAULT", default=True)
    default_quote_asset: str = Field(alias="DEFAULT_QUOTE_ASSET")
    openai_default_model: str = Field(alias="OPENAI_DEFAULT_MODEL")
    openai_url: str = Field(alias="OPENAI_URL", default="https://api.openai.com/v1/responses")
    tabdeal_base_url: str = Field(alias="TABDEAL_BASE_URL")
    binance_klines_url: str = Field(alias="BINANCE_KLINES_URL")
    next_public_api_base_url: str = Field(alias="NEXT_PUBLIC_API_BASE_URL", default="http://localhost:8000")
    risk_max_total_budget_usdt: float = Field(alias="RISK_MAX_TOTAL_BUDGET_USDT", default=1000)
    risk_per_order_usdt: float = Field(alias="RISK_PER_ORDER_USDT", default=100)
    risk_min_usdt_reserve: float = Field(alias="RISK_MIN_USDT_RESERVE", default=50)
    risk_max_open_positions: int = Field(alias="RISK_MAX_OPEN_POSITIONS", default=5)
    risk_max_daily_loss_pct: float = Field(alias="RISK_MAX_DAILY_LOSS_PCT", default=5)
    risk_symbol_cooldown_seconds: int = Field(alias="RISK_SYMBOL_COOLDOWN_SECONDS", default=300)
    real_confirm_token_ttl_seconds: int = Field(alias="REAL_CONFIRM_TOKEN_TTL_SECONDS", default=120)
    bot_scan_interval_seconds: int = Field(alias="BOT_SCAN_INTERVAL_SECONDS", default=30)
    watch_poll_interval_seconds: int = Field(alias="WATCH_POLL_INTERVAL_SECONDS", default=15)
    position_monitor_interval_seconds: int = Field(alias="POSITION_MONITOR_INTERVAL_SECONDS", default=15)
    bot_api_error_threshold: int = Field(alias="BOT_API_ERROR_THRESHOLD", default=3)
    ollama_base_url: str = Field(alias="OLLAMA_BASE_URL", default="http://host.docker.internal:11434")
    ollama_model: str = Field(alias="OLLAMA_MODEL", default="llama3.1")
    export_max_rows: int = Field(alias="EXPORT_MAX_ROWS", default=5000)
    csv_import_max_bytes: int = Field(alias="CSV_IMPORT_MAX_BYTES", default=2_000_000)
    backups_dir_name: str = Field(alias="BACKUPS_DIR_NAME", default="backups")
    metrics_window_minutes: int = Field(alias="METRICS_WINDOW_MINUTES", default=60)
    real_trading_lock_default: bool = Field(alias="REAL_TRADING_LOCK_DEFAULT", default=False)

    session_cookie_name: str = "tabdeal_panel_session"
    session_max_age_seconds: int = 60 * 60 * 12

    @property
    def is_local(self) -> bool:
        return self.app_env.lower() == "local"

    @property
    def logs_dir(self) -> Path:
        return Path("./logs")

    @property
    def data_dir(self) -> Path:
        return Path("./data")

    @property
    def backups_dir(self) -> Path:
        return self.data_dir / self.backups_dir_name

    @property
    def openai_api_base_url(self) -> str:
        normalized = self.openai_url.rstrip("/")
        if normalized.endswith("/responses"):
            return f"{normalized.rsplit('/', 1)[0]}/"
        return f"{normalized}/"

    @property
    def session_cookie_secure(self) -> bool:
        return not self.is_local

    @property
    def session_cookie_samesite(self) -> str:
        return "lax" if self.is_local else "strict"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    missing = []
    if not settings.secret_key.strip():
        missing.append("SECRET_KEY")
    if not settings.fernet_key.strip():
        missing.append("FERNET_KEY")
    if missing:
        raise RuntimeError(
            "Missing required secrets: "
            + ", ".join(missing)
            + ". Run start-windows.ps1 for local bootstrap or define them manually."
        )
    return settings
