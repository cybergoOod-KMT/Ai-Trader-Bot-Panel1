"use client";

import { useEffect, useState } from "react";

import { SectionCard } from "@/components/section-card";
import { normalizeError } from "@/lib/utils";

export function AdminSettingsView({
  title,
  description,
  load,
  save,
}: {
  title: string;
  description: string;
  load: () => Promise<{ key: string; value: Record<string, unknown> }>;
  save: (value: Record<string, unknown>) => Promise<{ key: string; value: Record<string, unknown> }>;
}) {
  const [value, setValue] = useState("{}");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const result = await load();
      setValue(JSON.stringify(result.value, null, 2));
    } catch (err) {
      setError(normalizeError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh().catch(() => undefined);
  }, []);

  async function handleSave() {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const parsed = JSON.parse(value) as Record<string, unknown>;
      const result = await save(parsed);
      setValue(JSON.stringify(result.value, null, 2));
      setSuccess("تنظیمات با موفقیت ذخیره شد.");
    } catch (err) {
      setError(normalizeError(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <SectionCard title={title}>
      <p className="mb-4 text-sm leading-7 text-slate-400">{description}</p>
      {error ? <div className="mb-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div> : null}
      {success ? <div className="mb-4 rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-200">{success}</div> : null}
      <textarea
        value={value}
        onChange={(event) => setValue(event.target.value)}
        dir="ltr"
        spellCheck={false}
        className="min-h-[420px] w-full rounded-[24px] border border-white/10 bg-[#091426] p-4 font-mono text-sm text-slate-100 outline-none"
      />
      <div className="mt-4 flex flex-wrap gap-3">
        <button type="button" onClick={() => refresh()} disabled={loading} className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-slate-200 disabled:opacity-60">
          بازخوانی
        </button>
        <button type="button" onClick={handleSave} disabled={saving || loading} className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-200 disabled:opacity-60">
          ذخیره
        </button>
      </div>
    </SectionCard>
  );
}
