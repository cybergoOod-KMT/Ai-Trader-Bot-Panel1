"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { SectionCard } from "@/components/section-card";
import { SimpleLineChart } from "@/components/simple-line-chart";
import { api } from "@/lib/api";
import type { PnlBucket, ReportSummary } from "@/lib/types";
import { normalizeError } from "@/lib/utils";

export function ReportsView() {
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [trades, setTrades] = useState<Array<Record<string, unknown>>>([]);
  const [aiDecisions, setAiDecisions] = useState<Array<Record<string, unknown>>>([]);
  const [botDecisions, setBotDecisions] = useState<Array<Record<string, unknown>>>([]);
  const [backtests, setBacktests] = useState<Array<Record<string, unknown>>>([]);
  const [pnlBySymbol, setPnlBySymbol] = useState<PnlBucket[]>([]);
  const [pnlByStrategy, setPnlByStrategy] = useState<PnlBucket[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [symbol, setSymbol] = useState("");
  const [strategy, setStrategy] = useState("");
  const [mode, setMode] = useState("");

  async function load() {
    const [nextSummary, nextTrades, nextAi, nextBots, nextBacktests, nextBySymbol, nextByStrategy] = await Promise.all([
      api.getReportSummary(),
      api.getReportTrades({ symbol: symbol || undefined, strategy: strategy || undefined, mode: mode || undefined }),
      api.getReportAiDecisions(symbol || undefined),
      api.getReportBotDecisions(symbol || undefined),
      api.getReportBacktests({ symbol: symbol || undefined, strategy: strategy || undefined }),
      api.getPnlBySymbol(),
      api.getPnlByStrategy(),
    ]);
    setSummary(nextSummary);
    setTrades(nextTrades);
    setAiDecisions(nextAi);
    setBotDecisions(nextBots);
    setBacktests(nextBacktests);
    setPnlBySymbol(nextBySymbol);
    setPnlByStrategy(nextByStrategy);
  }

  useEffect(() => {
    load().catch((err) => setError(normalizeError(err)));
  }, []);

  return (
    <div className="space-y-6">
      <SectionCard title="فیلتر گزارش‌ها">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <input value={symbol} onChange={(event) => setSymbol(event.target.value)} placeholder="Symbol" className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" />
          <input value={strategy} onChange={(event) => setStrategy(event.target.value)} placeholder="Strategy" className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" />
          <select value={mode} onChange={(event) => setMode(event.target.value)} className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none">
            <option value="">همه modeها</option>
            <option value="DRY_RUN">DRY_RUN</option>
            <option value="REAL_SENT">REAL_SENT</option>
            <option value="REAL_FILLED">REAL_FILLED</option>
          </select>
          <button type="button" onClick={() => load().catch((err) => setError(normalizeError(err)))} className="rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950">
            اعمال فیلتر
          </button>
        </div>
        {error ? <div className="mt-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}
      </SectionCard>

      {summary ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {[
            ["Trades", String(summary.trades_count)],
            ["AI Decisions", String(summary.ai_decisions_count)],
            ["Bot Decisions", String(summary.bot_decisions_count)],
            ["Backtests", String(summary.backtests_count)],
            ["Script Runs", String(summary.script_runs_count)],
            ["Dry PnL", summary.dry_run_pnl.toFixed(2)],
            ["Real PnL", summary.real_pnl.toFixed(2)],
          ].map(([label, value]) => (
            <div key={label} className="glass-panel rounded-[28px] p-5">
              <div className="text-sm text-slate-400">{label}</div>
              <div className="mt-3 text-2xl font-semibold text-white">{value}</div>
            </div>
          ))}
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <SectionCard title="PnL by Symbol">
          <SimpleLineChart points={pnlBySymbol.map((item) => ({ label: item.key, value: item.pnl }))} />
        </SectionCard>
        <SectionCard title="PnL by Strategy">
          <SimpleLineChart points={pnlByStrategy.map((item) => ({ label: item.key, value: item.pnl }))} stroke="#a78bfa" />
        </SectionCard>
      </div>

      <SectionCard title="Trades">
        {trades.length === 0 ? <EmptyState title="Tradeای وجود ندارد" description="گزارش معاملات بعد از ثبت رکوردهای واقعی پر می‌شود." /> : <ReportTable rows={trades} />}
        <ExportButtons paths={["/reports/export/trades.csv", "/reports/export/ai-decisions.csv", "/reports/export/backtests.csv", "/reports/export/bot_decisions.csv", "/reports/export/script_logs.csv"]} />
      </SectionCard>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <SectionCard title="AI Decisions">
          {aiDecisions.length === 0 ? <EmptyState title="داده‌ای نیست" description="تصمیم‌های AI اینجا نمایش داده می‌شوند." /> : <ReportTable rows={aiDecisions} />}
        </SectionCard>
        <SectionCard title="Bot Decisions">
          {botDecisions.length === 0 ? <EmptyState title="داده‌ای نیست" description="تصمیم‌های Bot اینجا نمایش داده می‌شوند." /> : <ReportTable rows={botDecisions} />}
        </SectionCard>
      </div>

      <SectionCard title="Backtests">
        {backtests.length === 0 ? <EmptyState title="Backtestی وجود ندارد" description="بعد از اجرای بک‌تست، این جدول از دیتابیس واقعی پر می‌شود." /> : <ReportTable rows={backtests} />}
      </SectionCard>
    </div>
  );
}

function ReportTable({ rows }: { rows: Array<Record<string, unknown>> }) {
  const columns = Object.keys(rows[0] || {}).slice(0, 8);
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="text-slate-400">
          <tr className="border-b border-white/8">
            {columns.map((head) => (
              <th key={head} className="px-3 py-3 text-right font-medium">{head}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className="border-b border-white/5">
              {columns.map((column) => (
                <td key={column} className="px-3 py-3 text-slate-200">{String(row[column] ?? "-")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ExportButtons({ paths }: { paths: string[] }) {
  return (
    <div className="mt-5 flex flex-wrap gap-3">
      {paths.map((path) => (
        <button
          key={path}
          type="button"
          onClick={async () => {
            const blob = await api.downloadCsv(path);
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = path.split("/").pop() || "export.csv";
            link.click();
            URL.revokeObjectURL(url);
          }}
          className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-200"
        >
          Export {path.split("/").pop()}
        </button>
      ))}
    </div>
  );
}
