import {
  AiDecision,
  AiExecuteResponse,
  ApiAccount,
  AuthStatus,
  BacktestEquityPoint,
  BacktestRun,
  BacktestTrade,
  BotConfig,
  BotDecision,
  BotRun,
  AuditLogItem,
  BackupItem,
  ConnectionTestResult,
  CsvImportResult,
  DashboardResponse,
  GenericSettingsResponse,
  LearningMemoryItem,
  ManualOrder,
  ManualOrderCreateResponse,
  ManualOrderPreviewResponse,
  MarketRules,
  MarketSearchItem,
  MarketSnapshot,
  NotificationItem,
  OrderBook,
  PnlBucket,
  PositionClosePreview,
  PositionItem,
  ReportSummary,
  RiskCheckResponse,
  ScriptFileItem,
  ScriptLogItem,
  ScriptRunItem,
  StrategyDecision,
  SystemLog,
  TechnicalGuardResponse,
  TradeOutcomeItem,
  TradeTick,
  User,
  WatchTask,
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  headers?: Record<string, string>;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method || "GET",
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    body: options.body ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = "درخواست با خطا مواجه شد.";
    try {
      const data = (await response.json()) as { detail?: string };
      if (data.detail) detail = data.detail;
    } catch {
      detail = `${detail} (${response.status})`;
    }
    throw new Error(detail);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

async function requestForm<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    credentials: "include",
    body: formData,
    cache: "no-store",
  });
  if (!response.ok) {
    let detail = "درخواست با خطا مواجه شد.";
    try {
      const data = (await response.json()) as { detail?: string };
      if (data.detail) detail = data.detail;
    } catch {
      detail = `${detail} (${response.status})`;
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

async function requestBlob(path: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("دریافت فایل با خطا مواجه شد.");
  }
  return await response.blob();
}

export function wsUrl(path: string) {
  const url = new URL(API_BASE_URL);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return `${url.toString().replace(/\/$/, "")}${path}`;
}

export const api = {
  login: (username: string, password: string) => request<User>("/auth/login", { method: "POST", body: { username, password } }),
  logout: () => request<{ success: boolean }>("/auth/logout", { method: "POST" }),
  me: () => request<AuthStatus>("/auth/me"),
  changePassword: (current_password: string, new_password: string) =>
    request<User>("/auth/change-password", { method: "POST", body: { current_password, new_password } }),
  getDashboard: () => request<DashboardResponse>("/dashboard"),

  listApiAccounts: () => request<ApiAccount[]>("/api-accounts"),
  createApiAccount: (payload: Record<string, unknown>) => request<ApiAccount>("/api-accounts", { method: "POST", body: payload }),
  updateApiAccount: (id: number, payload: Record<string, unknown>) => request<ApiAccount>(`/api-accounts/${id}`, { method: "PATCH", body: payload }),
  deleteApiAccount: (id: number) => request<{ success: boolean }>(`/api-accounts/${id}`, { method: "DELETE" }),
  testTabdealPing: (id: number) => request<ConnectionTestResult>(`/api-accounts/${id}/test-tabdeal-ping`, { method: "POST" }),
  testTabdealAccount: (id: number) => request<ConnectionTestResult>(`/api-accounts/${id}/test-tabdeal-account`, { method: "POST" }),
  testTabdealTradeAuth: (id: number) => request<ConnectionTestResult>(`/api-accounts/${id}/test-tabdeal-trade-auth`, { method: "POST" }),
  testOpenAI: (id: number) => request<ConnectionTestResult>(`/api-accounts/${id}/test-openai`, { method: "POST" }),

  listLogs: () => request<SystemLog[]>("/system-logs"),
  listNotifications: (params?: { type?: string; severity?: string; is_read?: boolean; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.type) query.set("type", params.type);
    if (params?.severity) query.set("severity", params.severity);
    if (params?.is_read !== undefined) query.set("is_read", String(params.is_read));
    if (params?.limit) query.set("limit", String(params.limit));
    return request<NotificationItem[]>(`/notifications${query.toString() ? `?${query.toString()}` : ""}`);
  },
  markNotificationRead: (id: number) => request<NotificationItem>(`/notifications/${id}/mark-read`, { method: "POST" }),
  markAllNotificationsRead: () => request<{ updated: number }>("/notifications/mark-all-read", { method: "POST" }),

  searchMarkets: (query: string) => request<MarketSearchItem[]>(`/markets/search?query=${encodeURIComponent(query)}`),
  getMarketSnapshot: (symbol: string) => request<MarketSnapshot>(`/markets/${symbol}/snapshot`),
  getMarketRules: (symbol: string) => request<MarketRules>(`/markets/${symbol}/rules`),
  getMarketOrderbook: (symbol: string) => request<OrderBook>(`/markets/${symbol}/orderbook`),
  getMarketRecentTrades: (symbol: string) => request<TradeTick[]>(`/markets/${symbol}/recent-trades`),
  checkTechnicalGuard: (symbol: string) => request<TechnicalGuardResponse>("/technical-guard/check", { method: "POST", body: { symbol } }),
  checkOrderRisk: (payload: Record<string, unknown>) => request<RiskCheckResponse>("/risk/check-order", { method: "POST", body: payload }),

  previewManualOrder: (payload: Record<string, unknown>) => request<ManualOrderPreviewResponse>("/manual-orders/preview", { method: "POST", body: payload }),
  createManualOrder: (payload: Record<string, unknown>, idempotencyKey?: string) =>
    request<ManualOrderCreateResponse>("/manual-orders", { method: "POST", body: payload, headers: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : undefined }),
  confirmRealOrder: (id: number, confirm_token: string) => request<ManualOrder>(`/manual-orders/${id}/confirm-real`, { method: "POST", body: { confirm_token } }),
  cancelManualOrder: (id: number) => request<ManualOrder>(`/manual-orders/${id}/cancel`, { method: "DELETE" }),
  listManualOrders: (params?: { symbol?: string; mode?: string }) => {
    const query = new URLSearchParams();
    if (params?.symbol) query.set("symbol", params.symbol);
    if (params?.mode) query.set("mode", params.mode);
    return request<ManualOrder[]>(`/manual-orders${query.toString() ? `?${query.toString()}` : ""}`);
  },

  listPositions: () => request<PositionItem[]>("/positions"),
  closePositionPreview: (id: number) => request<PositionClosePreview>(`/positions/${id}/close-preview`, { method: "POST" }),
  closePosition: (id: number, confirm_token?: string | null) => request<PositionItem>(`/positions/${id}/close`, { method: "POST", body: { confirm_token } }),
  updatePositionTpSl: (id: number, payload: { take_profit?: string | null; stop_loss?: string | null }) =>
    request<PositionItem>(`/positions/${id}/tp-sl`, { method: "PATCH", body: payload }),
  startPositionMonitor: () => request<{ running: boolean }>("/positions/monitor/start", { method: "POST" }),
  stopPositionMonitor: () => request<{ running: boolean }>("/positions/monitor/stop", { method: "POST" }),
  getPositionMonitorStatus: () => request<{ running: boolean }>("/positions/monitor/status"),

  analyzeAiSignal: (symbol: string) => request<AiDecision>("/ai/analyze", { method: "POST", body: { symbol } }),
  executeAiSignal: (payload: { decision_id: number; prefer_real_execution: boolean; confirm_token?: string | null }) =>
    request<AiExecuteResponse>("/ai/execute", { method: "POST", body: payload }),
  listAiDecisions: () => request<AiDecision[]>("/ai/decisions"),
  getAiDecision: (id: number) => request<AiDecision>(`/ai/decisions/${id}`),

  listBots: () => request<BotConfig[]>("/bots"),
  createBot: (payload: Record<string, unknown>) => request<BotConfig>("/bots", { method: "POST", body: payload }),
  updateBot: (id: number, payload: Record<string, unknown>) => request<BotConfig>(`/bots/${id}`, { method: "PATCH", body: payload }),
  deleteBot: (id: number) => request<{ success: boolean }>(`/bots/${id}`, { method: "DELETE" }),
  getBot: (id: number) => request<BotConfig>(`/bots/${id}`),
  startBot: (id: number, confirm_token?: string | null) => request<{ status: string; bot_run_id?: number | null; confirm_token?: string | null }>(`/bots/${id}/start`, { method: "POST", body: { confirm_token } }),
  stopBot: (id: number) => request<{ success: boolean }>(`/bots/${id}/stop`, { method: "POST" }),
  getBotDecisions: (id: number) => request<BotDecision[]>(`/bots/${id}/decisions`),
  getBotRuns: (id: number) => request<BotRun[]>(`/bots/${id}/runs`),

  listWatchTasks: () => request<WatchTask[]>("/watch-tasks"),
  cancelWatchTask: (id: number) => request<WatchTask>(`/watch-tasks/${id}/cancel`, { method: "POST" }),

  listStrategies: () => request<Array<{ name: string }>>("/strategies"),
  getStrategy: (name: string) => request<{ name: string }>(`/strategies/${name}`),
  analyzeStrategy: (name: string, symbol: string, config: Record<string, unknown>) =>
    request<StrategyDecision>(`/strategies/${name}/analyze`, { method: "POST", body: { symbol, config } }),

  listScripts: () => request<ScriptFileItem[]>("/scripts"),
  refreshScripts: () => request<ScriptFileItem[]>("/scripts/refresh", { method: "POST" }),
  updateScript: (id: number, enabled: boolean) => request<ScriptFileItem>(`/scripts/${id}`, { method: "PATCH", body: { enabled } }),
  startScript: (id: number) => request<ScriptRunItem>(`/scripts/${id}/start`, { method: "POST" }),
  listScriptRuns: () => request<ScriptRunItem[]>("/scripts/runs"),
  getScriptRun: (id: number) => request<ScriptRunItem>(`/scripts/runs/${id}`),
  stopScriptRun: (id: number) => request<ScriptRunItem>(`/scripts/runs/${id}/stop`, { method: "POST" }),
  restartScriptRun: (id: number) => request<ScriptRunItem>(`/scripts/runs/${id}/restart`, { method: "POST" }),
  sendScriptStdin: (id: number, value: string) => request<ScriptRunItem>(`/scripts/runs/${id}/stdin`, { method: "POST", body: { value } }),
  listScriptLogs: (id: number) => request<ScriptLogItem[]>(`/scripts/runs/${id}/logs`),

  importBacktestCsv: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return requestForm<CsvImportResult>("/data/import/csv", formData);
  },
  runBacktest: (payload: Record<string, unknown>) => request<BacktestRun>("/backtests/run", { method: "POST", body: payload }),
  listBacktests: () => request<BacktestRun[]>("/backtests"),
  getBacktest: (id: number) => request<BacktestRun>(`/backtests/${id}`),
  getBacktestTrades: (id: number) => request<BacktestTrade[]>(`/backtests/${id}/trades`),
  getBacktestEquity: (id: number) => request<BacktestEquityPoint[]>(`/backtests/${id}/equity`),
  deleteBacktest: (id: number) => request<{ success: boolean }>(`/backtests/${id}`, { method: "DELETE" }),

  getReportSummary: () => request<ReportSummary>("/reports/summary"),
  getReportTrades: (params?: { symbol?: string; strategy?: string; mode?: string }) => {
    const query = new URLSearchParams();
    if (params?.symbol) query.set("symbol", params.symbol);
    if (params?.strategy) query.set("strategy", params.strategy);
    if (params?.mode) query.set("mode", params.mode);
    return request<Array<Record<string, unknown>>>(`/reports/trades${query.toString() ? `?${query.toString()}` : ""}`);
  },
  getReportAiDecisions: (symbol?: string) => request<Array<Record<string, unknown>>>(`/reports/ai-decisions${symbol ? `?symbol=${encodeURIComponent(symbol)}` : ""}`),
  getReportBotDecisions: (symbol?: string) => request<Array<Record<string, unknown>>>(`/reports/bot-decisions${symbol ? `?symbol=${encodeURIComponent(symbol)}` : ""}`),
  getReportBacktests: (params?: { symbol?: string; strategy?: string }) => {
    const query = new URLSearchParams();
    if (params?.symbol) query.set("symbol", params.symbol);
    if (params?.strategy) query.set("strategy", params.strategy);
    return request<Array<Record<string, unknown>>>(`/reports/backtests${query.toString() ? `?${query.toString()}` : ""}`);
  },
  getPnlBySymbol: () => request<PnlBucket[]>("/reports/pnl-by-symbol"),
  getPnlByStrategy: () => request<PnlBucket[]>("/reports/pnl-by-strategy"),
  downloadCsv: (path: string) => requestBlob(path),

  getRiskSettings: () => request<GenericSettingsResponse>("/settings/risk"),
  updateRiskSettings: (value: Record<string, unknown>) => request<GenericSettingsResponse>("/settings/risk", { method: "PUT", body: { value } }),
  getAiEngineSettings: () => request<GenericSettingsResponse>("/settings/ai-engines"),
  updateAiEngineSettings: (value: Record<string, unknown>) => request<GenericSettingsResponse>("/settings/ai-engines", { method: "PUT", body: { value } }),
  getStrategySettings: () => request<GenericSettingsResponse>("/settings/strategies"),
  updateStrategySettings: (value: Record<string, unknown>) => request<GenericSettingsResponse>("/settings/strategies", { method: "PUT", body: { value } }),
  getEmergencySettings: () => request<GenericSettingsResponse>("/settings/emergency"),
  updateEmergencySettings: (value: Record<string, unknown>) => request<GenericSettingsResponse>("/settings/emergency", { method: "PUT", body: { value } }),

  emergencyStopAllBots: () => request<{ stopped_bots: number }>("/emergency/stop-all-bots", { method: "POST" }),
  emergencyPauseTrading: () => request<{ paused: boolean }>("/emergency/pause-trading", { method: "POST" }),
  emergencyResumeTrading: () => request<{ paused: boolean }>("/emergency/resume-trading", { method: "POST" }),
  emergencyDisableRealTrading: () => request<{ real_trading_locked: boolean }>("/emergency/disable-real-trading", { method: "POST" }),
  emergencyCloseAllDryRun: () => request<{ closed_positions: number }>("/emergency/close-all-dry-run", { method: "POST" }),
  emergencyCloseAllRealPreview: () => request<{ confirm_token: string; expires_in_seconds: number }>("/emergency/close-all-real-preview", { method: "POST" }),
  emergencyCloseAllRealConfirm: (confirm_token: string) => request<{ closed_positions: number }>("/emergency/close-all-real-confirm", { method: "POST", body: { confirm_token } }),

  listAuditLogs: (params?: { action?: string; entity_type?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.action) query.set("action", params.action);
    if (params?.entity_type) query.set("entity_type", params.entity_type);
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset) query.set("offset", String(params.offset));
    return request<AuditLogItem[]>(`/audit-logs${query.toString() ? `?${query.toString()}` : ""}`);
  },
  listLearningMemory: (params?: { symbol?: string; strategy_name?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.symbol) query.set("symbol", params.symbol);
    if (params?.strategy_name) query.set("strategy_name", params.strategy_name);
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset) query.set("offset", String(params.offset));
    return request<LearningMemoryItem[]>(`/learning-memory${query.toString() ? `?${query.toString()}` : ""}`);
  },
  listTradeOutcomes: (params?: { symbol?: string; strategy_name?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.symbol) query.set("symbol", params.symbol);
    if (params?.strategy_name) query.set("strategy_name", params.strategy_name);
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset) query.set("offset", String(params.offset));
    return request<TradeOutcomeItem[]>(`/learning-memory/outcomes${query.toString() ? `?${query.toString()}` : ""}`);
  },
  createBackup: () => request<BackupItem>("/backup/create", { method: "POST" }),
  listBackups: () => request<BackupItem[]>("/backup/list"),
  restoreBackup: (id: string) => request<{ restored: boolean; backup_id: string }>(`/backup/${id}/restore`, { method: "POST" }),
  downloadBackup: (id: string) => requestBlob(`/backup/${id}/download`),
};
