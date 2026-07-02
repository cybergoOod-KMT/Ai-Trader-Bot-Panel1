"use client";

import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { LearningMemoryView } from "@/components/learning-memory-view";
import { TopBar } from "@/components/top-bar";

export default function LearningMemoryPage() {
  return (
    <AuthGuard>
      {(user) => (
        <AppShell username={user.username}>
          <TopBar title="Learning Memory" subtitle="خلاصه محلی از performance قبلی برای کمک به AI و تصمیم‌های بعدی" />
          <LearningMemoryView />
        </AppShell>
      )}
    </AuthGuard>
  );
}
