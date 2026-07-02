"use client";

type Point = { label: string; value: number };

export function SimpleLineChart({ points, stroke = "#22d3ee" }: { points: Point[]; stroke?: string }) {
  if (!points.length) {
    return <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4 text-sm text-slate-400">هنوز داده‌ای برای نمودار وجود ندارد.</div>;
  }

  const width = 640;
  const height = 220;
  const padding = 18;
  const lastPoint = points[points.length - 1];
  const values = points.map((item) => item.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const coordinates = points.map((point, index) => {
    const x = padding + (index / Math.max(points.length - 1, 1)) * (width - padding * 2);
    const y = height - padding - ((point.value - min) / range) * (height - padding * 2);
    return `${x},${y}`;
  });
  const path = coordinates.join(" ");

  return (
    <div className="rounded-[28px] border border-white/8 bg-[#081220]/70 p-4">
      <svg viewBox={`0 0 ${width} ${height}`} className="h-56 w-full">
        <defs>
          <linearGradient id="line-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={stroke} stopOpacity="0.35" />
            <stop offset="100%" stopColor={stroke} stopOpacity="0" />
          </linearGradient>
        </defs>
        <polyline fill="none" stroke={stroke} strokeWidth="3" points={path} />
        <polygon
          fill="url(#line-fill)"
          points={`${padding},${height - padding} ${path} ${width - padding},${height - padding}`}
        />
      </svg>
      <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
        <span>{points[0]?.label?.slice(11, 16) || "-"}</span>
        <span>min: {min.toFixed(2)}</span>
        <span>max: {max.toFixed(2)}</span>
        <span>{lastPoint?.label?.slice(11, 16) || "-"}</span>
      </div>
    </div>
  );
}
