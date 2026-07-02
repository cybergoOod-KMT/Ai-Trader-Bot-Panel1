"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { SectionCard } from "@/components/section-card";
import { api } from "@/lib/api";
import type { ManualOrder } from "@/lib/types";
import { formatDateTime, normalizeError } from "@/lib/utils";

export function OrdersView() {
  const [orders, setOrders] = useState<ManualOrder[]>([]);
  const [symbol, setSymbol] = useState("");
  const [mode, setMode] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      const result = await api.listManualOrders({ symbol: symbol || undefined, mode: mode || undefined });
      setOrders(result);
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  useEffect(() => {
    load().catch(() => undefined);
  }, []);

  async function cancelOrder(id: number) {
    try {
      await api.cancelManualOrder(id);
      await load();
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  return (
    <SectionCard title="سفارش‌ها">
      <div className="mb-4 flex flex-col gap-3 md:flex-row">
        <input value={symbol} onChange={(e) => setSymbol(e.target.value)} placeholder="Filter symbol" className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" />
        <select value={mode} onChange={(e) => setMode(e.target.value)} className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none">
          <option value="">همه حالت‌ها</option>
          <option value="DRY_RUN">DRY_RUN</option>
          <option value="REAL_PENDING_CONFIRM">REAL_PENDING_CONFIRM</option>
        </select>
        <button type="button" onClick={() => load()} className="rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950">اعمال فیلتر</button>
      </div>
      {error ? <div className="mb-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}
      {orders.length === 0 ? (
        <EmptyState title="سفارشی وجود ندارد" description="بعد از ایجاد سفارش‌های Dry Run یا Real، این لیست به‌صورت واقعی پر می‌شود." />
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="text-slate-400">
              <tr className="border-b border-white/8">
                {["زمان", "Symbol", "Side", "Type", "Status", "Mode", "Exchange ID", "Error", "Action"].map((head) => (
                  <th key={head} className="px-3 py-3 text-right font-medium">{head}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr key={order.id} className="border-b border-white/5">
                  <td className="px-3 py-3 text-slate-300">{formatDateTime(order.created_at)}</td>
                  <td className="px-3 py-3 text-white">{order.symbol}</td>
                  <td className="px-3 py-3 text-slate-200">{order.side}</td>
                  <td className="px-3 py-3 text-slate-200">{order.order_type}</td>
                  <td className="px-3 py-3 text-slate-200">{order.status}</td>
                  <td className="px-3 py-3 text-slate-300">{order.mode}</td>
                  <td className="px-3 py-3 text-slate-400">{order.exchange_order_id || "-"}</td>
                  <td className="px-3 py-3 text-rose-200">{order.error_message || "-"}</td>
                  <td className="px-3 py-3">
                    {["REAL_SENT", "PENDING", "REAL_PENDING_CONFIRM", "NEW"].includes(order.status) ? (
                      <button type="button" onClick={() => cancelOrder(order.id)} className="rounded-xl border border-rose-400/20 bg-rose-400/10 px-3 py-2 text-xs text-rose-200">Cancel</button>
                    ) : (
                      <span className="text-slate-500">-</span>
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
