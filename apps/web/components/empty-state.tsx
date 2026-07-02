import { ShieldAlert } from "lucide-react";

export function EmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="flex min-h-52 flex-col items-center justify-center rounded-[28px] border border-dashed border-white/10 bg-white/[0.02] px-6 py-10 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-400/10 text-cyan-300">
        <ShieldAlert className="h-7 w-7" />
      </div>
      <div className="text-lg font-semibold text-white">{title}</div>
      <div className="mt-2 max-w-xl text-sm leading-7 text-slate-400">{description}</div>
    </div>
  );
}
