"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { SectionCard } from "@/components/section-card";
import { api } from "@/lib/api";
import type { AuditLogItem } from "@/lib/types";
import { formatDateTime, normalizeError } from "@/lib/utils";

export function AuditLogsView() {
  const [rows, setRows] = useState<AuditLogItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listAuditLogs().then(setRows).catch((err) => setError(normalizeError(err)));
  }, []);

  return (
    <SectionCard title="Audit Logs">
      <p className="mb-4 text-sm leading-7 text-slate-400">همه عملیات حساس ادمین، سفارش واقعی، emergency و تغییرات تنظیمات در این بخش ثبت می‌شوند.</p>
      {error ? <div className="mb-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}
      {rows.length === 0 ? (
        <EmptyState title="هنوز Audit Log ثبت نشده است" description="به محض انجام عملیات حساس، این صفحه از دیتابیس واقعی پر می‌شود." />
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-right text-sm">
            <thead className="text-slate-400">
              <tr className="border-b border-white/8">
                <th className="px-3 py-3">زمان</th>
                <th className="px-3 py-3">اکشن</th>
                <th className="px-3 py-3">نوع</th>
                <th className="px-3 py-3">شناسه</th>
                <th className="px-3 py-3">کاربر</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-b border-white/6 text-slate-200">
                  <td className="px-3 py-3">{formatDateTime(row.created_at)}</td>
                  <td className="px-3 py-3">{row.action}</td>
                  <td className="px-3 py-3">{row.entity_type}</td>
                  <td className="px-3 py-3">{row.entity_id || "-"}</td>
                  <td className="px-3 py-3">{row.actor_user_id || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SectionCard>
  );
}
