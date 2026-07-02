# README-WINDOWS

## شروع سریع

```powershell
.\start-windows.bat
```

این اسکریپت:

- `.env` را از `.env.example` می‌سازد اگر وجود نداشته باشد
- `SECRET_KEY` و `FERNET_KEY` را در صورت خالی بودن تولید می‌کند
- پورت آزاد پنل را از `3200` به بالا پیدا می‌کند
- `docker compose up -d --build` را اجرا می‌کند

## توقف

```powershell
.\stop-windows.bat
```

## بعد از بالا آمدن

1. پنل را در آدرس چاپ‌شده باز کنید
2. با `admin` وارد شوید
3. اگر پسورد هنوز پیش‌فرض است، فوراً آن را عوض کنید
4. ابتدا `API account` را در `/settings/api` بسازید
5. Dry-run را روی `/manual-trading`, `/markets`, `/ai-signal` تست کنید
6. Emergency controls را در `/settings/emergency` بررسی کنید

## مسیر تست دستی Phase 5

1. `docker compose up -d --build`
2. `http://localhost:<API_PORT>/health`
3. `http://localhost:<API_PORT>/health/deep`
4. login در پنل
5. ساخت API account
6. تست Tabdeal/OpenAI
7. Dry-run order
8. بررسی `Orders`, `Positions`, `Learning Memory`, `Audit Logs`
9. ساخت backup
10. تست `Stop All Bots` و `Pause Trading`

## نکات مهم

- اگر `401` دیدید، دوباره login کنید
- اگر `502` دیدید، upstream connector را بررسی کنید
- اگر `docker compose config` خطا داد، `.env` را بازبینی کنید
- اگر WebSocket به‌روزرسانی نداد، session cookie را چک کنید
