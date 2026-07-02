from decimal import Decimal


class TechnicalGuardService:
    def evaluate_buy(self, snapshot: dict) -> dict:
        price = Decimal(snapshot["analysis_close"])
        source_diff = Decimal(snapshot["source_price_diff_pct"])
        rsi = Decimal(snapshot["rsi14"])
        ema9 = Decimal(snapshot["ema9"])
        ema21 = Decimal(snapshot["ema21"])
        ema50 = Decimal(snapshot["ema50"])
        macd = Decimal(snapshot["macd"])
        macd_signal = Decimal(snapshot["macd_signal"])
        macd_hist = Decimal(snapshot["macd_histogram"])
        volume_ratio = Decimal(snapshot["volume_ratio"])
        orderbook_pressure = Decimal(snapshot["orderbook_pressure_bid_over_ask"])
        support = Decimal(snapshot["support_20"])
        resistance = Decimal(snapshot["resistance_20"])
        atr = Decimal(snapshot["atr14"])

        reasons: list[str] = []
        if source_diff > Decimal("1"):
            reasons.append("اختلاف قیمت منبع تحلیلی با Tabdeal بیشتر از 1 درصد است.")
        if not (Decimal("50") <= rsi <= Decimal("68")):
            reasons.append("RSI باید بین 50 و 68 باشد.")
        if price <= ema9:
            reasons.append("قیمت باید بالاتر از EMA9 باشد.")
        if ema9 < ema21:
            reasons.append("EMA9 باید بزرگ‌تر یا مساوی EMA21 باشد.")
        if price <= ema50:
            reasons.append("قیمت باید بالاتر از EMA50 باشد.")
        if macd <= macd_signal:
            reasons.append("MACD باید بالاتر از Signal باشد.")
        if macd_hist <= 0:
            reasons.append("هیستوگرام MACD باید مثبت باشد.")
        if volume_ratio < Decimal("1.5"):
            reasons.append("Volume ratio باید حداقل 1.5 باشد.")
        if orderbook_pressure < Decimal("1.2"):
            reasons.append("فشار اردربوک خریداران باید حداقل 1.2 باشد.")

        near_support = price > 0 and abs((price - support) / price) <= Decimal("0.01")
        breakout = price >= resistance * Decimal("1.001")
        if not near_support and not breakout:
            reasons.append("قیمت نه نزدیک حمایت است و نه شکست مقاومت تأیید شده دارد.")
        if price >= resistance * Decimal("0.995") and not breakout:
            reasons.append("قیمت خیلی نزدیک مقاومت است ولی breakout هنوز تأیید نشده است.")

        risk = max(price - support, atr if atr > 0 else Decimal("0.00000001"))
        reward_target = (resistance - price) if near_support else (price + (atr * Decimal("2")) - price)
        risk_reward = (reward_target / risk) if risk > 0 else Decimal("0")
        if risk_reward < Decimal("1.5"):
            reasons.append("حداقل نسبت ریسک به ریوارد 1.5 تامین نشده است.")

        entry_type = "near_support" if near_support else "breakout" if breakout else "blocked"
        return {
            "allowed": len(reasons) == 0,
            "reasons": reasons,
            "risk_reward": f"{risk_reward:.4f}",
            "entry_type": entry_type if len(reasons) == 0 else "blocked",
        }

    def evaluate(self, snapshot: dict, side: str) -> dict:
        if side.upper() != "BUY":
            return {"allowed": True, "reasons": [], "risk_reward": "0", "entry_type": "blocked"}
        return self.evaluate_buy(snapshot)
