"use client";

import { useEffect, useState } from "react";
import { Bell } from "lucide-react";

import { api, wsUrl } from "@/lib/api";
import type { NotificationItem } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export function NotificationBell() {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [open, setOpen] = useState(false);

  async function load() {
    const result = await api.listNotifications({ limit: 6 });
    setItems(result);
  }

  useEffect(() => {
    load().catch(() => undefined);
    const socket = new WebSocket(wsUrl("/ws/notifications"));
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data) as { event: string; payload: NotificationItem };
      if (data.event === "notification_created") {
        setItems((prev) => [data.payload, ...prev].slice(0, 6));
      }
      if (data.event === "notification_snapshot") {
        setItems((prev) => {
          if (prev.some((item) => item.id === data.payload.id)) return prev;
          return [data.payload, ...prev].slice(0, 6);
        });
      }
    };
    return () => socket.close();
  }, []);

  const unread = items.filter((item) => !item.is_read).length;

  return (
    <div className="relative">
      <button type="button" onClick={() => setOpen((value) => !value)} className="relative flex h-10 w-10 items-center justify-center rounded-2xl border border-white/8 bg-white/[0.03]">
        <Bell className="h-4 w-4 text-slate-200" />
        {unread > 0 ? (
          <span className="absolute -left-2 -top-2 rounded-full bg-rose-500 px-2 py-0.5 text-[10px] font-semibold text-white">
            {unread}
          </span>
        ) : null}
      </button>
      {open ? (
        <div className="absolute left-0 top-12 z-50 w-96 rounded-[28px] border border-white/8 bg-[#081220] p-4 shadow-2xl shadow-black/50">
          <div className="mb-3 flex items-center justify-between">
            <div className="text-sm font-semibold text-white">آخرین اعلان‌ها</div>
            <button
              type="button"
              onClick={async () => {
                await api.markAllNotificationsRead();
                await load();
              }}
              className="text-xs text-cyan-300"
            >
              خواندن همه
            </button>
          </div>
          <div className="space-y-3">
            {items.length === 0 ? <div className="text-sm text-slate-400">اعلان فعالی وجود ندارد.</div> : null}
            {items.map((item) => (
              <div key={item.id} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="text-sm font-medium text-white">{item.title}</div>
                  <span className="text-[10px] text-slate-500">{item.severity}</span>
                </div>
                <div className="mt-2 text-xs leading-6 text-slate-300">{item.message}</div>
                <div className="mt-2 text-[10px] text-slate-500">{formatDateTime(item.created_at)}</div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
