from datetime import datetime, timezone

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _get_serializer() -> URLSafeTimedSerializer:
    settings = get_settings()
    return URLSafeTimedSerializer(settings.secret_key, salt="tabdeal-admin-session")


def create_session_token(user_id: int) -> str:
    serializer = _get_serializer()
    return serializer.dumps(
        {
            "sub": user_id,
            "iat": int(datetime.now(tz=timezone.utc).timestamp()),
        }
    )


def decode_session_token(token: str) -> int | None:
    serializer = _get_serializer()
    settings = get_settings()
    try:
        payload = serializer.loads(token, max_age=settings.session_max_age_seconds)
        return int(payload["sub"])
    except (BadSignature, SignatureExpired, KeyError, TypeError, ValueError):
        return None
