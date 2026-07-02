"use client";

import { AppShell } from "@/components/app-shell";
import { AuditLogsView } from "@/components/audit-logs-view";
import { AuthGuard } from "@/components/auth-guard";
import { TopBar } from "@/components/top-bar";

export default function AuditLogsPage() {
  return (
    <AuthGuard>
      {(user) => (
        <AppShell username={user.username}>
          <TopBar title="Audit Logs" subtitle="ثبت کامل عملیات حساس ادمین، سفارش‌های واقعی، backup/restore و emergency actions" />
          <AuditLogsView />
        </AppShell>
      )}
    </AuthGuard>
  );
}
