"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { SectionCard } from "@/components/section-card";
import { TradingViewPanel } from "@/components/tradingview-panel";
import { api, wsUrl } from "@/lib/api";
import type { AiDecision, AiExecuteResponse, MarketSnapshot, TechnicalGuardResponse } from "@/lib/types";
import { normalizeError } from "@/lib/utils";

export function AiSignalView() {
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [decision, setDecision] = useState<AiDecision | null>(null);
  const [logLines, setLogLines] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [pendingConfirm, setPendingConfirm] = useState<AiExecuteResponse | null>(null);

  useEffect(() => {
    const socket = new WebSocket(wsUrl("/ws/ai-decisions"));
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data) as { type?: string; payload: Record<string, unknown> };
      if (data.type === "ai_decision") {
        setLogLines((prev) => [`AI decision received: ${String(data.payload.symbol)} / ${String(data.payload.action)}`, ...prev].slice(0, 20));
      }
    };
    return () => socket.close();
  }, []);

  async function analyze() {
    setError(null);
    setLogLines([
      "Fetching market data",
      "Validating source",
      "Calculating indicators",
      "Running Technical Guard",
      "Sending to OpenAI",
      "Awaiting AI decision",
    ]);
    try {
      const result = await api.analyzeAiSignal(symbol);
      setDecision(result);
      setLogLines((prev) => ["AI decision stored in DB", ...prev]);
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  async function execute(preferRealExecution: boolean) {
    if (!decision) return;
    setError(null);
    try {
      const result = await api.executeAiSignal({ decision_id: decision.id, prefer_real_execution: preferRealExecution });
      if (result.confirm_token) {
        setPendingConfirm(result);
      } else {
        setLogLines((prev) => ["Execution completed", ...prev]);
      }
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  async function confirmRealExecution() {
    if (!pendingConfirm?.confirm_token || !decision) return;
    try {
      const result = await api.executeAiSignal({
        decision_id: decision.id,
        prefer_real_execution: true,
        confirm_token: pendingConfirm.confirm_token,
      });
      setPendingConfirm(null);
      setLogLines((prev) => ["Real execution confirmed", ...prev]);
      if (result.decision) setDecision(result.decision);
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  const snapshot = decision?.market_snapshot_json as MarketSnapshot | undefined;
  const guard = decision?.guard_result_json as TechnicalGuardResponse | undefined;

  return (
    <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
      <div className="space-y-6">
        <SectionCard title="AI Signal">
          <div className="flex flex-col gap-3 md:flex-row">
            <input value={symbol} onChange={(event) => setSymbol(event.target.value)} className="flex-1 rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" />
            <button type="button" onClick={analyze} className="rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950">
              Analyze
            </button>
          </div>
          {error ? <div className="mt-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}
        </SectionCard>

        {!decision ? (
          <EmptyState title="هنوز تحلیل AI اجرا نشده است" description="یک نماد وارد کنید و Analyze را بزنید تا OpenAI Responses API واقعاً صدا زده شود." />
        ) : (
          <>
            {snapshot ? (
              <TradingViewPanel
                title="TradingView / AI Signal"
                symbol={decision.symbol}
                exchange={snapshot.source.startsWith("BINANCE") ? "BINANCE" : "TABDEAL"}
                priceLines={[
                  { label: "Entry", value: decision.entry_price, tone: "entry" },
                  { label: "Breakout", value: decision.breakout_price, tone: "resistance" },
                  { label: "Pullback", value: decision.pullback_price, tone: "support" },
                  { label: "Support 20", value: snapshot.support_20, tone: "support" },
                  { label: "Resistance 20", value: snapshot.resistance_20, tone: "resistance" },
                ]}
                aiDecision={`${decision.action} / confidence ${decision.confidence}`}
                guardSummary={guard ? `${guard.allowed ? "ALLOWED" : "BLOCKED"} / RR ${guard.risk_reward}` : null}
              />
            ) : null}

            <SectionCard title="AI Decision">
              <div className="grid gap-3 md:grid-cols-2">
                {[
                  ["Action", decision.action],
                  ["Confidence", String(decision.confidence)],
                  ["Entry Price", decision.entry_price || "-"],
                  ["Breakout Price", decision.breakout_price || "-"],
                  ["Pullback Price", decision.pullback_price || "-"],
                  ["TP / SL %", `${decision.take_profit_pct} / ${decision.stop_loss_pct}`],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                    <div className="text-xs text-slate-400">{label}</div>
                    <div className="mt-2 text-sm text-white">{value}</div>
                  </div>
                ))}
              </div>
              <div className="mt-4 rounded-2xl border border-white/8 bg-white/[0.03] p-4 text-sm text-slate-200">
                <div className="font-medium text-white">Reason</div>
                <div className="mt-2 leading-7">{decision.reason}</div>
                <div className="mt-4 font-medium text-white">Entry Note</div>
                <div className="mt-2 leading-7">{decision.entry_note}</div>
                <div className="mt-4 font-medium text-white">Risk Warning</div>
                <div className="mt-2 leading-7">{decision.risk_warning}</div>
              </div>
              <div className="mt-5 flex flex-wrap gap-3">
                <button type="button" onClick={() => execute(false)} className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-200">
                  Create Dry-Run Trade
                </button>
                <button type="button" onClick={() => execute(true)} className="rounded-2xl border border-yellow-400/20 bg-yellow-400/10 px-4 py-3 text-sm text-yellow-100">
                  Execute Real Trade
                </button>
              </div>
            </SectionCard>

            <SectionCard title="Market Snapshot / Guard">
              <div className="grid gap-3 md:grid-cols-2">
                {snapshot ? Object.entries(snapshot).slice(0, 12).map(([key, value]) => (
                  <div key={key} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm">
                    <div className="text-xs text-slate-400">{key}</div>
                    <div className="mt-2 text-white">{String(value)}</div>
                  </div>
                )) : null}
              </div>
              {guard ? (
                <div className="mt-4 rounded-2xl border border-white/8 bg-white/[0.03] p-4 text-sm text-slate-200">
                  <div>Guard Allowed: {String(guard.allowed)}</div>
                  <div className="mt-2">Entry Type: {guard.entry_type}</div>
                  <div className="mt-2">Risk/Reward: {guard.risk_reward}</div>
                  <div className="mt-3 space-y-2">
                    {guard.reasons.map((reason) => (
                      <div key={reason} className="rounded-2xl border border-yellow-400/20 bg-yellow-400/10 px-4 py-3 text-yellow-100">{reason}</div>
                    ))}
                  </div>
                </div>
              ) : null}
            </SectionCard>
          </>
        )}
      </div>

      <SectionCard title="AI Thinking / Decision Log">
        <div className="space-y-3">
          {logLines.length === 0 ? (
            <EmptyState title="لاگ تصمیم هنوز خالی است" description="بعد از تحلیل AI، مراحل تصمیم‌گیری اینجا نمایش داده می‌شود." />
          ) : (
            logLines.map((line, index) => (
              <div key={`${line}-${index}`} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-slate-200">
                {line}
              </div>
            ))
          )}
        </div>
        {pendingConfirm ? (
          <div className="mt-6 rounded-[24px] border border-yellow-400/20 bg-yellow-400/10 p-5">
            <div className="text-sm text-yellow-100">سفارش AI در حالت REAL نیاز به تأیید دوم backend دارد.</div>
            <button type="button" onClick={confirmRealExecution} className="mt-4 rounded-2xl bg-yellow-400 px-4 py-3 text-sm font-semibold text-slate-950">
              Confirm Real Execution
            </button>
          </div>
        ) : null}
      </SectionCard>
    </div>
  );
}
