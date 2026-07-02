"use client";

import { useEffect, useState } from "react";
import { MoonStar, Search, TimerReset } from "lucide-react";

import { NotificationBell } from "@/components/notification-bell";
import { api } from "@/lib/api";
import type { DashboardResponse } from "@/lib/types";

export function TopBar({ title, subtitle }: { title: string; subtitle?: string }) {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const time = new Intl.DateTimeFormat("fa-IR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date());

  useEffect(() => {
    api.getDashboard().then(setDashboard).catch(() => undefined);
  }, []);

  return (
    <div className="glass-panel mb-6 flex flex-col gap-4 rounded-[28px] px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <div className="text-2xl font-semibold text-white">{title}</div>
        <div className="mt-1 text-sm text-slate-400">
          {subtitle || "Phase 5 Production Hardening با plugin layer، audit trail، emergency controls و observability واقعی"}
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-3 text-sm text-slate-300">
        <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-2">
          <div className="text-[11px] text-slate-500">حساب فعال</div>
          <div className="mt-1 text-sm text-white">{dashboard?.active_api_account?.name || "تنظیم نشده"}</div>
        </div>
        <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-2">
          <div className="text-[11px] text-slate-500">حالت اجرا</div>
          <div className={`mt-1 text-sm ${dashboard?.dry_run_default ? "text-emerald-300" : "text-yellow-300"}`}>
            {dashboard?.dry_run_default ? "DRY_RUN" : "REAL"}
          </div>
        </div>
        <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-2">
          <div className="text-[11px] text-slate-500">فاز</div>
          <div className="mt-1 text-sm text-cyan-200">{dashboard?.phase || "phase_5_production"}</div>
        </div>
        <div className="flex items-center gap-2 rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-2">
          <TimerReset className="h-4 w-4 text-cyan-300" />
          <span>ساعت سرور: {time}</span>
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/8 bg-white/[0.03]">
          <Search className="h-4 w-4" />
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/8 bg-white/[0.03]">
          <MoonStar className="h-4 w-4" />
        </div>
        <NotificationBell />
      </div>
    </div>
  );
}
