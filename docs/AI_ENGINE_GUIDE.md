# AI Engine Guide

## Location

`apps/api/app/plugins/ai_engines/`

## Contract

- `name`
- `description`
- `config_schema`
- `healthcheck(config)`
- `analyze(payload, config)`

## Built-ins

- `OPENAI`
- `OLLAMA`

`OLLAMA` is a real adapter and fails clearly when the configured local endpoint is unavailable.
