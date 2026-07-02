# Troubleshooting

## 401

- session cookie missing
- login expired
- middleware redirected to `/login`

## 502

- Tabdeal timeout
- Binance unavailable
- OpenAI or Ollama connector unavailable

## invalid symbol

- symbol format mismatched
- market unavailable on upstream connector

## script runner

- file must live under `scripts/trading/`
- only `.py` is allowed

## REAL blocked

- global real trading disabled
- account is read-only
- account real trading flag disabled
- confirm token missing or expired
- emergency lock enabled
