from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routes import admin_settings, ai, audit_logs, auth, backtests, backup, bots, config, dashboard, data_import, emergency, learning_memory, manual_orders, markets, notifications, positions, reports, risk, scripts, strategies, system_logs, watch, websockets
from app.core.config import get_settings
from app.core.errors import RequestContextMiddleware, install_error_handlers
from app.core.logging import configure_logging
from app.core.security import get_password_hash
from app.db.database import SessionLocal
from app.db.models import Notification, User
from app.services.bot_runner import bot_runner_service
from app.services.health_service import health_service
from app.services.metrics_service import metrics_service
from app.services.notification_service import create_notification
from app.services.position_monitor import position_monitor_service
from app.services.script_runner import script_runner_service
from app.services.system_log_service import create_system_log


def run_migrations() -> None:
    alembic_cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


def ensure_seed_data() -> None:
    settings = get_settings()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == settings.admin_username))
        if not user:
            user = User(
                username=settings.admin_username,
                password_hash=get_password_hash(settings.admin_password),
                force_password_change=settings.admin_password == "change_this_password",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            create_system_log(db, "INFO", "bootstrap", "Admin user seeded.", {"username": settings.admin_username})

        if settings.admin_password == "change_this_password":
            existing_notice = db.scalar(select(Notification).where(Notification.type == "default_password_warning"))
            if not existing_notice:
                create_notification(
                    db,
                    "default_password_warning",
                    "رمز پیش‌فرض فعال است",
                    "رمز عبور پیش‌فرض هنوز تغییر نکرده است. بلافاصله آن را عوض کنید.",
                    None,
                )

        if not settings.real_trading_enabled:
            existing_notice = db.scalar(select(Notification).where(Notification.type == "real_trading_disabled"))
            if not existing_notice:
                create_notification(
                    db,
                    "real_trading_disabled",
                    "معامله واقعی غیرفعال است",
                    "REAL_TRADING_ENABLED=false است و پنل در حالت امن Phase 1 اجرا می‌شود.",
                    None,
                )


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    settings.backups_dir.mkdir(parents=True, exist_ok=True)
    configure_logging()
    run_migrations()
    ensure_seed_data()
    bot_runner_service.orphan_existing_runs()
    script_runner_service.orphan_existing_runs()
    script_runner_service.scan_scripts()
    yield
    await position_monitor_service.stop()

app = FastAPI(title="Tabdeal AI Trading Panel API", version="5.0.0-phase5", lifespan=lifespan)
install_error_handlers(app)
app.add_middleware(RequestContextMiddleware)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.panel_port}",
        "http://127.0.0.1:3200",
        "http://localhost:3200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(ai.router)
app.include_router(admin_settings.router)
app.include_router(audit_logs.router)
app.include_router(bots.router)
app.include_router(backtests.router)
app.include_router(backup.router)
app.include_router(config.router)
app.include_router(data_import.router)
app.include_router(dashboard.router)
app.include_router(emergency.router)
app.include_router(learning_memory.router)
app.include_router(manual_orders.router)
app.include_router(markets.router)
app.include_router(notifications.router)
app.include_router(positions.router)
app.include_router(reports.router)
app.include_router(risk.router)
app.include_router(scripts.router)
app.include_router(strategies.router)
app.include_router(system_logs.router)
app.include_router(watch.router)
app.include_router(websockets.router)


@app.get("/health")
def health() -> dict:
    return health_service.basic()


@app.get("/health/deep")
def deep_health() -> dict:
    with SessionLocal() as db:
        return health_service.deep(db)


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str:
    with SessionLocal() as db:
        return metrics_service.render_prometheus(db)
