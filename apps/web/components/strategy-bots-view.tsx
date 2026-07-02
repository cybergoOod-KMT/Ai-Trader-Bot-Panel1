"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { SectionCard } from "@/components/section-card";
import { api, wsUrl } from "@/lib/api";
import type { BotConfig, BotDecision, BotRun, WatchTask } from "@/lib/types";
import { normalizeError } from "@/lib/utils";

const strategyOptions = [
  "EMA_RSI_VOLUME",
  "MACD_BREAKOUT",
  "SUPPORT_RESISTANCE_BREAKOUT",
  "MEAN_REVERSION_RSI",
  "GRID_SIMPLE",
  "DCA_SIMPLE",
];

export function StrategyBotsView() {
  const [bots, setBots] = useState<BotConfig[]>([]);
  const [selectedBotId, setSelectedBotId] = useState<number | null>(null);
  const [decisions, setDecisions] = useState<BotDecision[]>([]);
  const [runs, setRuns] = useState<BotRun[]>([]);
  const [watchTasks, setWatchTasks] = useState<WatchTask[]>([]);
  const [stream, setStream] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [confirmToken, setConfirmToken] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    mode: "DRY_RUN",
    api_account_id: 1,
    symbols_json: "BTCUSDT",
    max_total_budget_usdt: "500",
    per_order_usdt: "50",
    max_open_positions: 3,
    max_daily_loss_pct: "5",
    min_ai_confidence: 60,
    technical_guard_enabled: true,
    strategy_name: "EMA_RSI_VOLUME",
  });

  async function load() {
    try {
      const [allBots, allWatchTasks] = await Promise.all([api.listBots(), api.listWatchTasks()]);
      const strategyBots = allBots.filter((item) => item.strategy_name !== "AI_TECHNICAL_GUARD");
      setBots(strategyBots);
      setWatchTasks(allWatchTasks);
      if (!selectedBotId && strategyBots[0]) setSelectedBotId(strategyBots[0].id);
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  useEffect(() => {
    load().catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!selectedBotId) return;
    api.getBotDecisions(selectedBotId).then(setDecisions).catch(() => undefined);
    api.getBotRuns(selectedBotId).then(setRuns).catch(() => undefined);
  }, [selectedBotId]);

  useEffect(() => {
    const run = runs.find((item) => item.status === "RUNNING");
    if (!run) return;
    const socket = new WebSocket(wsUrl(`/ws/bots/${run.id}`));
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data) as { type: string; payload: Record<string, unknown> };
      setStream((prev) => [`${data.type}: ${JSON.stringify(data.payload)}`, ...prev].slice(0, 25));
    };
    return () => socket.close();
  }, [runs]);

  async function createBot() {
    try {
      const created = await api.createBot({
        ...form,
        symbols_json: form.symbols_json.split(",").map((item) => item.trim()).filter(Boolean),
      });
      await load();
      setSelectedBotId(created.id);
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  async function startSelected(token?: string | null) {
    if (!selectedBotId) return;
    try {
      const result = await api.startBot(selectedBotId, token);
      if (result.confirm_token) {
        setConfirmToken(result.confirm_token);
      } else {
        setConfirmToken(null);
        setRuns(await api.getBotRuns(selectedBotId));
        await load();
      }
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  async function stopSelected() {
    if (!selectedBotId) return;
    try {
      await api.stopBot(selectedBotId);
      setRuns(await api.getBotRuns(selectedBotId));
      await load();
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
      <div className="space-y-6">
        <SectionCard title="Create Strategy Bot">
          <div className="grid gap-3 md:grid-cols-2">
            <input value={form.name} onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))} placeholder="Name" className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" />
            <select value={form.strategy_name} onChange={(e) => setForm((prev) => ({ ...prev, strategy_name: e.target.value }))} className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none">
              {strategyOptions.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
            <select value={form.mode} onChange={(e) => setForm((prev) => ({ ...prev, mode: e.target.value }))} className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none">
              <option value="DRY_RUN">DRY_RUN</option>
              <option value="REAL">REAL</option>
            </select>
            <input value={form.symbols_json} onChange={(e) => setForm((prev) => ({ ...prev, symbols_json: e.target.value }))} placeholder="Symbols" className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" />
          </div>
          <div className="mt-4 flex flex-wrap gap-3">
            <button type="button" onClick={createBot} className="rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950">Create Bot</button>
            {selectedBotId ? <button type="button" onClick={() => startSelected()} className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-200">Start</button> : null}
            {selectedBotId ? <button type="button" onClick={stopSelected} className="rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">Stop</button> : null}
          </div>
          {confirmToken ? <button type="button" onClick={() => startSelected(confirmToken)} className="mt-4 rounded-2xl bg-yellow-400 px-4 py-3 text-sm font-semibold text-slate-950">Confirm Real Bot Start</button> : null}
          {error ? <div className="mt-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}
        </SectionCard>

        <SectionCard title="Strategy Bots">
          {bots.length === 0 ? (
            <EmptyState title="Strategy Botی ساخته نشده است" description="اول یک strategy bot بسازید." />
          ) : (
            <div className="space-y-3">
              {bots.map((bot) => (
                <button key={bot.id} type="button" onClick={() => setSelectedBotId(bot.id)} className="w-full rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-right text-sm">
                  <div className="text-white">{bot.name}</div>
                  <div className="mt-2 text-slate-400">{bot.strategy_name} / {bot.mode}</div>
                </button>
              ))}
            </div>
          )}
        </SectionCard>
      </div>

      <div className="space-y-6">
        <SectionCard title="Live Logs / Decisions">
          <div className="space-y-3">
            {stream.length === 0 ? (
              <EmptyState title="جریان زنده‌ای وجود ندارد" description="بعد از start شدن bot، eventها اینجا stream می‌شوند." />
            ) : stream.map((line, index) => (
              <div key={`${line}-${index}`} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-slate-200">{line}</div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Runs / Decisions / Watches">
          <div className="space-y-3 text-sm">
            {runs.map((run) => (
              <div key={run.id} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-white">Run #{run.id} / {run.status}</div>
            ))}
            {decisions.slice(0, 12).map((decision) => (
              <div key={decision.id} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                <div className="text-white">{decision.symbol} / {decision.action}</div>
                <div className="mt-2 text-slate-400">{decision.reason}</div>
              </div>
            ))}
            {watchTasks.filter((task) => runs.some((run) => run.id === task.bot_run_id)).map((task) => (
              <div key={task.id} className="rounded-2xl border border-yellow-400/20 bg-yellow-400/10 px-4 py-3 text-yellow-100">
                {task.symbol} / {task.type} / {task.status}
              </div>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
