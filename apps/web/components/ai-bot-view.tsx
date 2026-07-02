"use client";

import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { SectionCard } from "@/components/section-card";
import { api, wsUrl } from "@/lib/api";
import type { BotConfig, BotDecision, BotRun, WatchTask } from "@/lib/types";
import { formatDateTime, normalizeError } from "@/lib/utils";

export function AiBotView() {
  const [bots, setBots] = useState<BotConfig[]>([]);
  const [selectedBotId, setSelectedBotId] = useState<number | null>(null);
  const [runs, setRuns] = useState<BotRun[]>([]);
  const [decisions, setDecisions] = useState<BotDecision[]>([]);
  const [watchTasks, setWatchTasks] = useState<WatchTask[]>([]);
  const [stream, setStream] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [startToken, setStartToken] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    mode: "DRY_RUN",
    api_account_id: 1,
    symbols_json: "BTCUSDT,LTCUSDT",
    max_total_budget_usdt: "500",
    per_order_usdt: "50",
    max_open_positions: 3,
    max_daily_loss_pct: "5",
    min_ai_confidence: 65,
    technical_guard_enabled: true,
  });

  const selectedBot = useMemo(() => bots.find((item) => item.id === selectedBotId) || null, [bots, selectedBotId]);

  async function load() {
    try {
      const [allBots, allWatchTasks] = await Promise.all([api.listBots(), api.listWatchTasks()]);
      const aiBots = allBots.filter((item) => item.strategy_name === "AI_TECHNICAL_GUARD");
      setBots(aiBots);
      setWatchTasks(allWatchTasks);
      if (!selectedBotId && aiBots[0]) setSelectedBotId(aiBots[0].id);
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  useEffect(() => {
    load().catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!selectedBotId) return;
    api.getBotRuns(selectedBotId).then(setRuns).catch(() => undefined);
    api.getBotDecisions(selectedBotId).then(setDecisions).catch(() => undefined);
  }, [selectedBotId]);

  useEffect(() => {
    const run = runs.find((item) => item.status === "RUNNING");
    if (!run) return;
    const socket = new WebSocket(wsUrl(`/ws/bots/${run.id}`));
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data) as { type: string; payload: Record<string, unknown> };
      if (data.type === "bot_decision") {
        setStream((prev) => [`${String(data.payload.symbol)} => ${String(data.payload.action)}`, ...prev].slice(0, 30));
      }
      if (data.type === "watch_task") {
        setStream((prev) => [`Watch ${String(data.payload.symbol)} => ${String(data.payload.status)}`, ...prev].slice(0, 30));
        load().catch(() => undefined);
      }
    };
    return () => socket.close();
  }, [runs]);

  async function createBot() {
    setError(null);
    try {
      const created = await api.createBot({
        ...form,
        strategy_name: "AI_TECHNICAL_GUARD",
        symbols_json: form.symbols_json.split(",").map((item) => item.trim()).filter(Boolean),
      });
      await load();
      setSelectedBotId(created.id);
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  async function startBot(confirmToken?: string | null) {
    if (!selectedBotId) return;
    try {
      const result = await api.startBot(selectedBotId, confirmToken);
      if (result.confirm_token) {
        setStartToken(result.confirm_token);
      } else {
        setStartToken(null);
        await load();
        setRuns(await api.getBotRuns(selectedBotId));
      }
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  async function stopBot() {
    if (!selectedBotId) return;
    try {
      await api.stopBot(selectedBotId);
      await load();
      setRuns(await api.getBotRuns(selectedBotId));
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
      <div className="space-y-6">
        <SectionCard title="Create AI Bot">
          <div className="grid gap-3 md:grid-cols-2">
            <input placeholder="Name" value={form.name} onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))} className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" />
            <select value={form.mode} onChange={(e) => setForm((prev) => ({ ...prev, mode: e.target.value }))} className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none">
              <option value="DRY_RUN">DRY_RUN</option>
              <option value="REAL">REAL</option>
            </select>
            <input placeholder="Symbols" value={form.symbols_json} onChange={(e) => setForm((prev) => ({ ...prev, symbols_json: e.target.value }))} className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none md:col-span-2" />
            <input placeholder="Max Budget" value={form.max_total_budget_usdt} onChange={(e) => setForm((prev) => ({ ...prev, max_total_budget_usdt: e.target.value }))} className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" />
            <input placeholder="Per Order" value={form.per_order_usdt} onChange={(e) => setForm((prev) => ({ ...prev, per_order_usdt: e.target.value }))} className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" />
          </div>
          <div className="mt-4 flex flex-wrap gap-3">
            <button type="button" onClick={createBot} className="rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950">Create AI Bot</button>
            {selectedBot ? <button type="button" onClick={() => startBot()} className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-200">Start</button> : null}
            {selectedBot ? <button type="button" onClick={stopBot} className="rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">Stop</button> : null}
          </div>
          {error ? <div className="mt-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}
          {startToken ? (
            <div className="mt-4 rounded-2xl border border-yellow-400/20 bg-yellow-400/10 p-4 text-sm text-yellow-100">
              این ربات در حالت REAL است و نیاز به تأیید دوم دارد.
              <button type="button" onClick={() => startBot(startToken)} className="mt-3 rounded-2xl bg-yellow-400 px-4 py-3 text-sm font-semibold text-slate-950">Confirm Real Start</button>
            </div>
          ) : null}
        </SectionCard>

        <SectionCard title="AI Bots">
          {bots.length === 0 ? (
            <EmptyState title="AI Botی ساخته نشده است" description="اول یک AI Bot واقعی بسازید." />
          ) : (
            <div className="space-y-3">
              {bots.map((bot) => (
                <button key={bot.id} type="button" onClick={() => setSelectedBotId(bot.id)} className="w-full rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-right text-sm">
                  <div className="text-white">{bot.name}</div>
                  <div className="mt-2 text-slate-400">{bot.mode} / confidence {bot.min_ai_confidence}</div>
                </button>
              ))}
            </div>
          )}
        </SectionCard>

        <SectionCard title="Live Decision Stream">
          <div className="space-y-2">
            {stream.length === 0 ? (
              <EmptyState title="جریان زنده‌ای دریافت نشده است" description="بعد از Start شدن Bot، لاگ تصمیم‌ها اینجا stream می‌شود." />
            ) : (
              stream.map((line, index) => (
                <div key={`${line}-${index}`} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-slate-200">{line}</div>
              ))
            )}
          </div>
        </SectionCard>
      </div>

      <div className="space-y-6">
        <SectionCard title="Runs / Decisions">
          <div className="space-y-3">
            {runs.map((run) => (
              <div key={run.id} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm">
                <div className="text-white">Run #{run.id} / {run.status}</div>
                <div className="mt-2 text-slate-400">{formatDateTime(run.started_at)}</div>
              </div>
            ))}
            {decisions.slice(0, 12).map((decision) => (
              <div key={decision.id} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm">
                <div className="text-white">{decision.symbol} / {decision.action}</div>
                <div className="mt-2 text-slate-300">{decision.reason}</div>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Watch Tasks">
          <div className="space-y-3">
            {watchTasks.filter((task) => (selectedBot ? runs.some((run) => run.id === task.bot_run_id) : true)).map((task) => (
              <div key={task.id} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm">
                <div className="text-white">{task.symbol} / {task.type}</div>
                <div className="mt-2 text-slate-400">{task.status} / trigger {task.trigger_price}</div>
                <button type="button" onClick={() => api.cancelWatchTask(task.id).then(() => load())} className="mt-3 rounded-xl border border-rose-400/20 bg-rose-400/10 px-3 py-2 text-xs text-rose-200">Cancel Watch</button>
              </div>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
