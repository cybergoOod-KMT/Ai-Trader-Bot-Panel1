"use client";

import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { PositionsView } from "@/components/positions-view";
import { TopBar } from "@/components/top-bar";

export default function PositionsPage() {
  return (
    <AuthGuard>
      {(user) => (
        <AppShell username={user.username}>
          <TopBar title="پوزیشن‌ها" />
          <PositionsView />
        </AppShell>
      )}
    </AuthGuard>
  );
}
