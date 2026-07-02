<div align="center">

# Tabdeal AI Trading Panel

### Real Personal Trading Panel for Tabdeal with AI Signals, Manual Trading, Bots, Backtests and Reports

Production-oriented trading platform built with FastAPI, Next.js, SQLite and Docker for personal crypto trading workflows.

<p>

<a href="https://github.com/cybergoOod-KMT/tabdeal-ai-trading-panel">
<img src="https://img.shields.io/badge/GitHub-Repository-black?style=for-the-badge&logo=github">
</a>

<a href="https://github.com/cybergoOod-KMT/tabdeal-ai-trading-panel/actions">
<img src="https://img.shields.io/badge/CI-GitHub%20Actions-blue?style=for-the-badge&logo=githubactions">
</a>

<a href="mailto:kmt.suport@gmail.com">
<img src="https://img.shields.io/badge/Email-Contact-red?style=for-the-badge">
</a>

</p>

</div>

---

# Overview

`tabdeal-ai-trading-panel` is a full-stack personal trading control panel designed around real workflows instead of mock dashboards.

The platform includes:

- secure API account management
- Tabdeal integration
- OpenAI-powered AI Signal analysis
- manual trading preview and guarded execution
- strategy bots and AI bots
- market snapshot and indicators
- backtests and CSV import
- script runner with live logs
- reports and exports
- audit logs, learning memory and emergency controls

---

# Features

- Admin authentication and protected panel
- Encrypted storage for API credentials
- Tabdeal market and account connectivity
- OpenAI Responses API integration
- Manual trading with risk checks and technical guard
- Dry-run and real execution paths
- Orders, positions and trade history
- AI Signal page
- Strategy bots and AI bots
- Watch tasks and position monitor
- TradingView integration
- Script runner
- Backtest engine
- Reports and CSV export
- Notifications, system logs and audit trail
- Persian RTL responsive dark UI
- Docker-first deployment

---

# Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.11, FastAPI, SQLAlchemy, Alembic |
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Database | SQLite |
| AI | OpenAI Responses API, Ollama adapter interface |
| Exchange | Tabdeal, Binance public market data |
| Runtime | Docker, Docker Compose |
| API | REST and WebSocket |
| Charts | TradingView widget integration |

---

# Project Structure

```text
tabdeal-ai-trading-panel/
  apps/
    api/
      app/
      tests/
    web/
      app/
      components/
      lib/
  docs/
  scripts/
    trading/
  .github/
  docker-compose.yml
  .env.example
  README.md
  README-WINDOWS.md
  start-windows.ps1
  start-windows.bat
  stop-windows.bat
```

---

# Getting Started

```bash
git clone https://github.com/YOUR_USERNAME/tabdeal-ai-trading-panel.git
cd tabdeal-ai-trading-panel
cp .env.example .env
docker compose up -d --build
```

For Windows:

```powershell
.\start-windows.bat
```

---

# Default Access

- Username: `admin`
- Password: value of `ADMIN_PASSWORD` in `.env`

If the password is still set to `change_this_password`, the panel will force a password change on first login.

---

# Security Notes

Do not commit:

- `.env`
- SQLite runtime database
- logs
- backups
- live API credentials
- private strategy data

API keys may be encrypted at rest inside the app, but the runtime database is still sensitive and should not be published with real data.

---

# DRY_RUN vs REAL

## DRY_RUN

- no real order is sent to Tabdeal
- orders, trades and positions are still recorded in the database
- suitable for end-to-end testing

## REAL

Real execution is allowed only when all safety conditions pass, including:

- global real trading enabled
- active account permissions allow real trading
- account is not read-only
- risk manager approval
- technical guard approval for BUY flows
- backend confirmation token

---
<h2>Screenshot</h2>

<p align="center">
  <img src="https://raw.githubusercontent.com/cybergoOod-KMT/Ai-Trader-Bot-Panel1/main/Screenshot%202026-07-02%20151036.png"
       width="900"
       alt="AI Trader Bot Panel">
</p>

# Main Pages

- `/dashboard`
- `/settings/api`
- `/markets`
- `/manual-trading`
- `/ai-signal`
- `/orders`
- `/positions`
- `/logs`
- `/notifications`
- `/reports`
- `/script-trading`
- `/backtests`
- `/audit-logs`
- `/learning-memory`
- `/settings/risk`
- `/settings/ai-engines`
- `/settings/strategies`
- `/settings/emergency`

---

# License

Choose and add the license you want before publishing, for example:

- MIT
- Apache-2.0
- Proprietary / Private Use

---

# Contact

- GitHub: https://github.com/cybergoOod-KMT
- Email: kmt.suport@gmail.com

---

<div align="center">

Built for practical crypto trading operations, AI-assisted workflows and extensible system design.

</div>
