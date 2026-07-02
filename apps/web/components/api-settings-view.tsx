"use client";

import { useEffect, useMemo, useState } from "react";
import { CheckCheck, LoaderCircle, Plus, RefreshCcw, Trash2 } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { SectionCard } from "@/components/section-card";
import { api } from "@/lib/api";
import type { ApiAccount, ConnectionTestResult } from "@/lib/types";
import { normalizeError } from "@/lib/utils";

const initialForm = {
  name: "",
  tabdeal_api_key: "",
  tabdeal_api_secret: "",
  openai_api_key: "",
  openai_model: "gpt-5",
  is_active: true,
  read_only: true,
  real_trading_allowed: false,
};

export function ApiSettingsView() {
  const [accounts, setAccounts] = useState<ApiAccount[]>([]);
  const [selectedId, setSelectedId] = useState<number | "new">("new");
  const [form, setForm] = useState(initialForm);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null);

  async function loadAccounts(nextSelectedId?: number | "new") {
    const result = await api.listApiAccounts();
    setAccounts(result);
    if (nextSelectedId !== undefined) {
      setSelectedId(nextSelectedId);
      return;
    }
    if (result.length > 0 && selectedId === "new") {
      setSelectedId(result[0].id);
    }
  }

  useEffect(() => {
    loadAccounts().catch((err) => setError(normalizeError(err)));
  }, []);

  const selectedAccount = useMemo(
    () => accounts.find((account) => account.id === selectedId) || null,
    [accounts, selectedId]
  );

  useEffect(() => {
    if (selectedAccount) {
      setForm({
        name: selectedAccount.name,
        tabdeal_api_key: "",
        tabdeal_api_secret: "",
        openai_api_key: "",
        openai_model: selectedAccount.openai_model,
        is_active: selectedAccount.is_active,
        read_only: selectedAccount.read_only,
        real_trading_allowed: selectedAccount.real_trading_allowed,
      });
    } else if (selectedId === "new") {
      setForm(initialForm);
    }
  }, [selectedAccount, selectedId]);

  function buildPayload() {
    const payload: Record<string, unknown> = {
      name: form.name.trim(),
      openai_model: form.openai_model.trim() || "gpt-5",
      is_active: form.is_active,
      read_only: form.read_only,
      real_trading_allowed: form.real_trading_allowed,
    };

    const tabdealApiKey = form.tabdeal_api_key.trim();
    const tabdealApiSecret = form.tabdeal_api_secret.trim();
    const openaiApiKey = form.openai_api_key.trim();

    if (!selectedAccount || tabdealApiKey) {
      payload.tabdeal_api_key = tabdealApiKey || undefined;
    }
    if (!selectedAccount || tabdealApiSecret) {
      payload.tabdeal_api_secret = tabdealApiSecret || undefined;
    }
    if (!selectedAccount || openaiApiKey) {
      payload.openai_api_key = openaiApiKey || undefined;
    }

    return payload;
  }

  async function handleSave() {
    setBusyAction("save");
    setError(null);
    setMessage(null);
    try {
      const payload = buildPayload();
      if (selectedAccount) {
        await api.updateApiAccount(selectedAccount.id, payload);
        await loadAccounts(selectedAccount.id);
        setMessage("حساب API با موفقیت به‌روزرسانی شد.");
      } else {
        const created = await api.createApiAccount(payload);
        await loadAccounts(created.id);
        setMessage("حساب API جدید ذخیره شد.");
      }
      setTestResult(null);
    } catch (err) {
      setError(normalizeError(err));
    } finally {
      setBusyAction(null);
    }
  }

  async function handleDelete() {
    if (!selectedAccount) return;
    setBusyAction("delete");
    setError(null);
    setMessage(null);
    try {
      await api.deleteApiAccount(selectedAccount.id);
      setSelectedId("new");
      setMessage("حساب API حذف شد.");
      await loadAccounts();
    } catch (err) {
      setError(normalizeError(err));
    } finally {
      setBusyAction(null);
    }
  }

  async function runTest(type: "ping" | "account" | "trade" | "openai") {
    if (!selectedAccount) {
      setError("ابتدا یک حساب API ذخیره کنید.");
      return;
    }
    setBusyAction(type);
    setError(null);
    setTestResult(null);
    try {
      const result =
        type === "ping"
          ? await api.testTabdealPing(selectedAccount.id)
          : type === "account"
            ? await api.testTabdealAccount(selectedAccount.id)
            : type === "trade"
              ? await api.testTabdealTradeAuth(selectedAccount.id)
              : await api.testOpenAI(selectedAccount.id);
      setTestResult(result);
      await loadAccounts();
    } catch (err) {
      setError(normalizeError(err));
    } finally {
      setBusyAction(null);
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[320px_1fr]">
      <SectionCard
        title="حساب‌های ذخیره‌شده"
        action={
          <button
            type="button"
            onClick={() => setSelectedId("new")}
            className="inline-flex items-center gap-2 rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-sm text-cyan-200"
          >
            <Plus className="h-4 w-4" />
            حساب جدید
          </button>
        }
      >
        {accounts.length === 0 ? (
          <EmptyState title="حسابی ثبت نشده است" description="برای شروع، یک حساب API واقعی اضافه کنید." />
        ) : (
          <div className="space-y-3">
            {accounts.map((account) => (
              <button
                key={account.id}
                type="button"
                onClick={() => setSelectedId(account.id)}
                className={`w-full rounded-2xl border px-4 py-4 text-right transition ${
                  selectedId === account.id
                    ? "border-violet-400/30 bg-violet-500/12"
                    : "border-white/8 bg-white/[0.03] hover:bg-white/[0.05]"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="font-medium text-white">{account.name}</div>
                  {account.is_active ? (
                    <span className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2 py-1 text-[11px] text-emerald-300">
                      فعال
                    </span>
                  ) : null}
                </div>
                <div className="mt-2 text-xs text-slate-400">{account.openai_model}</div>
              </button>
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard
        title={selectedAccount ? `ویرایش ${selectedAccount.name}` : "افزودن حساب API"}
        action={
          selectedAccount ? (
            <button
              type="button"
              onClick={handleDelete}
              disabled={busyAction === "delete"}
              className="inline-flex items-center gap-2 rounded-2xl border border-rose-400/20 bg-rose-400/10 px-3 py-2 text-sm text-rose-200 disabled:opacity-60"
            >
              <Trash2 className="h-4 w-4" />
              حذف
            </button>
          ) : null
        }
      >
        <div className="grid gap-4 md:grid-cols-2">
          <label className="space-y-2">
            <span className="text-sm text-slate-300">نام حساب</span>
            <input
              value={form.name}
              onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
              className="w-full rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none focus:border-cyan-300/50"
              placeholder="مثلاً Tabdeal Main"
            />
          </label>

          <label className="space-y-2">
            <span className="text-sm text-slate-300">مدل OpenAI</span>
            <input
              value={form.openai_model}
              onChange={(event) => setForm((prev) => ({ ...prev, openai_model: event.target.value }))}
              className="w-full rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none focus:border-cyan-300/50"
              placeholder="gpt-5"
            />
          </label>

          <label className="space-y-2">
            <span className="text-sm text-slate-300">Tabdeal API Key</span>
            <input
              value={form.tabdeal_api_key}
              onChange={(event) => setForm((prev) => ({ ...prev, tabdeal_api_key: event.target.value }))}
              className="w-full rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none focus:border-cyan-300/50"
              placeholder={selectedAccount?.tabdeal_api_key_masked || "کلید را وارد کنید"}
            />
          </label>

          <label className="space-y-2">
            <span className="text-sm text-slate-300">Tabdeal API Secret</span>
            <input
              value={form.tabdeal_api_secret}
              onChange={(event) => setForm((prev) => ({ ...prev, tabdeal_api_secret: event.target.value }))}
              className="w-full rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none focus:border-cyan-300/50"
              placeholder={selectedAccount?.tabdeal_api_secret_masked || "سکرت را وارد کنید"}
            />
          </label>

          <label className="space-y-2 md:col-span-2">
            <span className="text-sm text-slate-300">OpenAI API Key</span>
            <input
              value={form.openai_api_key}
              onChange={(event) => setForm((prev) => ({ ...prev, openai_api_key: event.target.value }))}
              className="w-full rounded-2xl border border-white/10 bg-[#091426] px-4 py-3 text-white outline-none focus:border-cyan-300/50"
              placeholder={selectedAccount?.openai_api_key_masked || "کلید OpenAI را وارد کنید"}
            />
          </label>

          <label className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-4">
            <span className="text-sm text-slate-300">حساب فعال</span>
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(event) => setForm((prev) => ({ ...prev, is_active: event.target.checked }))}
              className="h-4 w-4 accent-cyan-400"
            />
          </label>

          <label className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-4">
            <span className="text-sm text-slate-300">Read only</span>
            <input
              type="checkbox"
              checked={form.read_only}
              onChange={(event) => setForm((prev) => ({ ...prev, read_only: event.target.checked }))}
              className="h-4 w-4 accent-cyan-400"
            />
          </label>

          <label className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-4 md:col-span-2">
            <span className="text-sm text-slate-300">اجازه معامله واقعی برای همین حساب</span>
            <input
              type="checkbox"
              checked={form.real_trading_allowed}
              onChange={(event) => setForm((prev) => ({ ...prev, real_trading_allowed: event.target.checked }))}
              className="h-4 w-4 accent-cyan-400"
            />
          </label>
        </div>

        {message ? <div className="mt-4 rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-200">{message}</div> : null}
        {error ? <div className="mt-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}

        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleSave}
            disabled={busyAction === "save"}
            className="inline-flex items-center gap-2 rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:opacity-60"
          >
            {busyAction === "save" ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <CheckCheck className="h-4 w-4" />}
            ذخیره
          </button>
          <button
            type="button"
            onClick={() => runTest("ping")}
            disabled={!selectedAccount || Boolean(busyAction)}
            className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-slate-200 disabled:opacity-50"
          >
            تست Tabdeal Ping
          </button>
          <button
            type="button"
            onClick={() => runTest("account")}
            disabled={!selectedAccount || Boolean(busyAction)}
            className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-slate-200 disabled:opacity-50"
          >
            تست Tabdeal Account
          </button>
          <button
            type="button"
            onClick={() => runTest("trade")}
            disabled={!selectedAccount || Boolean(busyAction)}
            className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-slate-200 disabled:opacity-50"
          >
            تست Trade Permission
          </button>
          <button
            type="button"
            onClick={() => runTest("openai")}
            disabled={!selectedAccount || Boolean(busyAction)}
            className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-slate-200 disabled:opacity-50"
          >
            تست OpenAI
          </button>
          <button
            type="button"
            onClick={() => loadAccounts()}
            disabled={Boolean(busyAction)}
            className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-slate-200 disabled:opacity-50"
          >
            <RefreshCcw className="h-4 w-4" />
            بازخوانی
          </button>
        </div>

        {testResult ? (
          <div
            className={`mt-5 rounded-2xl border p-4 text-sm ${
              testResult.success
                ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-200"
                : "border-rose-400/20 bg-rose-400/10 text-rose-200"
            }`}
          >
            <div className="font-semibold">{testResult.message}</div>
            {testResult.details ? (
              <pre className="mt-3 overflow-x-auto rounded-xl bg-slate-950/50 p-3 text-xs text-slate-200">
                {JSON.stringify(testResult.details, null, 2)}
              </pre>
            ) : null}
          </div>
        ) : null}
      </SectionCard>
    </div>
  );
}
