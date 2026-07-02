"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { SectionCard } from "@/components/section-card";
import { api, wsUrl } from "@/lib/api";
import type { NotificationItem } from "@/lib/types";
import { formatDateTime, normalizeError } from "@/lib/utils";

export function NotificationsView() {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<number | null>(null);
  const [type, setType] = useState("");
  const [severity, setSeverity] = useState("");

  async function loadItems() {
    const result = await api.listNotifications({ type: type || undefined, severity: severity || undefined });
    setItems(result);
  }

  useEffect(() => {
    loadItems().catch((err) => setError(normalizeError(err)));
  }, [type, severity]);

  useEffect(() => {
    const socket = new WebSocket(wsUrl("/ws/notifications"));
    socket.onmessage = () => {
      loadItems().catch(() => undefined);
    };
    return () => socket.close();
  }, [type, severity]);

  async function markAsRead(id: number) {
    setBusy(id);
    setError(null);
    try {
      await api.markNotificationRead(id);
      await loadItems();
    } catch (err) {
      setError(normalizeError(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <SectionCard title="مرکز اعلان‌ها">
      {error ? <div className="mb-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}
      <div className="mb-5 grid gap-3 md:grid-cols-[1fr_180px_180px_auto]">
        <input value={type} onChange={(event) => setType(event.target.value)} placeholder="فیلتر نوع مثل AI یا SCRIPT" className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none" />
        <select value={severity} onChange={(event) => setSeverity(event.target.value)} className="rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none">
          <option value="">همه severityها</option>
          <option value="INFO">INFO</option>
          <option value="SUCCESS">SUCCESS</option>
          <option value="WARNING">WARNING</option>
          <option value="ERROR">ERROR</option>
        </select>
        <button type="button" onClick={() => loadItems()} className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-slate-200">
          بازخوانی
        </button>
        <button
          type="button"
          onClick={async () => {
            await api.markAllNotificationsRead();
            await loadItems();
          }}
          className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-200"
        >
          خواندن همه
        </button>
      </div>
      {items.length === 0 ? (
        <EmptyState title="اعلانی وجود ندارد" description="وقتی هشدارها، تست‌ها یا رویدادهای عملیاتی ثبت شوند، این بخش به‌صورت واقعی پر می‌شود." />
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.id} className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded-full px-2 py-1 text-[11px] ${
                        item.is_read ? "bg-slate-500/10 text-slate-300" : "bg-emerald-400/10 text-emerald-300"
                      }`}
                    >
                      {item.is_read ? "خوانده‌شده" : "خوانده‌نشده"}
                    </span>
                    <span className="text-xs text-slate-500">{item.type}</span>
                    <span className="text-xs text-slate-500">{item.severity}</span>
                  </div>
                  <div className="mt-3 text-base font-semibold text-white">{item.title}</div>
                  <div className="mt-2 text-sm leading-7 text-slate-300">{item.message}</div>
                </div>
                {!item.is_read ? (
                  <button
                    type="button"
                    disabled={busy === item.id}
                    onClick={() => markAsRead(item.id)}
                    className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-2 text-sm text-cyan-200 disabled:opacity-60"
                  >
                    علامت‌گذاری به‌عنوان خوانده‌شده
                  </button>
                ) : null}
              </div>
              <div className="mt-3 text-xs text-slate-500">{formatDateTime(item.created_at)}</div>
            </div>
          ))}
        </div>
      )}
    </SectionCard>
  );
}
