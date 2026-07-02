"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { SectionCard } from "@/components/section-card";
import { TradingViewPanel } from "@/components/tradingview-panel";
import { api } from "@/lib/api";
import type { PositionClosePreview, PositionItem } from "@/lib/types";
import { formatDateTime, normalizeError } from "@/lib/utils";

export function PositionsView() {
  const [positions, setPositions] = useState<PositionItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [tpSlDraft, setTpSlDraft] = useState<Record<number, string>>({});
  const [closePreview, setClosePreview] = useState<PositionClosePreview | null>(null);

  async function load() {
    setError(null);
    try {
      const result = await api.listPositions();
      setPositions(result);
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  useEffect(() => {
    load().catch(() => undefined);
  }, []);

  async function closePosition(id: number) {
    try {
      const preview = await api.closePositionPreview(id);
      if (preview.mode === "REAL_PENDING_CONFIRM") {
        setClosePreview(preview);
        return;
      }
      await api.closePosition(id, undefined);
      await load();
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  async function confirmRealClose() {
    if (!closePreview) return;
    try {
      await api.closePosition(closePreview.position_id, closePreview.confirm_token || undefined);
      setClosePreview(null);
      await load();
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  async function saveTpSl(position: PositionItem) {
    const draft = tpSlDraft[position.id] || `${position.take_profit || ""}|${position.stop_loss || ""}`;
    const [takeProfit, stopLoss] = draft.split("|");
    try {
      await api.updatePositionTpSl(position.id, {
        take_profit: takeProfit || null,
        stop_loss: stopLoss || null,
      });
      await load();
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  const openPositions = positions.filter((item) => item.status === "OPEN");
  const closedPositions = positions.filter((item) => item.status !== "OPEN");

  function renderTable(rows: PositionItem[], title: string) {
    return (
      <SectionCard title={title}>
        {rows.length === 0 ? (
          <EmptyState title="داده‌ای وجود ندارد" description="این بخش هنوز رکورد واقعی ندارد." />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="text-slate-400">
                <tr className="border-b border-white/8">
                  {["Symbol", "Qty", "Entry", "Current", "PnL", "TP/SL", "Opened", "Action"].map((head) => (
                    <th key={head} className="px-3 py-3 text-right font-medium">{head}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((position) => (
                  <tr key={position.id} className="border-b border-white/5">
                    <td className="px-3 py-3 text-white">{position.symbol}</td>
                    <td className="px-3 py-3 text-slate-200">{position.quantity}</td>
                    <td className="px-3 py-3 text-slate-200">{position.entry_price}</td>
                    <td className="px-3 py-3 text-slate-200">{position.current_price || "-"}</td>
                    <td className="px-3 py-3 text-slate-200">{position.pnl || "-"} / {position.pnl_pct || "-"}%</td>
                    <td className="px-3 py-3 text-slate-300">
                      <input
                        defaultValue={`${position.take_profit || ""}|${position.stop_loss || ""}`}
                        onBlur={(event) => setTpSlDraft((prev) => ({ ...prev, [position.id]: event.target.value }))}
                        className="w-40 rounded-xl border border-white/10 bg-[#091426] px-3 py-2 text-xs text-white outline-none"
                        placeholder="tp|sl"
                      />
                      <button type="button" onClick={() => saveTpSl(position)} className="mr-2 rounded-xl border border-white/10 px-3 py-2 text-xs text-slate-200">Save</button>
                    </td>
                    <td className="px-3 py-3 text-slate-300">{formatDateTime(position.opened_at)}</td>
                    <td className="px-3 py-3">
                      {position.status === "OPEN" ? (
                        <button type="button" onClick={() => closePosition(position.id)} className="rounded-xl border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-xs text-cyan-200">Close</button>
                      ) : (
                        <span className="text-slate-500">{position.status}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>
    );
  }

  return (
    <div className="space-y-6">
      {error ? <div className="rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}
      {openPositions[0] ? (
        <TradingViewPanel
          title="TradingView / Position Monitor"
          symbol={openPositions[0].symbol}
          exchange="BINANCE"
          priceLines={[
            { label: "Entry", value: openPositions[0].entry_price, tone: "entry" },
            { label: "Current", value: openPositions[0].current_price, tone: "info" },
            { label: "Take Profit", value: openPositions[0].take_profit, tone: "tp" },
            { label: "Stop Loss", value: openPositions[0].stop_loss, tone: "sl" },
          ]}
        />
      ) : null}
      {renderTable(openPositions, "پوزیشن‌های باز")}
      {renderTable(closedPositions, "پوزیشن‌های بسته")}
      {closePreview ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 px-4">
          <div className="w-full max-w-lg rounded-[28px] border border-yellow-400/20 bg-[#091426] p-6 shadow-2xl shadow-black/40">
            <div className="text-lg font-semibold text-white">تأیید دوم بستن پوزیشن</div>
            <p className="mt-3 text-sm leading-7 text-slate-300">
              بستن این پوزیشن در حالت real به ارسال سفارش market SELL منجر می‌شود. فقط در صورت آمادگی، تأیید نهایی را انجام دهید.
            </p>
            <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-slate-200">
              <div>Symbol: {closePreview.symbol}</div>
              <div className="mt-2">Quantity: {closePreview.quantity}</div>
              <div className="mt-2">Estimated Close Price: {closePreview.estimated_close_price}</div>
              <div className="mt-2">Estimated Value: {closePreview.estimated_value}</div>
            </div>
            <div className="mt-6 flex flex-wrap gap-3">
              <button type="button" onClick={confirmRealClose} className="rounded-2xl bg-yellow-400 px-4 py-3 text-sm font-semibold text-slate-950">
                تأیید نهایی بستن پوزیشن
              </button>
              <button type="button" onClick={() => setClosePreview(null)} className="rounded-2xl border border-white/10 px-4 py-3 text-sm text-slate-200">
                انصراف
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
