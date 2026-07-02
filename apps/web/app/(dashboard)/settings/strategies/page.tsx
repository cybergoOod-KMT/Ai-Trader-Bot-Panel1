"use client";

import { AdminSettingsView } from "@/components/admin-settings-view";
import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { TopBar } from "@/components/top-bar";
import { api } from "@/lib/api";

export default function StrategySettingsPage() {
  return (
    <AuthGuard>
      {(user) => (
        <AppShell username={user.username}>
          <TopBar title="استراتژی‌ها" subtitle="تنظیمات استراتژی پیش‌فرض و Technical Guard در لایه عملیاتی" />
          <AdminSettingsView
            title="Strategy Settings JSON"
            description="این بخش default strategy و سوئیچ‌های مرتبط با strategy execution را نگه می‌دارد."
            load={api.getStrategySettings}
            save={api.updateStrategySettings}
          />
        </AppShell>
      )}
    </AuthGuard>
  );
}
