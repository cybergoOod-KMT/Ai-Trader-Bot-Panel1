export type User = {
  id: number;
  username: string;
  force_password_change: boolean;
  created_at: string;
  updated_at: string;
};

export type AuthStatus = {
  authenticated: boolean;
  user: User | null;
};

export type ApiAccount = {
  id: number;
  name: string;
  openai_model: string;
  is_active: boolean;
  read_only: boolean;
  real_trading_allowed: boolean;
  has_tabdeal_api_key: boolean;
  tabdeal_api_key_masked: string | null;
  has_tabdeal_api_secret: boolean;
  tabdeal_api_secret_masked: string | null;
  has_openai_api_key: boolean;
  openai_api_key_masked: string | null;
  created_at: string;
  updated_at: string;
};

export type ConnectionTestResult = {
  success: boolean;
  message: string;
  details: Record<string, unknown> | null;
};

export type SystemLog = {
  id: number;
  level: string;
  source: string;
  message: string;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
};

export type NotificationItem = {
  id: number;
  type: string;
  severity: string;
  title: string;
  message: string;
  is_read: boolean;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
};

export type DashboardResponse = {
  api_status: string;
  openai_status: string;
  active_api_account: {
    id: number;
    name: string;
    read_only: boolean;
    real_trading_allowed: boolean;
    has_tabdeal_credentials: boolean;
    has_openai_api_key: boolean;
  } | null;
  latest_system_logs: Array<{
    id: number;
    level: string;
    source: string;
    message: string;
    created_at: string;
  }>;
  balances: Array<Record<string, unknown>>;
  open_orders: Array<Record<string, unknown>>;
  open_positions: Array<Record<string, unknown>>;
  latest_trades: Array<Record<string, unknown>>;
  active_bots: Array<Record<string, unknown>>;
  active_watches: Array<Record<string, unknown>>;
  latest_ai_decisions: Array<Record<string, unknown>>;
  latest_strategy_decisions: Array<Record<string, unknown>>;
  active_script_runs: Array<Record<string, unknown>>;
  latest_notifications: NotificationItem[];
  pnl_chart: Array<{ label: string; value: number }>;
  today_dry_run_pnl: string;
  today_real_pnl: string;
  bot_health: Record<string, unknown>;
  unread_notifications_count: number;
  real_trading_enabled: boolean;
  dry_run_default: boolean;
  phase: string;
};

export type MarketSearchItem = {
  symbol: string;
  base_asset: string;
  quote_asset: string;
  status: string;
};

export type MarketRules = {
  symbol: string;
  base_asset: string;
  quote_asset: string;
  price_precision: number;
  quantity_precision: number;
  min_qty: string | null;
  step_size: string | null;
  min_notional: string | null;
  tick_size: string | null;
  raw_filters: Array<Record<string, unknown>>;
};

export type OrderBookLevel = {
  price: string;
  quantity: string;
};

export type OrderBook = {
  symbol: string;
  bids: OrderBookLevel[];
  asks: OrderBookLevel[];
  best_bid: string | null;
  best_ask: string | null;
  spread_pct: string | null;
};

export type TradeTick = {
  id: string | number | null;
  price: string;
  quantity: string;
  timestamp: number | null;
  is_buyer_maker: boolean | null;
};

export type MarketSnapshot = {
  symbol: string;
  source: string;
  timeframe: string;
  lookback: string;
  tabdeal_price: string;
  analysis_close: string;
  source_price_diff_pct: string;
  best_bid: string;
  best_ask: string;
  spread_pct: string;
  rsi14: string;
  ema9: string;
  ema21: string;
  ema50: string;
  macd: string;
  macd_signal: string;
  macd_histogram: string;
  atr14: string;
  support_20: string;
  resistance_20: string;
  volume_ratio: string;
  momentum_pct_1h: string;
  orderbook_pressure_bid_over_ask: string;
};

export type TechnicalGuardResponse = {
  allowed: boolean;
  reasons: string[];
  risk_reward: string;
  entry_type: string;
};

export type RiskCheckResponse = {
  allowed: boolean;
  reasons: string[];
  calculated_quantity: string;
  estimated_value: string;
  mode: string;
};

export type ManualOrderPreviewResponse = {
  symbol: string;
  normalized_quantity: string;
  normalized_price: string | null;
  estimated_value: string;
  market_snapshot: MarketSnapshot;
  risk: RiskCheckResponse;
  technical_guard: TechnicalGuardResponse | null;
};

export type ManualOrder = {
  id: number;
  api_account_id: number;
  symbol: string;
  side: string;
  order_type: string;
  quantity: string;
  price: string | null;
  estimated_value: string | null;
  mode: string;
  status: string;
  exchange_order_id: string | null;
  response_json: Record<string, unknown> | null;
  error_message: string | null;
  created_at: string;
};

export type ManualOrderCreateResponse = {
  order: ManualOrder;
  preview: ManualOrderPreviewResponse;
  confirm_token: string | null;
};

export type PositionItem = {
  id: number;
  symbol: string;
  base_asset: string;
  quote_asset: string;
  quantity: string;
  entry_price: string;
  current_price: string | null;
  take_profit: string | null;
  stop_loss: string | null;
  status: string;
  source: string;
  opened_by: string;
  opened_at: string;
  closed_at: string | null;
  pnl: string | null;
  pnl_pct: string | null;
};

