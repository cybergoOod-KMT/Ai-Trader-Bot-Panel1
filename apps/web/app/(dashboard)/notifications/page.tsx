"use client";

import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { NotificationsView } from "@/components/notifications-view";
import { TopBar } from "@/components/top-bar";

export default function NotificationsPage() {
  return (
    <AuthGuard>
      {(user) => (
        <AppShell username={user.username}>
          <TopBar title="اعلان‌ها" />
          <NotificationsView />
        </AppShell>
      )}
    </AuthGuard>
  );
}
