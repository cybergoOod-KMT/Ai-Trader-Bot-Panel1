"use client";

import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { EmergencyView } from "@/components/emergency-view";
import { TopBar } from "@/components/top-bar";

export default function EmergencySettingsPage() {
  return (
    <AuthGuard>
      {(user) => (
        <AppShell username={user.username}>
          <TopBar title="Emergency" subtitle="کنترل‌های اضطراری، backup/restore و snapshotهای ریسک برای فاز Production" />
          <EmergencyView />
        </AppShell>
      )}
    </AuthGuard>
  );
}
