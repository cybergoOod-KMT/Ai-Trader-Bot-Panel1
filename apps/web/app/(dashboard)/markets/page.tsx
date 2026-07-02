"use client";

import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { MarketsView } from "@/components/markets-view";
import { TopBar } from "@/components/top-bar";

export default function MarketsPage() {
  return (
    <AuthGuard>
      {(user) => (
        <AppShell username={user.username}>
          <TopBar title="بازارها" />
          <MarketsView />
        </AppShell>
      )}
    </AuthGuard>
  );
}
