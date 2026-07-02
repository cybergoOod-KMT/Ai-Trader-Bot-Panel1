"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { SectionCard } from "@/components/section-card";
import { api, wsUrl } from "@/lib/api";
import type { SystemLog } from "@/lib/types";
import { formatDateTime, normalizeError } from "@/lib/utils";

export function LogsView() {
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listLogs()
      .then(setLogs)
      .catch((err) => setError(normalizeError(err)));

    const socket = new WebSocket(wsUrl("/ws/system-logs"));
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data) as { payload: SystemLog; event: string };
      if (data.event === "system_log_created" || data.event === "system_log_snapshot") {
        setLogs((prev) => {
          const next = [data.payload, ...prev.filter((item) => item.id !== data.payload.id)];
          return next.slice(0, 200);
        });
      }
    };
    return () => socket.close();
  }, []);

  return (
    <SectionCard title="لاگ سیستم">
      {error ? <div className="rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}
      {!error && logs.length === 0 ? (
        <EmptyState title="لاگی برای نمایش وجود ندارد" description="بعد از اولین عملیات موفق یا ناموفق، لاگ‌های واقعی اینجا ظاهر می‌شوند." />
      ) : null}
      {logs.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="text-slate-400">
              <tr className="border-b border-white/8">
                <th className="px-3 py-3 text-right font-medium">زمان</th>
                <th className="px-3 py-3 text-right font-medium">سطح</th>
                <th className="px-3 py-3 text-right font-medium">منبع</th>
                <th className="px-3 py-3 text-right font-medium">پیام</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-b border-white/5">
                  <td className="px-3 py-3 text-slate-300">{formatDateTime(log.created_at)}</td>
                  <td className="px-3 py-3 text-slate-200">{log.level}</td>
                  <td className="px-3 py-3 text-slate-400">{log.source}</td>
                  <td className="px-3 py-3 text-white">{log.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </SectionCard>
  );
}
