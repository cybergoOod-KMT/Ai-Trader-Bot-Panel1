from app.core.crypto import decrypt_secret, encrypt_secret
from app.core.security import create_session_token, decode_session_token, get_password_hash, verify_password


def test_password_hash_roundtrip() -> None:
    password = "StrongPass123!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True


def test_session_token_roundtrip() -> None:
    token = create_session_token(42)
    assert decode_session_token(token) == 42


def test_encrypt_decrypt_secret_roundtrip() -> None:
    raw = "sk-test-123"
    encrypted = encrypt_secret(raw)
    assert encrypted != raw
    assert decrypt_secret(encrypted) == raw
