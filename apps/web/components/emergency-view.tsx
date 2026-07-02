"use client";

import { useEffect, useState } from "react";

import { SectionCard } from "@/components/section-card";
import { api } from "@/lib/api";
import type { BackupItem, GenericSettingsResponse } from "@/lib/types";
import { formatDateTime, normalizeError } from "@/lib/utils";

export function EmergencyView() {
  const [riskSettings, setRiskSettings] = useState<GenericSettingsResponse | null>(null);
  const [backups, setBackups] = useState<BackupItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [realConfirmToken, setRealConfirmToken] = useState("");

  async function refresh() {
    const [risk, backupRows] = await Promise.all([api.getRiskSettings(), api.listBackups()]);
    setRiskSettings(risk);
    setBackups(backupRows);
  }

  useEffect(() => {
    refresh().catch((err) => setError(normalizeError(err)));
  }, []);

  async function runAction(action: () => Promise<unknown>, message: string) {
    setError(null);
    setSuccess(null);
    try {
      await action();
      await refresh();
      setSuccess(message);
    } catch (err) {
      setError(normalizeError(err));
    }
  }

  return (
    <div className="space-y-6">
      {error ? <div className="rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}
      {success ? <div className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-200">{success}</div> : null}

      <SectionCard title="Emergency Controls">
        <p className="mb-4 text-sm leading-7 text-slate-400">کنترل‌های اضطراری Phase 5 مستقیماً backend را تغییر می‌دهند و همه آن‌ها audit می‌شوند.</p>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <button type="button" onClick={() => runAction(api.emergencyStopAllBots, "همه بات‌ها متوقف شدند.")} className="rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-200">
            Stop All Bots
          </button>
          <button type="button" onClick={() => runAction(api.emergencyPauseTrading, "سفارش‌های جدید متوقف شدند.")} className="rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-200">
            Pause Trading
          </button>
          <button type="button" onClick={() => runAction(api.emergencyResumeTrading, "معاملات دوباره فعال شد.")} className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-200">
            Resume Trading
          </button>
          <button type="button" onClick={() => runAction(api.emergencyDisableRealTrading, "REAL trading قفل شد.")} className="rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">
            Disable Real Trading
          </button>
          <button type="button" onClick={() => runAction(api.emergencyCloseAllDryRun, "همه پوزیشن‌های dry-run بسته شدند.")} className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-200">
            Close All Dry-run
          </button>
          <button
            type="button"
            onClick={async () => {
              try {
                setError(null);
                const result = await api.emergencyCloseAllRealPreview();
                setRealConfirmToken(result.confirm_token);
                setSuccess("توکن تأیید close-all-real تولید شد.");
              } catch (err) {
                setError(normalizeError(err));
              }
            }}
            className="rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-200"
          >
            Close All Real Preview
          </button>
        </div>

        <div className="mt-4 rounded-[24px] border border-white/8 bg-white/[0.03] p-4">
          <div className="text-sm text-slate-300">Confirm token برای close-all-real</div>
          <input value={realConfirmToken} onChange={(event) => setRealConfirmToken(event.target.value)} dir="ltr" className="mt-3 w-full rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-slate-100 outline-none" />
          <button type="button" onClick={() => runAction(() => api.emergencyCloseAllRealConfirm(realConfirmToken), "درخواست بستن همه پوزیشن‌های واقعی ارسال شد.")} className="mt-3 rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">
            Confirm Close All Real
          </button>
        </div>
      </SectionCard>

      <SectionCard title="Risk Snapshot">
        <p className="mb-4 text-sm leading-7 text-slate-400">تصویر فعلی از risk settings پایدار که backend از آن برای block کردن execution استفاده می‌کند.</p>
        <pre className="overflow-x-auto whitespace-pre-wrap rounded-[24px] bg-[#091426] p-4 text-xs text-slate-200">{JSON.stringify(riskSettings?.value || {}, null, 2)}</pre>
      </SectionCard>

      <SectionCard title="Backups">
        <p className="mb-4 text-sm leading-7 text-slate-400">Backupهای SQLite و config امن‌شده. دانلود و restore از همین صفحه قابل انجام است.</p>
        <div className="mb-4 flex flex-wrap gap-3">
          <button type="button" onClick={() => runAction(api.createBackup, "Backup جدید ساخته شد.")} className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-200">
            Create Backup
          </button>
        </div>
        <div className="space-y-3">
          {backups.map((item) => (
            <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 rounded-[24px] border border-white/8 bg-white/[0.03] p-4">
              <div>
                <div className="font-medium text-white">{item.id}</div>
                <div className="mt-1 text-xs text-slate-500">{formatDateTime(item.created_at)}</div>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={async () => {
                    const blob = await api.downloadBackup(item.id);
                    const url = URL.createObjectURL(blob);
                    const anchor = document.createElement("a");
                    anchor.href = url;
                    anchor.download = `${item.id}.json`;
                    anchor.click();
                    URL.revokeObjectURL(url);
                  }}
                  className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-slate-200"
                >
                  Download
                </button>
                <button type="button" onClick={() => runAction(() => api.restoreBackup(item.id), `Backup ${item.id} restore شد.`)} className="rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-2 text-sm text-amber-200">
                  Restore
                </button>
              </div>
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
