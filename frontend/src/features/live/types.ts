export interface Session {
    id: number;
    status: string;
    strategy_slug: string;
    coin: string;
    timeframe: string;
    initial_balance: number;
    current_balance: number;
    equity?: number;  // Cash + Position Value
    pnl: number;
    pnl_pct: number;
    total_trades: number;
    has_position: boolean;
    started_at: string | null;
    stopped_at: string | null;
    slot?: number;
}

export interface SessionDetails {
    session: {
        id: number;
        status: string;
        strategy_slug: string;
        strategy_params: Record<string, unknown>;
        coin: string;
        timeframe: string;
        initial_balance: number;
        current_balance: number;
        pnl: number;
        pnl_pct: number;
        telegram_configured: boolean;
        started_at: string | null;
        stopped_at: string | null;
    };
    position: {
        side: string;
        coin: string;
        entry_price: number;
        quantity: number;
        current_price: number;
        unrealized_pnl: number;
        opened_at: string | null;
    } | null;
    metrics: {
        total_trades: number;
        completed_trades: number;
        total_pnl: number;
        win_rate: number;
        position_amount?: number;
    };
    triggers: {
        status: string;
        message?: string;
        current_price?: number;
        has_position?: boolean;
        buy_rules: Array<{
            indicator: string;
            current: number;
            operator: string;
            threshold: number | string;
            active: boolean;
        }>;
        sell_rules: Array<{
            indicator: string;
            current: number;
            operator: string;
            threshold: number | string;
            active: boolean;
        }>;
    } | null;
    recent_trades: Array<{
        id: number;
        side: string;
        price: number;
        quantity: number;
        value: number;
        fee: number;
        pnl: number | null;
        pnl_pct: number | null;
        balance_after: number;
        executed_at: string | null;
    }>;
    recent_transactions: Array<{
        id: number;
        type: string;
        amount: number;
        balance_before: number;
        balance_after: number;
        note: string | null;
        created_at: string | null;
    }>;
    price_history: Array<{
        time: number;
        open: number;
        high: number;
        low: number;
        close: number;
    }>;
}

export interface Strategy {
    slug: string;
    name: string;
    icon: string;
    category: string;
}
