import logging
from logging.handlers import RotatingFileHandler

from app.core.config import get_settings
from app.core.request_context import get_error_id, get_request_id


def configure_logging() -> None:
    settings = get_settings()
    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    class ContextFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            record.request_id = get_request_id()
            record.error_id = get_error_id()
            return True

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] request_id=%(request_id)s error_id=%(error_id)s %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if not any(isinstance(handler, RotatingFileHandler) for handler in root_logger.handlers):
        file_handler = RotatingFileHandler(
            settings.logs_dir / "app.log",
            maxBytes=1_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(ContextFilter())
        root_logger.addHandler(file_handler)

    if not any(isinstance(handler, logging.StreamHandler) for handler in root_logger.handlers):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.addFilter(ContextFilter())
        root_logger.addHandler(stream_handler)
