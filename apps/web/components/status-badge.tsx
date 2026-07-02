import { cn } from "@/lib/utils";

export function StatusBadge({ value }: { value: string }) {
  const tone =
    value === "configured" || value === "active" || value === "success"
      ? "bg-emerald-400/10 text-emerald-300 border-emerald-400/20"
      : value === "missing_credentials" || value === "warning"
        ? "bg-yellow-400/10 text-yellow-200 border-yellow-400/20"
        : "bg-slate-400/10 text-slate-300 border-slate-500/20";

  return <span className={cn("rounded-full border px-3 py-1 text-xs font-medium", tone)}>{value}</span>;
}
