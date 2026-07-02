"use client";

import { useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { SectionCard } from "@/components/section-card";
import { StatusBadge } from "@/components/status-badge";
import { TradingViewPanel } from "@/components/tradingview-panel";
import { api } from "@/lib/api";
import type { MarketRules, MarketSearchItem, MarketSnapshot, OrderBook, TechnicalGuardResponse, TradeTick } from "@/lib/types";
import { formatDateTime, normalizeError } from "@/lib/utils";

export function MarketsView() {
  const [query, setQuery] = useState("BTCUSDT");
  const [results, setResults] = useState<MarketSearchItem[]>([]);
  const [snapshot, setSnapshot] = useState<MarketSnapshot | null>(null);
  const [rules, setRules] = useState<MarketRules | null>(null);
  const [orderbook, setOrderbook] = useState<OrderBook | null>(null);
  const [trades, setTrades] = useState<TradeTick[]>([]);
  const [guard, setGuard] = useState<TechnicalGuardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadMarket(symbolOverride?: string) {
    const symbol = (symbolOverride || query).toUpperCase();
    setError(null);
    try {
      const [searchResults, nextSnapshot, nextRules, nextBook, nextTrades, nextGuard] = await Promise.all([
        api.searchMarkets(query),
        api.getMarketSnapshot(symbol),
        api.getMarketRules(symbol),
        api.getMarketOrderbook(symbol),
        api.getMarketRecentTrades(symbol),
        api.checkTechnicalGuard(symbol),
      ]);
      setResults(searchResults);
      setSnapshot(nextSnapshot);
      setRules(nextRules);
      setOrderbook(nextBook);
      setTrades(nextTrades);
      setGuard(nextGuard);
      setQuery(symbol);
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  return (
    <div className="space-y-6">
      <SectionCard title="جستجوی بازار">
        <div className="flex flex-col gap-3 md:flex-row">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="flex-1 rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none focus:border-cyan-300/50"
            placeholder="مثلاً BTCUSDT"
          />
          <button type="button" onClick={() => loadMarket()} className="rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950">
            بارگذاری بازار
          </button>
        </div>
        {error ? <div className="mt-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}
        {results.length > 0 ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {results.slice(0, 10).map((item) => (
              <button key={item.symbol} type="button" onClick={() => loadMarket(item.symbol)} className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-slate-300">
                {item.symbol}
              </button>
            ))}
          </div>
        ) : null}
      </SectionCard>

      {!snapshot || !rules || !orderbook ? (
        <EmptyState title="هنوز بازاری انتخاب نشده است" description="یک نماد واقعی جستجو کنید تا snapshot، indicatorها، orderbook، trades و نتیجه Technical Guard نمایش داده شود." />
      ) : (
        <>
          <TradingViewPanel
            title="TradingView / Market Snapshot"
            symbol={query}
            exchange={snapshot.source.startsWith("BINANCE") ? "BINANCE" : "TABDEAL"}
            priceLines={[
              { label: "Analysis Close", value: snapshot.analysis_close, tone: "entry" },
              { label: "Support 20", value: snapshot.support_20, tone: "support" },
              { label: "Resistance 20", value: snapshot.resistance_20, tone: "resistance" },
              { label: "Spread %", value: snapshot.spread_pct, tone: "info" },
            ]}
            guardSummary={guard ? `${guard.allowed ? "ALLOWED" : "BLOCKED"} / ${guard.entry_type}` : null}
          />

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {[
              { label: "قیمت تحلیلی", value: snapshot.analysis_close },
              { label: "Best Bid / Ask", value: `${snapshot.best_bid} / ${snapshot.best_ask}` },
              { label: "Spread", value: `${snapshot.spread_pct}%` },
              { label: "Source", value: snapshot.source },
            ].map((item) => (
              <div key={item.label} className="glass-panel rounded-[28px] p-5">
                <div className="text-sm text-slate-400">{item.label}</div>
                <div className="mt-3 text-xl font-semibold text-white">{item.value}</div>
              </div>
            ))}
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
            <SectionCard title="Market Snapshot">
              <div className="grid gap-3 md:grid-cols-2">
                {Object.entries(snapshot).map(([key, value]) => (
                  <div key={key} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                    <div className="text-xs text-slate-400">{key}</div>
                    <div className="mt-2 text-sm text-white">{String(value)}</div>
                  </div>
                ))}
              </div>
            </SectionCard>

            <SectionCard title="Technical Guard برای BUY">
              {guard ? (
                <div className="space-y-4">
                  <StatusBadge value={guard.allowed ? "success" : "warning"} />
                  <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4 text-sm text-slate-300">
                    <div>Entry Type: {guard.entry_type}</div>
                    <div className="mt-2">Risk/Reward: {guard.risk_reward}</div>
                  </div>
                  {guard.reasons.length > 0 ? (
                    <ul className="space-y-2 text-sm text-rose-200">
                      {guard.reasons.map((reason) => (
                        <li key={reason} className="rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3">
                          {reason}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-200">
                      خرید از نگاه Technical Guard مجاز است.
                    </div>
                  )}
                </div>
              ) : null}
            </SectionCard>
          </div>

          <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
            <SectionCard title="Rules و Validation">
              <div className="space-y-3 text-sm">
                {[
                  ["minQty", rules.min_qty],
                  ["stepSize", rules.step_size],
                  ["minNotional", rules.min_notional],
                  ["tickSize", rules.tick_size],
                  ["pricePrecision", String(rules.price_precision)],
                  ["quantityPrecision", String(rules.quantity_precision)],
                  ["support / resistance", `${snapshot.support_20} / ${snapshot.resistance_20}`],
                ].map(([label, value]) => (
                  <div key={label} className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                    <span className="text-slate-400">{label}</span>
                    <span className="text-white">{value || "-"}</span>
                  </div>
                ))}
              </div>
            </SectionCard>

            <SectionCard title="Orderbook و Recent Trades">
              <div className="grid gap-6 md:grid-cols-2">
                <div>
                  <div className="mb-3 text-sm text-slate-400">Orderbook</div>
                  <div className="space-y-2">
                    {orderbook.asks.slice(0, 6).map((item, index) => (
                      <div key={`ask-${index}`} className="flex items-center justify-between rounded-xl bg-rose-400/8 px-3 py-2 text-xs">
                        <span className="text-rose-200">{item.price}</span>
                        <span className="text-slate-300">{item.quantity}</span>
                      </div>
                    ))}
                    {orderbook.bids.slice(0, 6).map((item, index) => (
                      <div key={`bid-${index}`} className="flex items-center justify-between rounded-xl bg-emerald-400/8 px-3 py-2 text-xs">
                        <span className="text-emerald-200">{item.price}</span>
                        <span className="text-slate-300">{item.quantity}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="mb-3 text-sm text-slate-400">Recent Trades</div>
                  <div className="space-y-2">
                    {trades.slice(0, 10).map((item, index) => (
                      <div key={`${item.id}-${index}`} className="rounded-xl border border-white/8 bg-white/[0.03] px-3 py-2 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="text-white">{item.price}</span>
                          <span className="text-slate-300">{item.quantity}</span>
                        </div>
                        <div className="mt-1 text-slate-500">
                          {item.timestamp ? formatDateTime(new Date(item.timestamp).toISOString()) : "بدون زمان"}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </SectionCard>
          </div>
        </>
      )}
    </div>
  );
}
