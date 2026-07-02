"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { AuthGuard } from "@/components/auth-guard";
import { normalizeError } from "@/lib/utils";
import { api } from "@/lib/api";

function ForceChangePasswordContent() {
  const router = useRouter();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      await api.changePassword(currentPassword, newPassword);
      setMessage("رمز عبور با موفقیت تغییر کرد.");
      setTimeout(() => {
        router.push("/dashboard");
        router.refresh();
      }, 900);
    } catch (err) {
      setError(normalizeError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center px-4 py-10">
      <div className="glass-panel w-full max-w-lg rounded-[32px] p-8">
        <div className="text-2xl font-semibold text-white">تغییر اجباری رمز عبور</div>
        <div className="mt-3 text-sm leading-7 text-slate-400">
          تا زمانی که رمز پیش‌فرض تغییر نکند، ورود به داشبورد اصلی مسدود می‌ماند.
        </div>
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <input
            type="password"
            placeholder="رمز فعلی"
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
            className="w-full rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none focus:border-cyan-300/50"
          />
          <input
            type="password"
            placeholder="رمز جدید"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            className="w-full rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none focus:border-cyan-300/50"
          />
          {message ? <div className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-200">{message}</div> : null}
          {error ? <div className="rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:opacity-60"
          >
            {loading ? "در حال ثبت..." : "ثبت رمز جدید"}
          </button>
        </form>
      </div>
    </main>
  );
}

export default function ForceChangePasswordPage() {
  return <AuthGuard>{() => <ForceChangePasswordContent />}</AuthGuard>;
}
