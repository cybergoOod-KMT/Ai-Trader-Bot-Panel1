"use client";

import { AdminSettingsView } from "@/components/admin-settings-view";
import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { TopBar } from "@/components/top-bar";
import { api } from "@/lib/api";

export default function RiskSettingsPage() {
  return (
    <AuthGuard>
      {(user) => (
        <AppShell username={user.username}>
          <TopBar title="تنظیمات ریسک" subtitle="Risk policy پایدار که همه executionهای manual، AI و bot از آن عبور می‌کنند" />
          <AdminSettingsView
            title="Risk Settings JSON"
            description="مقادیر این بخش مستقیماً روی Risk Manager اثر می‌گذارند."
            load={api.getRiskSettings}
            save={api.updateRiskSettings}
          />
        </AppShell>
      )}
    </AuthGuard>
  );
}
