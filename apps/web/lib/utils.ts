export function cn(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function formatDateTime(value: string) {
  try {
    return new Intl.DateTimeFormat("fa-IR", {
      dateStyle: "short",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export function normalizeError(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "خطای غیرمنتظره‌ای رخ داد.";
}
