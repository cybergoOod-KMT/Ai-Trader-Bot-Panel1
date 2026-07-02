"use client";

import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { ManualTradingView } from "@/components/manual-trading-view";
import { TopBar } from "@/components/top-bar";

export default function ManualTradingPage() {
  return (
    <AuthGuard>
      {(user) => (
        <AppShell username={user.username}>
          <TopBar title="معامله دستی" />
          <ManualTradingView />
        </AppShell>
      )}
    </AuthGuard>
  );
}
