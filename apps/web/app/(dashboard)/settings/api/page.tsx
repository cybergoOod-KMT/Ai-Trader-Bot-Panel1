"use client";

import { AppShell } from "@/components/app-shell";
import { ApiSettingsView } from "@/components/api-settings-view";
import { AuthGuard } from "@/components/auth-guard";
import { TopBar } from "@/components/top-bar";

export default function ApiSettingsPage() {
  return (
    <AuthGuard>
      {(user) => (
        <AppShell username={user.username}>
          <TopBar title="تنظیمات API" />
          <ApiSettingsView />
        </AppShell>
      )}
    </AuthGuard>
  );
}
