# Deployment

## Docker

```powershell
docker compose up -d --build
```

## Validate first

```powershell
docker compose config
cd apps/api
python -m pytest
cd ../web
npm run build
```

## Production notes

- terminate TLS before public exposure
- keep SQLite backups frequent
- review `/health/deep`
- confirm emergency controls before enabling REAL
