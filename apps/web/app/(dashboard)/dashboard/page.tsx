"use client";

import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { DashboardView } from "@/components/dashboard-view";
import { TopBar } from "@/components/top-bar";

export default function DashboardPage() {
  return (
    <AuthGuard>
      {(user) => (
        <AppShell username={user.username}>
          <TopBar title="داشبورد" />
          <DashboardView />
        </AppShell>
      )}
    </AuthGuard>
  );
}
