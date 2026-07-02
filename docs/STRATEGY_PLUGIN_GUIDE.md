# Strategy Plugin Guide

## Location

`apps/api/app/plugins/strategies/`

## Contract

- `name`
- `description`
- `config_schema`
- `supports_backtest`
- `analyze(config, market_snapshot, account_snapshot, open_positions)`

## Return shape

Use `StrategyDecision` from `plugins/strategies/base.py`.

## Registration

Add the strategy instance to `strategy_registry`.
