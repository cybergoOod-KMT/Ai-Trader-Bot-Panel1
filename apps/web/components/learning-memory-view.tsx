"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { SectionCard } from "@/components/section-card";
import { api } from "@/lib/api";
import type { LearningMemoryItem, TradeOutcomeItem } from "@/lib/types";
import { formatDateTime, normalizeError } from "@/lib/utils";

export function LearningMemoryView() {
  const [memoryRows, setMemoryRows] = useState<LearningMemoryItem[]>([]);
  const [outcomes, setOutcomes] = useState<TradeOutcomeItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.listLearningMemory(), api.listTradeOutcomes({ limit: 20 })])
      .then(([memory, trades]) => {
        setMemoryRows(memory);
        setOutcomes(trades);
      })
      .catch((err) => setError(normalizeError(err)));
  }, []);

  return (
    <div className="space-y-6">
      <SectionCard title="Learning Memory">
        <p className="mb-4 text-sm leading-7 text-slate-400">خلاصه‌ی محلی از نتیجه معاملات قبلی بر اساس symbol و strategy برای تغذیه تصمیم‌های بعدی AI.</p>
        {error ? <div className="mb-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}
        {memoryRows.length === 0 ? (
          <EmptyState title="هنوز حافظه محلی ساخته نشده است" description="بعد از بسته‌شدن پوزیشن‌ها، TradeOutcome و LearningMemory به‌صورت واقعی ساخته می‌شوند." />
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            {memoryRows.map((item) => (
              <div key={item.id} className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4">
                <div className="text-base font-semibold text-white">{item.symbol}</div>
                <div className="mt-1 text-sm text-slate-400">{item.strategy_name}</div>
                <pre className="mt-4 overflow-x-auto whitespace-pre-wrap rounded-2xl bg-[#091426] p-3 text-xs text-slate-200">
                  {JSON.stringify({ stats: item.stats_json, lessons: item.lessons_json }, null, 2)}
                </pre>
                <div className="mt-3 text-xs text-slate-500">{formatDateTime(item.updated_at)}</div>
              </div>
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="Trade Outcomes">
        <p className="mb-4 text-sm leading-7 text-slate-400">آخرین outcomeهای ثبت‌شده برای بررسی کیفیت حافظه محلی.</p>
        {outcomes.length === 0 ? (
          <EmptyState title="Outcomeای ثبت نشده است" description="این جدول بعد از بسته‌شدن پوزیشن‌های واقعی یا dry-run پر می‌شود." />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-right text-sm">
              <thead className="text-slate-400">
                <tr className="border-b border-white/8">
                  <th className="px-3 py-3">زمان</th>
                  <th className="px-3 py-3">نماد</th>
                  <th className="px-3 py-3">استراتژی</th>
                  <th className="px-3 py-3">PnL</th>
                  <th className="px-3 py-3">درصد</th>
                  <th className="px-3 py-3">خروج</th>
                </tr>
              </thead>
              <tbody>
                {outcomes.map((row) => (
                  <tr key={row.id} className="border-b border-white/6 text-slate-200">
                    <td className="px-3 py-3">{formatDateTime(row.created_at)}</td>
                    <td className="px-3 py-3">{row.symbol}</td>
                    <td className="px-3 py-3">{row.strategy_name}</td>
                    <td className={`px-3 py-3 ${Number(row.pnl) >= 0 ? "text-emerald-300" : "text-rose-300"}`}>{row.pnl}</td>
                    <td className="px-3 py-3">{row.pnl_pct}</td>
                    <td className="px-3 py-3">{row.exit_reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>
    </div>
  );
}
