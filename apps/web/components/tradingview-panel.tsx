"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type PriceLine = {
  label: string;
  value: string | number | null | undefined;
  tone?: "support" | "resistance" | "entry" | "tp" | "sl" | "info";
};

function normalizeTradingViewSymbol(symbol: string) {
  const cleaned = symbol.toUpperCase().replace("/", "").replace("_", "").replace("-", "");
  if (cleaned.endsWith("USDT")) {
    return `BINANCE:${cleaned}`;
  }
  return null;
}

export function TradingViewPanel({
  symbol,
  exchange = "BINANCE",
  title = "TradingView",
  priceLines = [],
  aiDecision,
  guardSummary,
}: {
  symbol: string;
  exchange?: "BINANCE" | "TABDEAL";
  title?: string;
  priceLines?: PriceLine[];
  aiDecision?: string | null;
  guardSummary?: string | null;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [mounted, setMounted] = useState(false);
  const tradingViewSymbol = useMemo(() => normalizeTradingViewSymbol(symbol), [symbol]);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || !containerRef.current || exchange !== "BINANCE" || !tradingViewSymbol) {
      return;
    }
    containerRef.current.innerHTML = "";
    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
    script.async = true;
    script.type = "text/javascript";
    script.innerHTML = JSON.stringify({
      autosize: true,
      symbol: tradingViewSymbol,
      interval: "1",
      timezone: "Etc/UTC",
      theme: "dark",
      style: "1",
      locale: "en",
      hide_top_toolbar: false,
      allow_symbol_change: false,
      support_host: "https://www.tradingview.com",
    });
    containerRef.current.appendChild(script);
  }, [mounted, exchange, tradingViewSymbol]);

  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_300px]">
      <div className="rounded-[28px] border border-white/8 bg-[#081220]/70 p-4">
        <div className="mb-3 flex items-center justify-between">
          <div className="text-sm font-semibold text-white">{title}</div>
          <div className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-xs text-cyan-200">
            {exchange === "BINANCE" && tradingViewSymbol ? tradingViewSymbol : "TABDEAL TEXT MODE"}
          </div>
        </div>
        {exchange === "BINANCE" && tradingViewSymbol ? (
          <div ref={containerRef} className="h-[420px] w-full overflow-hidden rounded-2xl bg-[#0a1627]" />
        ) : (
          <div className="flex h-[420px] items-center justify-center rounded-2xl border border-dashed border-white/10 bg-[#0a1627] p-6 text-sm leading-7 text-slate-300">
            TradingView برای این نماد یا این Exchange mapping در دسترس نیست. داده‌های واقعی Tabdeal و سطوح قیمتی در پنل کناری نمایش داده می‌شوند.
          </div>
        )}
      </div>

      <div className="rounded-[28px] border border-white/8 bg-[#081220]/70 p-4">
        <div className="text-sm font-semibold text-white">سطوح عملیاتی</div>
        <div className="mt-4 space-y-3">
          {priceLines.map((line) => (
            <div key={line.label} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
              <div className="text-xs text-slate-400">{line.label}</div>
              <div
                className={`mt-2 text-sm font-medium ${
                  line.tone === "support"
                    ? "text-emerald-300"
                    : line.tone === "resistance"
                      ? "text-rose-300"
                      : line.tone === "entry"
                        ? "text-cyan-300"
                        : line.tone === "tp"
                          ? "text-yellow-300"
                          : line.tone === "sl"
                            ? "text-rose-200"
                            : "text-white"
                }`}
              >
                {line.value ?? "-"}
              </div>
            </div>
          ))}
          {aiDecision ? (
            <div className="rounded-2xl border border-violet-400/15 bg-violet-400/10 px-4 py-3 text-sm text-violet-100">
              <div className="text-xs text-violet-200/80">AI Decision</div>
              <div className="mt-2">{aiDecision}</div>
            </div>
          ) : null}
          {guardSummary ? (
            <div className="rounded-2xl border border-yellow-400/15 bg-yellow-400/10 px-4 py-3 text-sm text-yellow-50">
              <div className="text-xs text-yellow-200/80">Technical Guard</div>
              <div className="mt-2">{guardSummary}</div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
