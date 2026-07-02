"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Bell,
  Bot,
  ChartCandlestick,
  CircleHelp,
  FileClock,
  Gauge,
  Layers3,
  ListOrdered,
  LogOut,
  PackageSearch,
  PencilRuler,
  ScrollText,
  Settings2,
  Sparkles,
  SquareTerminal,
  WalletCards,
} from "lucide-react";

import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const mainItems = [
  { href: "/dashboard", label: "داشبورد", icon: Gauge },
  { href: "/manual-trading", label: "معامله دستی", icon: SquareTerminal },
  { href: "/ai-signal", label: "سیگنال AI", icon: Sparkles },
  { href: "/ai-bot", label: "ربات AI", icon: Bot },
  { href: "/strategy-bots", label: "ربات استراتژی", icon: ListOrdered },
  { href: "/markets", label: "بازارها", icon: PackageSearch },
  { href: "/orders", label: "سفارش‌ها", icon: ChartCandlestick },
  { href: "/positions", label: "پوزیشن‌ها", icon: Layers3 },
  { href: "/script-trading", label: "اسکریپت ترید", icon: PencilRuler },
  { href: "/backtests", label: "بک‌تست", icon: ChartCandlestick },
  { href: "/reports", label: "گزارش‌ها", icon: ScrollText },
  { href: "/settings/api", label: "تنظیمات API", icon: WalletCards },
  { href: "/settings/risk", label: "تنظیمات ریسک", icon: Settings2 },
  { href: "/settings/ai-engines", label: "AI Engines", icon: Sparkles },
  { href: "/settings/strategies", label: "استراتژی‌ها", icon: ListOrdered },
  { href: "/settings/emergency", label: "Emergency", icon: CircleHelp },
  { href: "/logs", label: "لاگ سیستم", icon: FileClock },
  { href: "/notifications", label: "اعلان‌ها", icon: Bell },
  { href: "/audit-logs", label: "Audit Logs", icon: ScrollText },
  { href: "/learning-memory", label: "Learning Memory", icon: Layers3 },
];

export function AppShell({ username, children }: { username: string; children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  async function handleLogout() {
    await api.logout();
    router.push("/login");
    router.refresh();
  }

  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[300px_1fr]">
      <aside className="border-l border-white/8 bg-[#081220]/90 p-4 backdrop-blur-xl">
        <div className="glass-panel rounded-[28px] p-5">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-linear-to-br from-cyan-400/30 to-violet-500/30 text-cyan-200">
              <Bot className="h-6 w-6" />
            </div>
            <div>
              <div className="text-lg font-semibold">Tabdeal AI Panel</div>
              <div className="text-xs text-slate-400">Production Control Surface</div>
            </div>
          </div>

          <nav className="space-y-2">
            {mainItems.map((item) => {
              const Icon = item.icon;
              const active = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center justify-between rounded-2xl px-4 py-3 text-sm transition",
                    active
                      ? "bg-violet-500/20 text-white shadow-[0_0_0_1px_rgba(174,107,255,0.28)]"
                      : "text-slate-300 hover:bg-white/5 hover:text-white"
                  )}
                >
                  <span>{item.label}</span>
                  <Icon className="h-4 w-4" />
                </Link>
              );
            })}
          </nav>

          <div className="mt-8 rounded-3xl border border-emerald-400/10 bg-emerald-400/6 p-4">
            <div className="text-xs text-slate-400">حساب ادمین</div>
            <div className="mt-2 flex items-center justify-between">
              <div>
                <div className="font-medium text-white">{username}</div>
                <div className="text-xs text-slate-400">Administrator</div>
              </div>
              <button type="button" onClick={handleLogout} className="rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-200 transition hover:bg-white/8">
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="mt-4 flex items-center justify-between rounded-3xl border border-white/6 bg-white/[0.03] p-4 text-sm text-slate-300">
            <div className="flex items-center gap-2">
              <CircleHelp className="h-4 w-4 text-cyan-300" />
              <span>راهنما</span>
            </div>
            <Settings2 className="h-4 w-4 text-slate-500" />
          </div>
        </div>
      </aside>

      <main className="grid-sheen min-w-0 p-4 lg:p-6">{children}</main>
    </div>
  );
}
