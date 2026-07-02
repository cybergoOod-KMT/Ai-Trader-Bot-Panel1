# Risk Manager

## Inputs

- active account
- market rules
- balances
- open positions
- recent trades and losses
- emergency settings

## Main controls

- per order budget
- total budget
- min reserve
- max open positions
- max daily loss pct
- max daily loss usdt
- max consecutive losses
- symbol cooldown
- cooldown after loss
- cooldown after API error
- real trading lock
- emergency stop
- global kill switch

## Output

- `allowed`
- `reasons`
- `calculated_quantity`
- `estimated_value`
- `mode`
