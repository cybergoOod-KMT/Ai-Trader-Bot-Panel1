"use client";

import { useEffect, useState } from "react";
import { Bell, Bot, BrainCircuit, FileClock, KeyRound, PencilRuler, ShieldCheck, Wallet2 } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { SectionCard } from "@/components/section-card";
import { SimpleLineChart } from "@/components/simple-line-chart";
import { StatusBadge } from "@/components/status-badge";
import { api } from "@/lib/api";
import type { DashboardResponse } from "@/lib/types";
import { formatDateTime, normalizeError } from "@/lib/utils";

const metrics = [
  { key: "api_status", label: "وضعیت Tabdeal", icon: Wallet2, accent: "text-cyan-300" },
  { key: "openai_status", label: "وضعیت OpenAI", icon: KeyRound, accent: "text-violet-300" },
  { key: "real_trading", label: "معامله واقعی", icon: ShieldCheck, accent: "text-yellow-300" },
  { key: "notifications", label: "اعلان‌های خوانده‌نشده", icon: Bell, accent: "text-emerald-300" },
  { key: "bots", label: "ربات‌های فعال", icon: Bot, accent: "text-cyan-300" },
  { key: "scripts", label: "اسکریپت‌های فعال", icon: PencilRuler, accent: "text-violet-300" },
] as const;

export function DashboardView() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getDashboard().then(setData).catch((err) => setError(normalizeError(err)));
  }, []);

  if (error) {
    return <div className="rounded-3xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div>;
  }

  if (!data) {
    return <div className="text-sm text-slate-300">در حال دریافت خلاصه‌ی عملیاتی Phase 4...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          let value = "";
          if (metric.key === "real_trading") value = data.real_trading_enabled ? "فعال" : "غیرفعال";
          else if (metric.key === "notifications") value = String(data.unread_notifications_count);
          else if (metric.key === "api_status") value = data.api_status;
          else if (metric.key === "openai_status") value = data.openai_status;
          else if (metric.key === "bots") value = String(data.active_bots.length);
          else value = String(data.active_script_runs.length);
          return (
            <div key={metric.key} className="glass-panel rounded-[28px] p-5">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-sm text-slate-400">{metric.label}</div>
                  <div className="mt-3 text-2xl font-semibold text-white">{value}</div>
                </div>
                <div className={`rounded-2xl bg-white/[0.03] p-3 ${metric.accent}`}>
                  <Icon className="h-5 w-5" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {!data.active_api_account ? (
        <EmptyState title="هنوز API تنظیم نشده است" description="برای فعال شدن موتورهای عملیاتی، ابتدا یک حساب API واقعی و فعال تعریف کنید." />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <SectionCard title="خلاصه حساب و سلامت سیستم">
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                <div className="text-xs text-slate-400">حساب فعال</div>
                <div className="mt-2 text-lg font-semibold text-white">{data.active_api_account.name}</div>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                <div className="text-xs text-slate-400">حالت پیش‌فرض</div>
                <div className="mt-2">
                  <StatusBadge value={data.dry_run_default ? "dry_run" : "live"} />
                </div>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                <div className="text-xs text-slate-400">Today DRY_RUN PnL</div>
                <div className="mt-2 text-lg font-semibold text-white">{data.today_dry_run_pnl}</div>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                <div className="text-xs text-slate-400">Today REAL PnL</div>
                <div className="mt-2 text-lg font-semibold text-white">{data.today_real_pnl}</div>
              </div>
            </div>
            <div className="mt-4 rounded-2xl border border-white/8 bg-white/[0.03] p-4 text-sm text-slate-300">
              <div>Bot Health Running: {String(data.bot_health.running || 0)}</div>
              <div className="mt-2">Bot Health Error: {String(data.bot_health.error || 0)}</div>
              <div className="mt-2">Active Watches: {data.active_watches.length}</div>
              <div className="mt-2">Open Positions: {data.open_positions.length}</div>
              <div className="mt-2">Active Script Runs: {data.active_script_runs.length}</div>
            </div>
          </SectionCard>

          <SectionCard title="نمودار تجمعی PnL">
            <SimpleLineChart points={data.pnl_chart} stroke="#22c55e" />
          </SectionCard>
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <SectionCard title="اسکریپت‌های فعال">
          {data.active_script_runs.length === 0 ? (
            <EmptyState title="اسکریپت فعالی وجود ندارد" description="وقتی یک اسکریپت از بخش Script Trading اجرا شود، اینجا دیده می‌شود." />
          ) : (
            <div className="space-y-3">
              {data.active_script_runs.map((item, index) => (
                <div key={index} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm">
                  <div className="text-white">run #{String(item.id || "-")}</div>
                  <div className="mt-2 text-slate-300">PID: {String(item.pid || "-")} / {String(item.status || "-")}</div>
                </div>
              ))}
            </div>
          )}
        </SectionCard>

        <SectionCard title="آخرین تصمیم‌های AI">
          {data.latest_ai_decisions.length === 0 ? (
            <EmptyState title="تصمیم AI ثبت نشده است" description="بعد از اجرای AI Signal یا AI Bot این بخش پر می‌شود." />
          ) : (
            <div className="space-y-3">
              {data.latest_ai_decisions.map((item, index) => (
                <div key={index} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-white">{String(item.symbol || "-")} / {String(item.action || "-")}</div>
                    <BrainCircuit className="h-4 w-4 text-violet-300" />
                  </div>
                  <div className="mt-2 text-slate-300">confidence: {String(item.confidence || "-")}</div>
                  <div className="text-slate-500">{item.created_at ? formatDateTime(String(item.created_at)) : "-"}</div>
                </div>
              ))}
            </div>
          )}
        </SectionCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <SectionCard title="آخرین اعلان‌ها">
          {data.latest_notifications.length === 0 ? (
            <EmptyState title="اعلان فعالی وجود ندارد" description="اعلان‌های سیستم، اسکریپت، AI و بک‌تست اینجا نمایش داده می‌شوند." />
          ) : (
            <div className="space-y-3">
              {data.latest_notifications.map((item) => (
                <div key={item.id} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-white">{item.title}</div>
                    <span className="text-xs text-slate-500">{item.severity}</span>
                  </div>
                  <div className="mt-2 text-slate-300">{item.message}</div>
                  <div className="mt-2 text-xs text-slate-500">{formatDateTime(item.created_at)}</div>
                </div>
              ))}
            </div>
          )}
        </SectionCard>

        <SectionCard title="آخرین لاگ‌های سیستم">
          {data.latest_system_logs.length === 0 ? (
            <EmptyState title="لاگی ثبت نشده است" description="وقتی عملیات اجرایی انجام شوند، لاگ‌های واقعی اینجا دیده می‌شوند." />
          ) : (
            <div className="space-y-3 text-sm">
              {data.latest_system_logs.map((log) => (
                <div key={log.id} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-white">{log.message}</div>
                    <FileClock className="h-4 w-4 text-cyan-300" />
                  </div>
                  <div className="mt-2 text-slate-400">{log.source} / {log.level}</div>
                  <div className="mt-2 text-xs text-slate-500">{formatDateTime(log.created_at)}</div>
                </div>
              ))}
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}
