# Architecture

## Core layers

- `apps/api/app/api/routes`: HTTP and WebSocket surfaces
- `apps/api/app/services`: orchestration and domain logic
- `apps/api/app/plugins`: replaceable AI, strategy, and exchange modules
- `apps/api/app/db`: SQLAlchemy models and Alembic migrations
- `apps/web`: operator-facing panel

## Execution flow

1. UI requests preview or action
2. backend authenticates admin session
3. request passes through Risk Manager
4. BUY flows can pass through Technical Guard
5. REAL flows require confirm token
6. execution passes through OrderManager only
7. logs, notifications, audit, outcomes update

## Plugin families

- `plugins/ai_engines`
- `plugins/strategies`
- `plugins/exchanges`

Each family exposes a registry so existing routes can stay backward compatible while engines/connectors remain swappable.
