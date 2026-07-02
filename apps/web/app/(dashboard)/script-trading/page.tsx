"use client";

import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { ScriptTradingView } from "@/components/script-trading-view";
import { TopBar } from "@/components/top-bar";

export default function ScriptTradingPage() {
  return (
    <AuthGuard>
      {(user) => (
        <AppShell username={user.username}>
          <TopBar title="اسکریپت ترید" />
          <ScriptTradingView />
        </AppShell>
      )}
    </AuthGuard>
  );
}
