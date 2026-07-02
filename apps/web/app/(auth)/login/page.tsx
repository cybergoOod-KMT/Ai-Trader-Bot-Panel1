"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LockKeyhole, User2 } from "lucide-react";

import { api } from "@/lib/api";
import { normalizeError } from "@/lib/utils";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const user = await api.login(username, password);
      router.push(user.force_password_change ? "/force-change-password" : "/dashboard");
      router.refresh();
    } catch (err) {
      setError(normalizeError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center px-4 py-10">
      <div className="glass-panel w-full max-w-md rounded-[32px] p-8">
        <div className="mb-8 text-center">
          <div className="text-3xl font-semibold text-white">ورود به پنل Tabdeal AI</div>
          <div className="mt-3 text-sm leading-7 text-slate-400">
            این صفحه به احراز هویت واقعی FastAPI متصل است و بدون نشست معتبر دسترسی به داشبورد ممکن نیست.
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block">
            <span className="mb-2 block text-sm text-slate-300">نام کاربری</span>
            <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-[#091426] px-4 py-3">
              <User2 className="h-4 w-4 text-slate-500" />
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="w-full bg-transparent text-white outline-none"
                autoComplete="username"
              />
            </div>
          </label>

          <label className="block">
            <span className="mb-2 block text-sm text-slate-300">رمز عبور</span>
            <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-[#091426] px-4 py-3">
              <LockKeyhole className="h-4 w-4 text-slate-500" />
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full bg-transparent text-white outline-none"
                autoComplete="current-password"
              />
            </div>
          </label>

          {error ? <div className="rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:opacity-60"
          >
            {loading ? "در حال ورود..." : "ورود"}
          </button>
        </form>
      </div>
    </main>
  );
}