export type PositionClosePreview = {
  position_id: number;
  symbol: string;
  quantity: string;
  estimated_close_price: string;
  estimated_value: string;
  mode: string;
  reasons: string[];
  confirm_token: string | null;
};

export type AiDecision = {
  id: number;
  api_account_id: number;
  symbol: string;
  action: string;
  confidence: number;
  reason: string;
  entry_note: string;
  entry_price: string | null;
  breakout_price: string | null;
  pullback_price: string | null;
  take_profit_pct: string;
  stop_loss_pct: string;
  risk_warning: string;
  technical_summary_json: Record<string, unknown>;
  market_snapshot_json: MarketSnapshot;
  account_snapshot_json: Record<string, unknown>;
  guard_result_json: TechnicalGuardResponse | null;
  risk_result_json: RiskCheckResponse | null;
  ai_engine_name: string;
  strategy_name: string | null;
  learning_memory_json: Record<string, unknown> | null;
  executed: boolean;
  execution_order_id: number | null;
  created_at: string;
};

export type AiExecuteResponse = {
  decision: AiDecision;
  order: Record<string, unknown>;
  preview: Record<string, unknown> | null;
  confirm_token: string | null;
};

export type BotConfig = {
  id: number;
  name: string;
  mode: string;
  api_account_id: number;
  symbols_json: string[];
  max_total_budget_usdt: string;
  per_order_usdt: string;
  max_open_positions: number;
  max_daily_loss_pct: string;
  min_ai_confidence: number;
  technical_guard_enabled: boolean;
  strategy_name: string;
  ai_engine_name: string;
  is_active: boolean;
  api_error_count: number;
  created_at: string;
  updated_at: string;
};

export type BotRun = {
  id: number;
  bot_config_id: number;
  status: string;
  started_at: string;
  stopped_at: string | null;
  error_message: string | null;
};

export type BotDecision = {
  id: number;
  bot_run_id: number;
  symbol: string;
  action: string;
  confidence: number;
  reason: string;
  market_snapshot_json: MarketSnapshot;
  ai_decision_id: number | null;
  guard_result_json: Record<string, unknown> | null;
  risk_result_json: Record<string, unknown> | null;
  strategy_name?: string | null;
  ai_engine_name?: string | null;
  executed: boolean;
  created_at: string;
};

export type WatchTask = {
  id: number;
  bot_run_id: number;
  symbol: string;
  type: string;
  trigger_price: string;
  invalidation_price: string | null;
  status: string;
  reason: string;
  created_at: string;
  updated_at: string;
};

export type StrategyDecision = {
  action: string;
  confidence: number;
  reason: string;
  entry_price: number | null;
  take_profit_pct: number | null;
  stop_loss_pct: number | null;
  metadata: Record<string, unknown>;
};

export type ScriptFileItem = {
  id: number;
  name: string;
  relative_path: string;
  enabled: boolean;
  detected_at: string;
  created_at: string;
  updated_at: string;
};

export type ScriptRunItem = {
  id: number;
  script_file_id: number;
  status: string;
  pid: number | null;
  started_at: string;
  stopped_at: string | null;
  exit_code: number | null;
  error_message: string | null;
};

export type ScriptLogItem = {
  id: number;
  script_run_id: number;
  stream: string;
  line: string;
  created_at: string;
};

export type BacktestRun = {
  id: number;
  strategy_name: string;
  symbol: string;
  timeframe: string;
  start_time: string;
  end_time: string;
  initial_balance: string;
  final_balance: string;
  net_pnl: string;
  net_pnl_pct: string;
  max_drawdown: string;
  win_rate: string;
  profit_factor: string;
  config_json: Record<string, unknown>;
  result_json: Record<string, unknown>;
  created_at: string;
};

export type BacktestTrade = {
  id: number;
  backtest_run_id: number;
  symbol: string;
  side: string;
  entry_price: string;
  exit_price: string;
  quantity: string;
  pnl: string;
  pnl_pct: string;
  opened_at: string;
  closed_at: string;
  reason: string;
};

export type BacktestEquityPoint = {
  timestamp: string;
  equity: number;
  drawdown_pct: number;
};

export type ReportSummary = {
  trades_count: number;
  ai_decisions_count: number;
  bot_decisions_count: number;
  backtests_count: number;
  script_runs_count: number;
  dry_run_pnl: number;
  real_pnl: number;
};

export type PnlBucket = {
  key: string;
  pnl: number;
  count: number;
};

export type CsvImportResult = {
  dataset_id: string;
  rows: number;
  symbol_hint: string | null;
};

export type GenericSettingsResponse = {
  key: string;
  value: Record<string, unknown>;
};

export type AuditLogItem = {
  id: number;
  actor_user_id: number | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  before_json: Record<string, unknown> | null;
  after_json: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
};

export type LearningMemoryItem = {
  id: number;
  symbol: string;
  strategy_name: string;
  stats_json: Record<string, unknown>;
  lessons_json: Record<string, unknown>;
  updated_at: string;
};

export type TradeOutcomeItem = {
  id: number;
  symbol: string;
  strategy_name: string;
  ai_engine: string | null;
  entry_snapshot_json: Record<string, unknown>;
  decision_json: Record<string, unknown>;
  exit_reason: string;
  pnl: string;
  pnl_pct: string;
  duration_seconds: number;
  was_successful: boolean;
  created_at: string;
};

export type BackupItem = {
  id: string;
  files: string[];
  created_at: string;
};
