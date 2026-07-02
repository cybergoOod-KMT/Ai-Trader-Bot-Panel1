"use client";

import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { OrdersView } from "@/components/orders-view";
import { TopBar } from "@/components/top-bar";

export default function OrdersPage() {
  return (
    <AuthGuard>
      {(user) => (
        <AppShell username={user.username}>
          <TopBar title="سفارش‌ها" />
          <OrdersView />
        </AppShell>
      )}
    </AuthGuard>
  );
}
