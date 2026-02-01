// API Configuration
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Generic fetch wrapper
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_URL}${endpoint}`, {
        headers: {
            "Content-Type": "application/json",
            ...options?.headers,
        },
        ...options,
    });

    if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
}

// Types
export interface CoinData {
    coin: string;
    days: number;
    timeframe: string;
    source: string;
    data: OHLCVData[];
    indicators: string[];
}

export interface OHLCVData {
    time: number | string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    ema_9?: number;
    ema_21?: number;
    rsi_14?: number;
}

export interface Strategy {
    slug: string;
    name: string;
    category: string;
    icon: string;
    description: string;
    idealFor?: string;
    parameters?: Record<string, ParameterConfig>;
}

export interface ParameterConfig {
    default: number;
    min: number;
    max: number;
    label: string;
}

export interface Trade {
    id?: number;
    type: "BUY" | "SELL";
    entry_date: string;
    entry_ts: number;
    entry_price: number;
    exit_date?: string;
    exit_ts?: number;
    exit_price?: number;
    size: number;
    pnl?: number;
    pnl_pct?: number;
    fee?: number;
    status: "OPEN" | "CLOSED";
}

export interface BacktestResult {
    slug: string;
    trades: Trade[];
    metrics: {
        total_pnl: number;
        total_pnl_pct: number;
        win_rate: number;
        max_drawdown: number;
        total_trades: number;
    };
}

export interface ResultsData {
    metrics: {
        total_trades: number;
        buy_trades: number;
        sell_trades: number;
        completed_trades: number;
        final_value: number;
        total_pnl: number;
        total_pnl_pct: number;
        win_rate: number;
        profit_factor: number;
    };
    drawdown: {
        max_drawdown_pct: number;
        max_drawdown_date: string | null;
        current_drawdown_pct: number;
        max_daily_loss_pct: number;
    };
    ftmo: {
        passed_profit: boolean;
        passed_drawdown: boolean;
        passed_daily_loss: boolean;
        passed_days: boolean;
        all_passed: boolean;
    };
}

// API Functions
export const api = {
    // Health check
    health: () => fetchAPI<{ status: string; version: string }>("/api/health"),

    // Market data
    getMarketData: (coin: string, days = 90, timeframe = "1h") =>
        fetchAPI<CoinData>(`/api/market/?coin=${encodeURIComponent(coin)}&days=${days}&timeframe=${timeframe}`),

    // Strategies
    listStrategies: () => fetchAPI<Strategy[]>("/api/strategies/"),

    getStrategy: (slug: string) => fetchAPI<Strategy>(`/api/strategies/${slug}`),

    // Custom Strategies Persistence
    saveCustomStrategy: (strategy: {
        name: string;
        description?: string;
        coin: string;
        period: string;
        timeframe: string;
        rules: any;
    }) =>
        fetchAPI<{ id: number; status: string }>("/api/strategies/custom", {
            method: "POST",
            body: JSON.stringify(strategy),
        }),

    listCustomStrategies: () => fetchAPI<any[]>("/api/strategies/custom"), // Uses DB Strategy model

    deleteCustomStrategy: (id: number) => fetchAPI<{ status: string }>(`/api/strategies/custom/${id}`, { method: "DELETE" }),

    runStrategy: (
        slug: string,
        options: {
            coin: string;
            days: number;
            timeframe: string;
            initial_balance: number;
            use_compound?: boolean;
            sizing_method?: string;
            params?: any;
            include_fees?: boolean;
            fee_rate?: number;
        }
    ) =>
        fetchAPI<BacktestResult>(`/api/strategies/${slug}/run`, {
            method: "POST",
            body: JSON.stringify(options),
        }),

    // Optimizer
    runOptimizer: (
        params: {
            strategies: string[];
            coin: string;
            days: number;
            param_steps: number;
            optimize_execution: boolean;
            min_pairs: number;
            include_fees: boolean;
            fee_rate?: number;
            initial_balance?: number;
            use_compound?: boolean;
        }
    ) =>
        fetchAPI<{
            request: unknown;
            total_combinations: number;
            results: unknown[];
            champion: unknown;
            execution_time_ms: number;
        }>("/api/optimizer/run", {
            method: "POST",
            body: JSON.stringify(params),
        }),

    // Results & Context
    setMarketContext: (context: { coin: string; days: number; timeframe: string }) =>
        fetchAPI<{ message: string }>("/api/results/context", {
            method: "POST",
            body: JSON.stringify(context),
        }),

    getMarketContext: () => fetchAPI<{ coin: string; days: number; timeframe: string } | null>("/api/results/context"),

    clearMarketContext: () => fetchAPI<{ message: string }>("/api/results/context", { method: "DELETE" }),

    calculateResults: (trades: Trade[], initial_balance = 10000, coin = "SOL/USDT") =>
        fetchAPI<ResultsData>("/api/results/calculate", {
            method: "POST",
            body: JSON.stringify({ trades, initial_balance, coin }),
        }),

    setActiveStrategy: (strategy: {
        strategy_slug: string;
        params: any;
        coin: string;
        period: string;
        timeframe: string;
        initial_balance: number;
        use_compound: boolean;
        sizing_method: string;
        include_fees: boolean;
        fee_rate: number;
        backtest_metrics: any;
    }) =>
        fetchAPI<{ message: string }>("/api/strategies/active/set", {
            method: "POST",
            body: JSON.stringify(strategy),
        }),

    getActiveStrategy: () => fetchAPI<any | null>("/api/strategies/active"),

    clearActiveStrategy: () => fetchAPI<{ status: string }>("/api/strategies/active", { method: "DELETE" }),

    // Glossary
    listGlossary: (category?: string) =>
        fetchAPI<{ categories: string[]; total: number; terms: unknown[] }>(
            `/api/glossary/${category ? `?category=${category}` : ""}`
        ),

    getGlossaryTerm: (slug: string) => fetchAPI<unknown>(`/api/glossary/${slug}`),

    // ========================================
    // Live Trading (Paper Trading)
    // ========================================

    // Get all sessions
    getLiveSessions: (status?: string) =>
        fetchAPI<unknown[]>(`/api/live/sessions${status ? `?status=${status}` : ""}`),

    // Get single session details
    getLiveSession: (sessionId: number) =>
        fetchAPI<unknown>(`/api/live/sessions/${sessionId}`),

    // Start a new session
    startLiveSession: (options: {
        strategy_slug: string;
        strategy_params?: Record<string, unknown>;
        coin: string;
        timeframe: string;
        initial_balance: number;
        telegram_chat_id?: string;
    }) =>
        fetchAPI<{ message: string; session_id: number }>("/api/live/start", {
            method: "POST",
            body: JSON.stringify(options),
        }),

    // Stop a session
    stopLiveSession: (sessionId: number) =>
        fetchAPI<{ message: string; final_balance: number; pnl: number }>(`/api/live/stop/${sessionId}`, {
            method: "POST",
        }),

    // Reset a session
    resetLiveSession: (sessionId: number) =>
        fetchAPI<{ message: string; new_balance: number }>(`/api/live/sessions/${sessionId}/reset`, {
            method: "POST",
        }),

    // Delete a session
    deleteLiveSession: (sessionId: number) =>
        fetchAPI<{ message: string }>(`/api/live/sessions/${sessionId}`, {
            method: "DELETE",
        }),

    // Deposit to session
    depositLiveSession: (sessionId: number, amount: number, note?: string) =>
        fetchAPI<{ message: string; balance_after: number }>(`/api/live/sessions/${sessionId}/deposit`, {
            method: "POST",
            body: JSON.stringify({ amount, note }),
        }),

    // Withdraw from session
    withdrawLiveSession: (sessionId: number, amount: number, note?: string) =>
        fetchAPI<{ message: string; balance_after: number }>(`/api/live/sessions/${sessionId}/withdraw`, {
            method: "POST",
            body: JSON.stringify({ amount, note }),
        }),

    // Get global status
    getLiveStatus: () =>
        fetchAPI<{
            active_sessions_count: number;
            active_streams_count: number;
            telegram_configured: boolean;
            sessions: unknown[];
            streams: unknown[];
        }>("/api/live/status"),

    // Get aggregated stats
    getLiveStats: () =>
        fetchAPI<{
            total_sessions: number;
            active_sessions: number;
            total_trades: number;
            total_pnl: number;
            win_rate: number;
        }>("/api/live/stats"),
};

export default api;
