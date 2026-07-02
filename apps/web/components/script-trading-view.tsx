"use client";

import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { SectionCard } from "@/components/section-card";
import { api, wsUrl } from "@/lib/api";
import type { ScriptFileItem, ScriptLogItem, ScriptRunItem } from "@/lib/types";
import { formatDateTime, normalizeError } from "@/lib/utils";

export function ScriptTradingView() {
  const [scripts, setScripts] = useState<ScriptFileItem[]>([]);
  const [runs, setRuns] = useState<ScriptRunItem[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [logs, setLogs] = useState<ScriptLogItem[]>([]);
  const [stdin, setStdin] = useState("");
  const [error, setError] = useState<string | null>(null);

  const selectedRun = useMemo(() => runs.find((item) => item.id === selectedRunId) || null, [runs, selectedRunId]);

  async function loadAll() {
    const [nextScripts, nextRuns] = await Promise.all([api.listScripts(), api.listScriptRuns()]);
    setScripts(nextScripts);
    setRuns(nextRuns);
    if (!selectedRunId && nextRuns[0]) setSelectedRunId(nextRuns[0].id);
  }

  async function loadLogs(runId: number) {
    const nextLogs = await api.listScriptLogs(runId);
    setLogs(nextLogs);
  }

  useEffect(() => {
    loadAll().catch((err) => setError(normalizeError(err)));
  }, []);

  useEffect(() => {
    if (!selectedRunId) return;
    loadLogs(selectedRunId).catch(() => undefined);
    const socket = new WebSocket(wsUrl(`/ws/scripts/${selectedRunId}`));
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data) as { event: string; payload: ScriptLogItem | ScriptRunItem };
      if (data.event === "script_log") {
        setLogs((prev) => [...prev, data.payload as ScriptLogItem].slice(-500));
      }
      if (data.event === "script_run_finished") {
        loadAll().catch(() => undefined);
      }
    };
    return () => socket.close();
  }, [selectedRunId]);

  return (
    <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <div className="space-y-6">
        <SectionCard title="فایل‌های Python">
          <div className="mb-4 flex gap-3">
            <button type="button" onClick={() => api.refreshScripts().then(setScripts).catch((err) => setError(normalizeError(err)))} className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-200">
              Refresh scripts
            </button>
            <button type="button" onClick={() => loadAll().catch((err) => setError(normalizeError(err)))} className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-slate-200">
              بازخوانی Runها
            </button>
          </div>
          {error ? <div className="mb-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}
          {scripts.length === 0 ? (
            <EmptyState title="فایل Python پیدا نشد" description="فایل‌های واقعی را داخل scripts/trading/ قرار دهید و Refresh scripts را بزنید." />
          ) : (
            <div className="space-y-3">
              {scripts.map((script) => (
                <div key={script.id} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="font-medium text-white">{script.name}</div>
                      <div className="mt-1 text-xs text-slate-500">{script.relative_path}</div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={async () => {
                          await api.updateScript(script.id, !script.enabled);
                          await loadAll();
                        }}
                        className="rounded-xl border border-white/10 px-3 py-2 text-xs text-slate-200"
                      >
                        {script.enabled ? "Disable" : "Enable"}
                      </button>
                      <button
                        type="button"
                        onClick={async () => {
                          const run = await api.startScript(script.id);
                          setSelectedRunId(run.id);
                          await loadAll();
                          await loadLogs(run.id);
                        }}
                        className="rounded-xl border border-emerald-400/20 bg-emerald-400/10 px-3 py-2 text-xs text-emerald-200"
                      >
                        Start
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </SectionCard>

        <SectionCard title="Run History">
          {runs.length === 0 ? (
            <EmptyState title="هنوز Runای ثبت نشده" description="بعد از اجرای اولین اسکریپت، تاریخچه اینجا نمایش داده می‌شود." />
          ) : (
            <div className="space-y-3">
              {runs.map((run) => (
                <button
                  key={run.id}
                  type="button"
                  onClick={() => setSelectedRunId(run.id)}
                  className={`w-full rounded-2xl border px-4 py-3 text-right ${selectedRunId === run.id ? "border-cyan-400/30 bg-cyan-400/10" : "border-white/8 bg-white/[0.03]"}`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-white">run #{run.id}</div>
                    <div className="text-xs text-slate-400">{run.status}</div>
                  </div>
                  <div className="mt-2 text-xs text-slate-500">{formatDateTime(run.started_at)}</div>
                </button>
              ))}
            </div>
          )}
        </SectionCard>
      </div>

      <SectionCard title="Terminal Viewer زنده">
        {!selectedRun ? (
          <EmptyState title="Run انتخاب نشده" description="یک run را از ستون سمت راست انتخاب کنید تا terminal و stdin فعال شود." />
        ) : (
          <>
            <div className="mb-4 flex flex-wrap items-center gap-3">
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-2 text-sm text-white">
                status: {selectedRun.status}
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-2 text-sm text-white">
                pid: {selectedRun.pid || "-"}
              </div>
              <button type="button" onClick={async () => { await api.stopScriptRun(selectedRun.id); await loadAll(); }} className="rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-2 text-sm text-rose-200">Stop</button>
              <button type="button" onClick={async () => { const run = await api.restartScriptRun(selectedRun.id); setSelectedRunId(run.id); await loadAll(); }} className="rounded-2xl border border-yellow-400/20 bg-yellow-400/10 px-4 py-2 text-sm text-yellow-100">Restart</button>
            </div>
            <div className="h-[480px] overflow-auto rounded-[28px] border border-white/8 bg-[#050c16] p-4 font-mono text-xs leading-6 text-slate-200">
              {logs.length === 0 ? "No output yet." : logs.map((log) => <div key={log.id}>[{log.stream}] {log.line}</div>)}
            </div>
            <div className="mt-4 flex gap-3">
              <input value={stdin} onChange={(event) => setStdin(event.target.value)} placeholder="ارسال stdin" className="flex-1 rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" />
              <button
                type="button"
                onClick={async () => {
                  if (!stdin.trim()) return;
                  await api.sendScriptStdin(selectedRun.id, stdin);
                  setStdin("");
                }}
                className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-200"
              >
                Send
              </button>
            </div>
          </>
        )}
      </SectionCard>
    </div>
  );
}
