"use client";

import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { ReportsView } from "@/components/reports-view";
import { TopBar } from "@/components/top-bar";

export default function ReportsPage() {
  return (
    <AuthGuard>
      {(user) => (
        <AppShell username={user.username}>
          <TopBar title="گزارش‌ها" />
          <ReportsView />
        </AppShell>
      )}
    </AuthGuard>
  );
}
