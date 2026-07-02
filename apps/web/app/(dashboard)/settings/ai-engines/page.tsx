"use client";

import { AdminSettingsView } from "@/components/admin-settings-view";
import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { TopBar } from "@/components/top-bar";
import { api } from "@/lib/api";

export default function AiEnginesSettingsPage() {
  return (
    <AuthGuard>
      {(user) => (
        <AppShell username={user.username}>
          <TopBar title="AI Engines" subtitle="مدیریت engine پیش‌فرض و تنظیمات OpenAI/Ollama بدون افشای secretها" />
          <AdminSettingsView
            title="AI Engine Settings JSON"
            description="Ollama فقط وقتی enabled=true باشد و backend بتواند HTTP واقعی بگیرد، فعال می‌شود."
            load={api.getAiEngineSettings}
            save={api.updateAiEngineSettings}
          />
        </AppShell>
      )}
    </AuthGuard>
  );
}
