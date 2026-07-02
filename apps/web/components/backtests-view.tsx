"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { SectionCard } from "@/components/section-card";
import { SimpleLineChart } from "@/components/simple-line-chart";
import { api } from "@/lib/api";
import type { BacktestEquityPoint, BacktestRun, BacktestTrade, CsvImportResult } from "@/lib/types";
import { normalizeError } from "@/lib/utils";

export function BacktestsView() {
  const [strategy, setStrategy] = useState("EMA_RSI_VOLUME");
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [timeframe, setTimeframe] = useState("1m");
  const [startTime, setStartTime] = useState("2026-06-29T00:00");
  const [endTime, setEndTime] = useState("2026-06-30T00:00");
  const [initialBalance, setInitialBalance] = useState("1000");
  const [configJson, setConfigJson] = useState("{}");
  const [dataset, setDataset] = useState<CsvImportResult | null>(null);
  const [runs, setRuns] = useState<BacktestRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<BacktestRun | null>(null);
  const [equity, setEquity] = useState<BacktestEquityPoint[]>([]);
  const [trades, setTrades] = useState<BacktestTrade[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function loadRuns() {
    const result = await api.listBacktests();
    setRuns(result);
    if (!selectedRun && result[0]) {
      await selectRun(result[0].id);
    }
  }

  async function selectRun(runId: number) {
    const [run, nextTrades, nextEquity] = await Promise.all([api.getBacktest(runId), api.getBacktestTrades(runId), api.getBacktestEquity(runId)]);
    setSelectedRun(run);
    setTrades(nextTrades);
    setEquity(nextEquity);
  }

  useEffect(() => {
    loadRuns().catch((err) => setError(normalizeError(err)));
  }, []);

  return (
    <div className="space-y-6">
      <SectionCard title="اجرای Backtest">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <input value={strategy} onChange={(event) => setStrategy(event.target.value)} className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" placeholder="Strategy" />
          <input value={symbol} onChange={(event) => setSymbol(event.target.value)} className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" placeholder="Symbol" />
          <input value={timeframe} onChange={(event) => setTimeframe(event.target.value)} className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" placeholder="Timeframe" />
          <input value={startTime} onChange={(event) => setStartTime(event.target.value)} type="datetime-local" className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" />
          <input value={endTime} onChange={(event) => setEndTime(event.target.value)} type="datetime-local" className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" />
          <input value={initialBalance} onChange={(event) => setInitialBalance(event.target.value)} className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" placeholder="Initial Balance" />
          <textarea value={configJson} onChange={(event) => setConfigJson(event.target.value)} className="min-h-32 rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none md:col-span-2 xl:col-span-3" placeholder='{"max_steps":3}' />
          <label className="rounded-2xl border border-dashed border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-slate-300 md:col-span-2 xl:col-span-3">
            CSV fallback import
            <input
              type="file"
              accept=".csv"
              className="mt-3 block"
              onChange={async (event) => {
                const file = event.target.files?.[0];
                if (!file) return;
                try {
                  setDataset(await api.importBacktestCsv(file));
                } catch (err) {
                  setError(normalizeError(err));
                }
              }}
            />
            {dataset ? <div className="mt-2 text-xs text-cyan-300">dataset #{dataset.dataset_id} / rows {dataset.rows}</div> : null}
          </label>
        </div>
        <div className="mt-5 flex gap-3">
          <button
            type="button"
            onClick={async () => {
              try {
                const run = await api.runBacktest({
                  strategy_name: strategy,
                  symbol,
                  timeframe,
                  start_time: new Date(startTime).toISOString(),
                  end_time: new Date(endTime).toISOString(),
                  initial_balance: Number(initialBalance),
                  config_json: JSON.parse(configJson || "{}"),
                  csv_dataset_id: dataset?.dataset_id,
                });
                await loadRuns();
                await selectRun(run.id);
              } catch (err) {
                setError(normalizeError(err));
              }
            }}
            className="rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950"
          >
            Run Backtest
          </button>
        </div>
        {error ? <div className="mt-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}
      </SectionCard>

      {selectedRun ? (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {[
              ["Net PnL", selectedRun.net_pnl],
              ["Net PnL %", selectedRun.net_pnl_pct],
              ["Win Rate", selectedRun.win_rate],
              ["Profit Factor", selectedRun.profit_factor],
              ["Final Balance", selectedRun.final_balance],
              ["Max Drawdown", selectedRun.max_drawdown],
              ["Trades", String((selectedRun.result_json.total_trades as number) || 0)],
              ["Strategy", selectedRun.strategy_name],
            ].map(([label, value]) => (
              <div key={label} className="glass-panel rounded-[28px] p-5">
                <div className="text-sm text-slate-400">{label}</div>
                <div className="mt-3 text-xl font-semibold text-white">{value}</div>
              </div>
            ))}
          </div>

          <SectionCard title="Equity Curve">
            <SimpleLineChart points={equity.map((item) => ({ label: item.timestamp, value: item.equity }))} stroke="#facc15" />
          </SectionCard>

          <SectionCard title="Trades">
            {trades.length === 0 ? (
              <EmptyState title="تریدی ثبت نشده" description="این بک‌تست هنوز ترید واقعی در دیتابیس ندارد." />
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="text-slate-400">
                    <tr className="border-b border-white/8">
                      {["Symbol", "Entry", "Exit", "Qty", "PnL", "PnL %", "Reason"].map((head) => (
                        <th key={head} className="px-3 py-3 text-right font-medium">{head}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {trades.map((trade) => (
                      <tr key={trade.id} className="border-b border-white/5">
                        <td className="px-3 py-3 text-white">{trade.symbol}</td>
                        <td className="px-3 py-3 text-slate-200">{trade.entry_price}</td>
                        <td className="px-3 py-3 text-slate-200">{trade.exit_price}</td>
                        <td className="px-3 py-3 text-slate-200">{trade.quantity}</td>
                        <td className="px-3 py-3 text-slate-200">{trade.pnl}</td>
                        <td className="px-3 py-3 text-slate-200">{trade.pnl_pct}</td>
                        <td className="px-3 py-3 text-slate-300">{trade.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div className="mt-5">
              <button
                type="button"
                onClick={async () => {
                  const blob = await api.downloadCsv("/reports/export/backtests.csv");
                  const url = URL.createObjectURL(blob);
                  const link = document.createElement("a");
                  link.href = url;
                  link.download = "backtests.csv";
                  link.click();
                  URL.revokeObjectURL(url);
                }}
                className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-200"
              >
                Export CSV
              </button>
            </div>
          </SectionCard>
        </div>
      ) : (
        <EmptyState title="Backtest انتخاب نشده" description="بعد از اجرای یک بک‌تست، نتایج واقعی اینجا نمایش داده می‌شوند." />
      )}
    </div>
  );
}
