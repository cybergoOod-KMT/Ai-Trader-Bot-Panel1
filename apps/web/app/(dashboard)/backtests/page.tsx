"use client";

import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { BacktestsView } from "@/components/backtests-view";
import { TopBar } from "@/components/top-bar";

export default function BacktestsPage() {
  return (
    <AuthGuard>
      {(user) => (
        <AppShell username={user.username}>
          <TopBar title="بک‌تست" />
          <BacktestsView />
        </AppShell>
      )}
    </AuthGuard>
  );
}
