# Security

## Secrets

- API secrets are encrypted at rest with Fernet
- secrets never return to frontend after save
- secrets are not exported in backups or CSV reports
- sanitized error handling suppresses sensitive upstream messages

## REAL trading

- global `REAL_TRADING_ENABLED` must be true
- Risk Manager must allow execution
- account must not be `read_only`
- account must allow real trading
- backend confirm token is mandatory

## Admin surface

- HttpOnly session cookie
- production-aware `secure` and `samesite`
- protected routes in frontend middleware
- audit log for sensitive actions

## Script Runner

- only `.py` files inside `scripts/trading/`
- path traversal blocked
- `shell=True` is not used
- stdin length is capped in stored logs
