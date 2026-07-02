"use client";

import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { SectionCard } from "@/components/section-card";
import { StatusBadge } from "@/components/status-badge";
import { TradingViewPanel } from "@/components/tradingview-panel";
import { api } from "@/lib/api";
import type { DashboardResponse, ManualOrderCreateResponse, ManualOrderPreviewResponse, MarketRules, MarketSnapshot, OrderBook } from "@/lib/types";
import { normalizeError } from "@/lib/utils";

type Mode = "DRY_RUN" | "REAL";

export function ManualTradingView() {
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [side, setSide] = useState("BUY");
  const [orderType, setOrderType] = useState("MARKET");
  const [quantity, setQuantity] = useState("");
  const [usdtAmount, setUsdtAmount] = useState("");
  const [price, setPrice] = useState("");
  const [mode, setMode] = useState<Mode>("DRY_RUN");
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [rules, setRules] = useState<MarketRules | null>(null);
  const [snapshot, setSnapshot] = useState<MarketSnapshot | null>(null);
  const [orderbook, setOrderbook] = useState<OrderBook | null>(null);
  const [preview, setPreview] = useState<ManualOrderPreviewResponse | null>(null);
  const [created, setCreated] = useState<ManualOrderCreateResponse | null>(null);
  const [pendingConfirmToken, setPendingConfirmToken] = useState<string | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const normalizedSymbol = useMemo(() => {
    const cleaned = symbol.toUpperCase().replace("/", "").replace("_", "").replace("-", "");
    return cleaned.endsWith("USDT") ? cleaned : `${cleaned}USDT`;
  }, [symbol]);

  async function loadMarketData() {
    setError(null);
    try {
      const [dash, nextRules, nextSnapshot, nextOrderbook] = await Promise.all([
        api.getDashboard(),
        api.getMarketRules(normalizedSymbol),
        api.getMarketSnapshot(normalizedSymbol),
        api.getMarketOrderbook(normalizedSymbol),
      ]);
      setDashboard(dash);
      setRules(nextRules);
      setSnapshot(nextSnapshot);
      setOrderbook(nextOrderbook);
      if (!price && nextSnapshot.analysis_close) {
        setPrice(nextSnapshot.analysis_close);
      }
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  useEffect(() => {
    loadMarketData().catch(() => undefined);
  }, []);

  async function handlePreview() {
    setError(null);
    try {
      const result = await api.previewManualOrder({
        symbol: normalizedSymbol,
        side,
        order_type: orderType,
        quantity: quantity || undefined,
        price: orderType === "LIMIT" ? price : undefined,
        usdt_amount: usdtAmount || undefined,
        prefer_real_execution: mode === "REAL",
      });
      setPreview(result);
      setCreated(null);
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  async function handleSubmit() {
    setError(null);
    setMessage(null);
    try {
      const result = await api.createManualOrder({
        symbol: normalizedSymbol,
        side,
        order_type: orderType,
        quantity: quantity || undefined,
        price: orderType === "LIMIT" ? price : undefined,
        usdt_amount: usdtAmount || undefined,
        prefer_real_execution: mode === "REAL",
      });
      setCreated(result);
      setPreview(result.preview);
      setMessage(result.confirm_token ? "سفارش در انتظار تأیید دوم ثبت شد." : "سفارش با موفقیت ثبت شد.");
      if (result.confirm_token) {
        setPendingConfirmToken(result.confirm_token);
        setShowConfirmModal(true);
      }
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  async function handleConfirmReal() {
    if (!created || !pendingConfirmToken) return;
    setError(null);
    try {
      await api.confirmRealOrder(created.order.id, pendingConfirmToken);
      setMessage("سفارش واقعی به Tabdeal ارسال شد.");
      setCreated(null);
      setPendingConfirmToken(null);
      setShowConfirmModal(false);
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  const submitBlocked = preview ? !preview.risk.allowed || (side === "BUY" && preview.technical_guard ? !preview.technical_guard.allowed : false) : true;

  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <SectionCard title="فرم معامله دستی">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="space-y-2">
              <span className="text-sm text-slate-300">Symbol</span>
              <input value={symbol} onChange={(event) => setSymbol(event.target.value)} onBlur={() => setSymbol(normalizedSymbol)} className="w-full rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none focus:border-cyan-300/50" />
            </label>
            <label className="space-y-2">
              <span className="text-sm text-slate-300">Side</span>
              <select value={side} onChange={(event) => setSide(event.target.value)} className="w-full rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none">
                <option value="BUY">BUY</option>
                <option value="SELL">SELL</option>
              </select>
            </label>
            <label className="space-y-2">
              <span className="text-sm text-slate-300">Type</span>
              <select value={orderType} onChange={(event) => setOrderType(event.target.value)} className="w-full rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none">
                <option value="MARKET">MARKET</option>
                <option value="LIMIT">LIMIT</option>
              </select>
            </label>
            <label className="space-y-2">
              <span className="text-sm text-slate-300">Mode</span>
              <select value={mode} onChange={(event) => setMode(event.target.value as Mode)} className="w-full rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none">
                <option value="DRY_RUN">DRY_RUN</option>
                <option value="REAL">REAL</option>
              </select>
            </label>
            <label className="space-y-2">
              <span className="text-sm text-slate-300">Quantity</span>
              <input value={quantity} onChange={(event) => setQuantity(event.target.value)} className="w-full rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" placeholder="مثلاً 0.01" />
            </label>
            <label className="space-y-2">
              <span className="text-sm text-slate-300">USDT Amount Helper</span>
              <input value={usdtAmount} onChange={(event) => setUsdtAmount(event.target.value)} className="w-full rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" placeholder="مثلاً 100" />
            </label>
            {orderType === "LIMIT" ? (
              <label className="space-y-2 md:col-span-2">
                <span className="text-sm text-slate-300">Price</span>
                <input value={price} onChange={(event) => setPrice(event.target.value)} className="w-full rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" />
              </label>
            ) : null}
          </div>

          <div className="mt-5 flex flex-wrap gap-3">
            <button type="button" onClick={() => loadMarketData()} className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-slate-200">جستجوی بازار</button>
            <button type="button" onClick={handlePreview} className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-200">Preview</button>
            <button type="button" onClick={handleSubmit} disabled={submitBlocked} className="rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50">Submit</button>
          </div>

          {message ? <div className="mt-4 rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-200">{message}</div> : null}
          {error ? <div className="mt-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}

        </SectionCard>

        <SectionCard title="وضعیت بازار و حساب">
          {!snapshot || !rules || !orderbook ? (
            <EmptyState title="بازار بارگذاری نشده" description="ابتدا یک symbol جستجو کنید تا قوانین بازار، bid/ask، spread و snapshot واقعی نمایش داده شود." />
          ) : (
            <div className="space-y-4">
              <div className="grid gap-3 md:grid-cols-2">
                {[
                  ["Current Price", snapshot.analysis_close],
                  ["Bid / Ask", `${snapshot.best_bid} / ${snapshot.best_ask}`],
                  ["Spread", `${snapshot.spread_pct}%`],
                  ["Mode", mode],
                  ["minQty", rules.min_qty || "-"],
                  ["stepSize", rules.step_size || "-"],
                  ["minNotional", rules.min_notional || "-"],
                  ["Balance Items", String(dashboard?.balances.length || 0)],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                    <div className="text-xs text-slate-400">{label}</div>
                    <div className="mt-2 text-sm text-white">{value}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </SectionCard>
      </div>

      {snapshot ? (
        <TradingViewPanel
          title="TradingView / Manual Trading"
          symbol={normalizedSymbol}
          exchange={snapshot.source.startsWith("BINANCE") ? "BINANCE" : "TABDEAL"}
          priceLines={[
            { label: "Current Price", value: snapshot.analysis_close, tone: "entry" },
            { label: "Best Bid", value: snapshot.best_bid, tone: "support" },
            { label: "Best Ask", value: snapshot.best_ask, tone: "resistance" },
            { label: "Support 20", value: snapshot.support_20, tone: "support" },
            { label: "Resistance 20", value: snapshot.resistance_20, tone: "resistance" },
          ]}
          guardSummary={preview?.technical_guard ? `${preview.technical_guard.entry_type} / RR ${preview.technical_guard.risk_reward}` : null}
        />
      ) : null}

      {preview ? (
        <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <SectionCard title="Order Preview / Risk Manager">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <StatusBadge value={preview.risk.allowed ? "success" : "warning"} />
                <span className="text-sm text-slate-300">Mode: {preview.risk.mode}</span>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4 text-sm text-slate-300">
                <div>Quantity: {preview.normalized_quantity}</div>
                <div className="mt-2">Price: {preview.normalized_price || preview.market_snapshot.analysis_close}</div>
                <div className="mt-2">Estimated Value: {preview.estimated_value}</div>
              </div>
              {preview.risk.reasons.length > 0 ? (
                <ul className="space-y-2">
                  {preview.risk.reasons.map((reason) => (
                    <li key={reason} className="rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">{reason}</li>
                  ))}
                </ul>
              ) : (
                <div className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-200">Risk Manager این سفارش را مجاز می‌داند.</div>
              )}
            </div>
          </SectionCard>

          <SectionCard title="Technical Guard">
            {preview.technical_guard ? (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <StatusBadge value={preview.technical_guard.allowed ? "success" : "warning"} />
                  <span className="text-sm text-slate-300">Entry Type: {preview.technical_guard.entry_type}</span>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4 text-sm text-slate-300">Risk/Reward: {preview.technical_guard.risk_reward}</div>
                {preview.technical_guard.reasons.length > 0 ? (
                  <ul className="space-y-2">
                    {preview.technical_guard.reasons.map((reason) => (
                      <li key={reason} className="rounded-2xl border border-yellow-400/20 bg-yellow-400/10 px-4 py-3 text-sm text-yellow-100">{reason}</li>
                    ))}
                  </ul>
                ) : (
                  <div className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-200">از نگاه Technical Guard، خرید مجاز است.</div>
                )}
              </div>
            ) : (
              <div className="text-sm text-slate-400">برای SELL بررسی Technical Guard لازم نیست.</div>
            )}
          </SectionCard>
        </div>
      ) : null}

      {showConfirmModal && created ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 px-4">
          <div className="w-full max-w-lg rounded-[28px] border border-yellow-400/20 bg-[#091426] p-6 shadow-2xl shadow-black/40">
            <div className="text-lg font-semibold text-white">تأیید دوم سفارش واقعی</div>
            <p className="mt-3 text-sm leading-7 text-slate-300">
              این سفارش در حالت real ارسال می‌شود. تا زمانی که این مرحله را تأیید نکنید، backend هیچ سفارش واقعی به Tabdeal ارسال نخواهد کرد.
            </p>
            <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-slate-200">
              <div>Symbol: {created.order.symbol}</div>
              <div className="mt-2">Side: {created.order.side}</div>
              <div className="mt-2">Type: {created.order.order_type}</div>
              <div className="mt-2">Quantity: {created.order.quantity}</div>
            </div>
            <div className="mt-6 flex flex-wrap gap-3">
              <button type="button" onClick={handleConfirmReal} className="rounded-2xl bg-yellow-400 px-4 py-3 text-sm font-semibold text-slate-950">
                تأیید نهایی و ارسال سفارش
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowConfirmModal(false);
                  setPendingConfirmToken(null);
                }}
                className="rounded-2xl border border-white/10 px-4 py-3 text-sm text-slate-200"
              >
                انصراف
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
