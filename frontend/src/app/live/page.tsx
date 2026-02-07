"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import api from "../../lib/api";
import { getStoredSettings } from "../../lib/settings";

// Types
interface Session {
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
}

interface SessionDetails {
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


interface Strategy {
    slug: string;
    name: string;
    icon: string;
    category: string;
}

// --- Interactive Chart Component ---
interface InteractiveChartProps {
    data: { time: number; open: number; high: number; low: number; close: number }[];
}

const InteractiveChart: React.FC<InteractiveChartProps> = ({ data }) => {
    const [hoveredCandle, setHoveredCandle] = useState<any>(null);

    const { width, height, minPrice, maxPrice, range, adjMin, adjRange, candleWidth, gap, scaleY } = useMemo(() => {
        const width = 600;
        const height = 200;
        const allPrices = data.flatMap(d => [d.high, d.low]);
        const minPrice = Math.min(...allPrices);
        const maxPrice = Math.max(...allPrices);
        const range = maxPrice - minPrice || 1;
        const padding = range * 0.1;
        const adjMin = minPrice - padding;
        const adjRange = range + padding * 2;
        const candleWidth = Math.max(3, (width / data.length) * 0.7);
        const gap = (width / data.length) * 0.15;
        const scaleY = (price: number) => height - ((price - adjMin) / adjRange) * height;

        return { width, height, minPrice, maxPrice, range, adjMin, adjRange, candleWidth, gap, scaleY };
    }, [data]);

    const displayCandle = hoveredCandle || data[data.length - 1];

    if (!data || data.length === 0) return null;

    return (
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 mt-4">
            {/* Header: OHLC Stats */}
            <div className="flex justify-between items-center mb-4 text-xs font-mono">
                <div className="flex flex-wrap gap-4 md:gap-6">
                    <span className="text-gray-400">Abertura: <span className={displayCandle.open > displayCandle.close ? "text-red-400" : "text-green-400"}>{displayCandle.open.toFixed(2)}</span></span>
                    <span className="text-gray-400">Máxima: <span className="text-gray-200">{displayCandle.high.toFixed(2)}</span></span>
                    <span className="text-gray-400">Mínima: <span className="text-gray-200">{displayCandle.low.toFixed(2)}</span></span>
                    <span className="text-gray-400">Fechamento: <span className={displayCandle.close >= displayCandle.open ? "text-green-400" : "text-red-400"}>{displayCandle.close.toFixed(2)}</span></span>
                </div>
                <div className="text-gray-500 whitespace-nowrap ml-4">
                    Horário: {new Date(displayCandle.time * 1000).toLocaleTimeString()}
                </div>
            </div>

            {/* Chart */}
            <div className="w-full h-48 relative cursor-crosshair">
                <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full" preserveAspectRatio="none">
                    {data.map((candle, i) => {
                        const x = (i / data.length) * width + gap;
                        const isGreen = candle.close >= candle.open;
                        const color = isGreen ? "#22c55e" : "#ef4444";
                        const bodyTop = scaleY(Math.max(candle.open, candle.close));
                        const bodyBottom = scaleY(Math.min(candle.open, candle.close));
                        const bodyHeight = Math.max(1, bodyBottom - bodyTop);
                        const wickX = x + candleWidth / 2;

                        return (
                            <g key={i}
                                onMouseEnter={() => setHoveredCandle(candle)}
                                onMouseLeave={() => setHoveredCandle(null)}
                            >
                                {/* Invisible Hit Area (Larger) */}
                                <rect
                                    x={x - gap / 2}
                                    y={0}
                                    width={candleWidth + gap}
                                    height={height}
                                    fill="transparent"
                                />

                                {/* Wick */}
                                <line
                                    x1={wickX}
                                    y1={scaleY(candle.high)}
                                    x2={wickX}
                                    y2={scaleY(candle.low)}
                                    stroke={color}
                                    strokeWidth="1"
                                    className="pointer-events-none"
                                />
                                {/* Body */}
                                <rect
                                    x={x}
                                    y={bodyTop}
                                    width={candleWidth}
                                    height={bodyHeight}
                                    fill={color}
                                    className="pointer-events-none"
                                />
                            </g>
                        );
                    })}

                    {/* Linha de Preço Atual (Dotted) */}
                    <line
                        x1="0"
                        y1={scaleY(displayCandle.close)}
                        x2={width}
                        y2={scaleY(displayCandle.close)}
                        stroke="#ffffff"
                        strokeOpacity="0.2"
                        strokeDasharray="4"
                    />
                </svg>
            </div>
        </div>
    );
};

export default function LiveTradingPage() {

    // State
    const [sessions, setSessions] = useState<Session[]>([]);
    const [selectedSession, setSelectedSession] = useState<SessionDetails | null>(null);
    const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);
    const selectedSessionIdRef = useRef<number | null>(null); // Para evitar race condition
    const deletedSessionIds = useRef<Set<number>>(new Set()); // Para evitar que polling traga de volta sessões deletadas

    const [strategies, setStrategies] = useState<Strategy[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Form state
    const [selectedStrategy, setSelectedStrategy] = useState("");
    const [showNewSessionForm, setShowNewSessionForm] = useState(false);

    // Transaction modal
    const [transactionModal, setTransactionModal] = useState<{
        type: "deposit" | "withdrawal";
        sessionId: number;
    } | null>(null);
    const [transactionAmount, setTransactionAmount] = useState("");
    const [transactionNote, setTransactionNote] = useState("");

    // Helpers
    const handleSessionSelect = (id: number) => {
        setSelectedSession(null); // Clear stale data immediate
        setSelectedSessionId(id);
        selectedSessionIdRef.current = id;
        loadSessionDetails(id);
    };

    // Load data
    const loadSessions = useCallback(async () => {
        try {
            const data = await api.getLiveSessions() as Session[];
            // Filter out sessions that are marked as deleted locally
            const filteredData = data.filter(s => !deletedSessionIds.current.has(s.id));
            setSessions(filteredData);
        } catch (e) {
            console.error("Failed to load sessions", e);
        }
    }, []);

    const loadStrategies = useCallback(async () => {
        try {
            const data = await api.listStrategies();
            setStrategies(data);
        } catch (e) {
            console.error("Failed to load strategies", e);
        }
    }, []);

    const loadSessionDetails = useCallback(async (sessionId: number) => {
        try {
            const data = await api.getLiveSession(sessionId) as SessionDetails;

            // Check for race condition
            if (selectedSessionIdRef.current === sessionId) {
                setSelectedSession(data);
            }
        } catch (e) {
            console.error("Failed to load session details", e);
        }
    }, []);

    useEffect(() => {
        loadSessions();
        loadStrategies();

        // Poll sessions every 5 seconds
        const interval = setInterval(loadSessions, 5000);
        return () => clearInterval(interval);
    }, [loadSessions, loadStrategies]);

    // Refresh selected session details
    useEffect(() => {
        if (!selectedSessionId) return;

        // Initial load
        loadSessionDetails(selectedSessionId);

        const interval = setInterval(() => {
            loadSessionDetails(selectedSessionId);
        }, 3000);

        return () => clearInterval(interval);
    }, [selectedSessionId, loadSessionDetails]);

    // Handlers
    const handleStartSession = async () => {
        if (!selectedStrategy) {
            setError("Selecione uma estratégia");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const settings = getStoredSettings();

            await api.startLiveSession({
                strategy_slug: selectedStrategy,
                coin: settings.paperTradingCoin,
                timeframe: settings.paperTradingTimeframe,
                initial_balance: settings.paperTradingBalance,
                telegram_chat_id: settings.telegramChatId || undefined,
            });

            await loadSessions();
            setShowNewSessionForm(false);
            setSelectedStrategy("");
        } catch (e: unknown) {
            const errorMessage = e instanceof Error ? e.message : "Erro ao iniciar sessão";
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    const handleStopSession = async (sessionId: number) => {
        if (!confirm("Tem certeza que deseja parar esta sessão?")) return;

        setLoading(true);
        try {
            await api.stopLiveSession(sessionId);
            await loadSessions();
            if (selectedSession?.session.id === sessionId) {
                loadSessionDetails(sessionId);
            }
        } catch (e: unknown) {
            const errorMessage = e instanceof Error ? e.message : "Erro ao parar sessão";
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    const handleResetSession = async (sessionId: number) => {
        if (!confirm("Tem certeza? Isso irá apagar todos os trades e resetar o saldo.")) return;

        setLoading(true);
        try {
            await api.resetLiveSession(sessionId);
            await loadSessions();
            if (selectedSession?.session.id === sessionId) {
                loadSessionDetails(sessionId);
            }
        } catch (e: unknown) {
            const errorMessage = e instanceof Error ? e.message : "Erro ao resetar sessão";
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteSession = async (sessionId: number, force: boolean = false) => {
        // Confirmação já é feita no onClick do botão, não precisa aqui

        // Add to ignored list immediately to prevent polling from bringing it back
        deletedSessionIds.current.add(sessionId);

        // Feedback imediato - remove da UI antes da API responder
        if (selectedSession?.session.id === sessionId) {
            setSelectedSession(null);
            setSelectedSessionId(null);
        }
        setSessions(prev => prev.filter(s => s.id !== sessionId));

        // Não precisa de loading pois UI já foi atualizada
        try {
            await api.deleteLiveSession(sessionId, force);
            // Não recarrega - a UI já foi atualizada otimisticamente
        } catch (e: unknown) {
            const errorMessage = e instanceof Error ? e.message : "Erro ao deletar sessão";
            setError(errorMessage);

            // Se falhar, remove da lista de ignorados e recarrega para restaurar
            deletedSessionIds.current.delete(sessionId);
            await loadSessions();
        }
    };

    const handleTransaction = async () => {
        if (!transactionModal || !transactionAmount) return;

        const amount = parseFloat(transactionAmount);
        if (isNaN(amount) || amount <= 0) {
            setError("Valor inválido");
            return;
        }

        setLoading(true);
        try {
            if (transactionModal.type === "deposit") {
                await api.depositLiveSession(transactionModal.sessionId, amount, transactionNote || undefined);
            } else {
                await api.withdrawLiveSession(transactionModal.sessionId, amount, transactionNote || undefined);
            }

            await loadSessions();
            if (selectedSession?.session.id === transactionModal.sessionId) {
                loadSessionDetails(transactionModal.sessionId);
            }

            setTransactionModal(null);
            setTransactionAmount("");
            setTransactionNote("");
        } catch (e: unknown) {
            const errorMessage = e instanceof Error ? e.message : "Erro na transação";
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    // Render helpers
    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            minimumFractionDigits: 2,
        }).format(value);
    };

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return "-";
        return new Date(dateStr).toLocaleString("pt-BR");
    };

    const getPnLColor = (pnl: number) => {
        if (pnl > 0) return "text-green-400";
        if (pnl < 0) return "text-red-400";
        return "text-gray-400";
    };



    return (
        <div className="min-h-screen bg-gray-950 p-6">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        🎮 Paper Trading
                    </h1>
                    <p className="text-gray-400 text-sm mt-1">
                        Teste estratégias com preços ao vivo sem arriscar dinheiro real
                    </p>
                </div>

                <button
                    onClick={() => setShowNewSessionForm(!showNewSessionForm)}
                    className="px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white font-medium rounded-lg flex items-center gap-2"
                >
                    ➕ Nova Sessão
                </button>
            </div>

            {/* Error Alert */}
            {error && (
                <div className="mb-4 p-4 bg-red-900/30 border border-red-500/50 rounded-lg text-red-400">
                    {error}
                    <button onClick={() => setError(null)} className="ml-4 underline">Fechar</button>
                </div>
            )}

            {/* New Session Form */}
            {showNewSessionForm && (
                <div className="mb-6 p-6 bg-gray-800/50 border border-gray-700 rounded-xl">
                    <h2 className="text-lg font-semibold text-white mb-4">Iniciar Nova Sessão</h2>

                    <div className="grid md:grid-cols-2 gap-4">
                        {/* Strategy */}
                        <div className="md:col-span-2">
                            <label className="block text-gray-400 text-sm mb-2">Estratégia</label>
                            <select
                                value={selectedStrategy}
                                onChange={(e) => setSelectedStrategy(e.target.value)}
                                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white"
                            >
                                <option value="">Selecione...</option>
                                {strategies.map((s) => (
                                    <option key={s.slug} value={s.slug}>
                                        {s.icon} {s.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div className="mt-4 p-3 bg-blue-900/20 border border-blue-500/30 rounded-lg">
                        <p className="text-blue-400 text-sm">
                            📍 Configurações carregadas de Settings:
                        </p>
                        <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                            <div>
                                <span className="text-gray-400">Par:</span>{" "}
                                <strong className="text-white">{getStoredSettings().paperTradingCoin}</strong>
                            </div>
                            <div>
                                <span className="text-gray-400">Timeframe:</span>{" "}
                                <strong className="text-white">{getStoredSettings().paperTradingTimeframe}</strong>
                            </div>
                            <div>
                                <span className="text-gray-400">Saldo:</span>{" "}
                                <strong className="text-white">${getStoredSettings().paperTradingBalance.toLocaleString()}</strong>
                            </div>
                            <div>
                                <span className="text-gray-400">Telegram:</span>{" "}
                                <strong className={getStoredSettings().telegramChatId ? "text-green-400" : "text-gray-500"}>
                                    {getStoredSettings().telegramChatId ? "✓ Configurado" : "Não configurado"}
                                </strong>
                            </div>
                        </div>
                        <p className="text-blue-300 text-xs mt-2">
                            <a href="/settings" className="underline hover:text-blue-200">Alterar configurações →</a>
                        </p>
                    </div>

                    <div className="flex gap-3 mt-4">
                        <button
                            onClick={handleStartSession}
                            disabled={loading || !selectedStrategy}
                            className="px-6 py-2 bg-green-600 hover:bg-green-500 text-white font-medium rounded-lg disabled:opacity-50"
                        >
                            {loading ? "⏳ Iniciando..." : "🚀 Iniciar"}
                        </button>
                        <button
                            onClick={() => setShowNewSessionForm(false)}
                            className="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg"
                        >
                            Cancelar
                        </button>
                    </div>
                </div>
            )}

            <div className="grid lg:grid-cols-3 gap-6">
                {/* Sessions List */}
                <div className="lg:col-span-1">
                    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
                        <h2 className="text-lg font-semibold text-white mb-4">Sessões</h2>

                        {sessions.length === 0 ? (
                            <div className="text-center text-gray-500 py-8">
                                <p className="text-4xl mb-2">📭</p>
                                <p>Nenhuma sessão ainda</p>
                                <p className="text-sm">Clique em &quot;Nova Sessão&quot; para começar</p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {sessions.map((session) => (
                                    <div
                                        key={session.id}
                                        onClick={() => handleSessionSelect(session.id)}
                                        className={`p-4 rounded-lg cursor-pointer transition-all ${selectedSessionId === session.id
                                            ? "bg-gray-700 border border-blue-500"
                                            : "bg-gray-900/50 border border-gray-700 hover:border-gray-600"
                                            }`}
                                    >
                                        <div className="flex justify-between items-start mb-2">
                                            <div>
                                                <span
                                                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${session.status === "running"
                                                        ? "bg-green-500/20 text-green-400"
                                                        : "bg-gray-500/20 text-gray-400"
                                                        }`}
                                                >
                                                    {session.status === "running" ? "● ATIVA" : "PARADA"}
                                                </span>
                                            </div>
                                            <span className="text-gray-500 text-xs">#{session.id}</span>
                                        </div>

                                        <h3 className="text-white font-medium">{session.strategy_slug}</h3>
                                        <p className="text-gray-400 text-sm">{session.coin}</p>

                                        <div className="flex justify-between items-center mt-3">
                                            <span className="text-gray-400 text-sm">
                                                {/* Mostrar Equity se tiver posição, senão saldo */}
                                                {session.has_position
                                                    ? <span title="Patrimônio (inclui posição)">{formatCurrency(session.equity || session.current_balance)} 📊</span>
                                                    : formatCurrency(session.current_balance)
                                                }
                                            </span>
                                            <span className={`font-medium ${getPnLColor(session.pnl)}`}>
                                                {session.pnl >= 0 ? "+" : ""}
                                                {formatCurrency(session.pnl)}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Session Details */}
                <div className="lg:col-span-2">
                    {selectedSession ? (
                        <div className="space-y-6">
                            {/* Session Header */}
                            <div className="bg-gradient-to-r from-gray-800/80 to-gray-800/50 border border-gray-700 rounded-xl p-6">
                                <div className="flex justify-between items-start mb-4">
                                    <div>
                                        <span
                                            className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${selectedSession.session.status === "running"
                                                ? "bg-green-500/20 text-green-400"
                                                : "bg-gray-500/20 text-gray-400"
                                                }`}
                                        >
                                            {selectedSession.session.status === "running" ? "● RODANDO" : "PARADA"}
                                        </span>
                                        <h2 className="text-xl font-bold text-white mt-2">
                                            {selectedSession.session.strategy_slug}
                                        </h2>
                                        <p className="text-gray-400">
                                            {selectedSession.session.coin} • {selectedSession.session.timeframe}
                                        </p>
                                    </div>

                                    <div className="flex gap-2">
                                        {selectedSession.session.status === "running" && (
                                            <button
                                                onClick={() => handleStopSession(selectedSession.session.id)}
                                                disabled={loading}
                                                className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-sm rounded-lg"
                                            >
                                                Parar
                                            </button>
                                        )}
                                        <button
                                            onClick={() => {
                                                if (selectedSession.session.status === "running") {
                                                    if (confirm("A sessão está rodando. Deseja forçar a deleção? Isso irá parar a sessão e remover todos os dados imediatamente.")) {
                                                        handleDeleteSession(selectedSession.session.id, true);
                                                    }
                                                } else {
                                                    if (confirm("Tem certeza que deseja deletar esta sessão?")) {
                                                        handleDeleteSession(selectedSession.session.id);
                                                    }
                                                }
                                            }}
                                            disabled={loading}
                                            className="px-3 py-1.5 bg-red-700 hover:bg-red-600 text-white text-sm rounded-lg"
                                        >
                                            Deletar
                                        </button>
                                        <button
                                            onClick={() => handleResetSession(selectedSession.session.id)}
                                            disabled={loading}
                                            className="px-3 py-1.5 bg-gray-600 hover:bg-gray-500 text-white text-sm rounded-lg"
                                        >
                                            Reset
                                        </button>
                                    </div>
                                </div>

                                {/* Balance Cards */}
                                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                    <div className="bg-black/30 rounded-lg p-3">
                                        <p className="text-gray-400 text-xs">Saldo Inicial</p>
                                        <p className="text-lg font-bold text-white">
                                            {formatCurrency(selectedSession.session.initial_balance)}
                                        </p>
                                    </div>
                                    <div className="bg-black/30 rounded-lg p-3">
                                        <p className="text-gray-400 text-xs">Saldo Disponível</p>
                                        <p className="text-lg font-bold text-white">
                                            {formatCurrency(selectedSession.session.current_balance)}
                                        </p>
                                    </div>
                                    <div className="bg-black/30 rounded-lg p-3">
                                        <p className="text-gray-400 text-xs">Posição</p>
                                        <p className="text-lg font-bold text-white">
                                            {selectedSession.metrics.position_amount ? selectedSession.metrics.position_amount.toFixed(4) : (selectedSession.position?.quantity?.toFixed(4) || "0.0000")} <span className="text-xs text-gray-500">{selectedSession.session.coin}</span>
                                        </p>
                                    </div>

                                    {/* Calculated Equity Card */}
                                    <div className="bg-black/30 rounded-lg p-3">
                                        <p className="text-gray-400 text-xs">Patrimônio (Equity)</p>
                                        <p className="text-lg font-bold text-white">
                                            {/* Equity = Cash + PositionValue */}
                                            {(() => {
                                                const cash = selectedSession.session.current_balance;
                                                const qty = selectedSession.position?.quantity || 0;
                                                const currentPrice = selectedSession.triggers?.current_price || (selectedSession.position?.current_price || 0);
                                                const equity = cash + (qty * currentPrice);
                                                return formatCurrency(equity);
                                            })()}
                                        </p>
                                    </div>

                                    {/* Global PnL Card */}
                                    <div className="bg-black/30 rounded-lg p-3">
                                        <p className="text-gray-400 text-xs">PnL Global</p>
                                        {(() => {
                                            const cash = selectedSession.session.current_balance;
                                            const qty = selectedSession.position?.quantity || 0;
                                            const currentPrice = selectedSession.triggers?.current_price || (selectedSession.position?.current_price || 0);
                                            const equity = cash + (qty * currentPrice);
                                            const initial = selectedSession.session.initial_balance;
                                            const pnl = equity - initial;
                                            const pnlPct = (pnl / initial) * 100;

                                            return (
                                                <p className={`text-lg font-bold ${getPnLColor(pnl)}`}>
                                                    {pnl >= 0 ? "+" : ""}
                                                    {formatCurrency(pnl)} ({pnlPct.toFixed(2)}%)
                                                </p>
                                            );
                                        })()}
                                    </div>
                                </div>

                                {/* Triggers Panel */}
                                {selectedSession.triggers && (
                                    <div className="mt-4 bg-purple-900/20 border border-purple-500/30 rounded-xl p-4">
                                        <h3 className="text-purple-400 font-semibold mb-3 flex items-center gap-2">
                                            Gatilhos da Estratégia
                                            {selectedSession.triggers.status === "collecting" && (
                                                <span className="text-xs text-gray-400 font-normal">
                                                    ({selectedSession.triggers.message})
                                                </span>
                                            )}
                                        </h3>

                                        {selectedSession.triggers.status === "ready" && (
                                            <div className="grid md:grid-cols-2 gap-4">
                                                {/* Buy Triggers */}
                                                <div className="space-y-2">
                                                    <p className="text-green-400 text-sm font-medium">Compra</p>
                                                    {selectedSession.triggers.buy_rules.length === 0 ? (
                                                        <p className="text-gray-500 text-xs">Nenhuma regra</p>
                                                    ) : (
                                                        selectedSession.triggers.buy_rules.map((rule, idx) => (
                                                            <div
                                                                key={idx}
                                                                className={`p-2 rounded-lg border text-xs ${rule.active
                                                                    ? "bg-green-900/40 border-green-500/50"
                                                                    : "bg-gray-800/50 border-gray-700"
                                                                    }`}
                                                            >
                                                                <div className="flex justify-between items-center">
                                                                    <span className="text-gray-300">{rule.indicator}</span>
                                                                    <span className={rule.active ? "text-green-400 font-bold" : "text-gray-400"}>
                                                                        {rule.active ? "✓ ATIVO" : "Aguardando"}
                                                                    </span>
                                                                </div>
                                                                <div className="mt-1 flex justify-between text-gray-400">
                                                                    <span>Atual: <strong className="text-white">{rule.current}</strong></span>
                                                                    <span>{rule.operator} {rule.threshold}</span>
                                                                </div>
                                                            </div>
                                                        ))
                                                    )}
                                                </div>

                                                {/* Sell Triggers */}
                                                <div className="space-y-2">
                                                    <p className="text-red-400 text-sm font-medium">Venda</p>
                                                    {selectedSession.triggers.sell_rules.length === 0 ? (
                                                        <p className="text-gray-500 text-xs">Nenhuma regra</p>
                                                    ) : (
                                                        selectedSession.triggers.sell_rules.map((rule, idx) => (
                                                            <div
                                                                key={idx}
                                                                className={`p-2 rounded-lg border text-xs ${rule.active
                                                                    ? "bg-red-900/40 border-red-500/50"
                                                                    : "bg-gray-800/50 border-gray-700"
                                                                    }`}
                                                            >
                                                                <div className="flex justify-between items-center">
                                                                    <span className="text-gray-300">{rule.indicator}</span>
                                                                    <span className={rule.active ? "text-red-400 font-bold" : "text-gray-400"}>
                                                                        {rule.active ? "✓ ATIVO" : "Aguardando"}
                                                                    </span>
                                                                </div>
                                                                <div className="mt-1 flex justify-between text-gray-400">
                                                                    <span>Atual: <strong className="text-white">{rule.current}</strong></span>
                                                                    <span>{rule.operator} {rule.threshold}</span>
                                                                </div>
                                                            </div>
                                                        ))
                                                    )}
                                                </div>
                                            </div>
                                        )}

                                        {selectedSession.triggers.current_price && (
                                            <p className="mt-3 text-center text-gray-400 text-xs">
                                                Preço atual: <strong className="text-white">${selectedSession.triggers.current_price}</strong>
                                            </p>
                                        )}
                                    </div>
                                )}

                                {/* Candlestick Chart */}
                                {selectedSession.price_history && selectedSession.price_history.length > 1 && (
                                    <InteractiveChart data={selectedSession.price_history} />
                                )}

                                {/* Deposit/Withdraw Buttons */}
                                <div className="flex gap-3 mt-4">
                                    <button
                                        onClick={() =>
                                            setTransactionModal({ type: "deposit", sessionId: selectedSession.session.id })
                                        }
                                        className="flex-1 px-4 py-2 bg-green-900/50 hover:bg-green-900/70 border border-green-500/30 text-green-400 rounded-lg"
                                    >
                                        Depositar
                                    </button>
                                    <button
                                        onClick={() =>
                                            setTransactionModal({ type: "withdrawal", sessionId: selectedSession.session.id })
                                        }
                                        className="flex-1 px-4 py-2 bg-red-900/50 hover:bg-red-900/70 border border-red-500/30 text-red-400 rounded-lg"
                                    >
                                        Sacar
                                    </button>
                                </div>
                            </div>

                            {/* Position */}
                            {selectedSession.position && (
                                <div className="bg-blue-900/20 border border-blue-500/30 rounded-xl p-4">
                                    <h3 className="text-blue-400 font-semibold mb-3">Posição Aberta</h3>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <div>
                                            <p className="text-gray-400 text-xs">Lado</p>
                                            <p className="text-white font-medium">{selectedSession.position.side}</p>
                                        </div>
                                        <div>
                                            <p className="text-gray-400 text-xs">Entrada</p>
                                            <p className="text-white font-medium">
                                                ${selectedSession.position.entry_price.toFixed(4)}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-gray-400 text-xs">Atual</p>
                                            <p className="text-white font-medium">
                                                ${selectedSession.position.current_price.toFixed(4)}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-gray-400 text-xs">PnL Não Realizado</p>
                                            <p
                                                className={`font-medium ${getPnLColor(
                                                    selectedSession.position.unrealized_pnl
                                                )}`}
                                            >
                                                {formatCurrency(selectedSession.position.unrealized_pnl)}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Recent Trades */}
                            <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
                                <h3 className="text-white font-semibold mb-3">📈 Trades Recentes</h3>

                                {selectedSession.recent_trades.length === 0 ? (
                                    <p className="text-gray-500 text-center py-4">Nenhum trade ainda</p>
                                ) : (
                                    <div className="overflow-x-auto">
                                        <table className="w-full">
                                            <thead>
                                                <tr className="text-gray-400 text-xs border-b border-gray-700">
                                                    <th className="text-left py-2">Lado</th>
                                                    <th className="text-right py-2">Preço</th>
                                                    <th className="text-right py-2">Qtd</th>
                                                    <th className="text-right py-2">Valor</th>
                                                    <th className="text-right py-2">Taxas</th>
                                                    <th className="text-right py-2">PnL</th>
                                                    <th className="text-right py-2">Data</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {selectedSession.recent_trades.map((trade) => (
                                                    <tr key={trade.id} className="border-b border-gray-800">
                                                        <td className="py-2">
                                                            <span
                                                                className={`${trade.side === "BUY" ? "text-green-400" : "text-red-400"
                                                                    }`}
                                                            >
                                                                {trade.side === "BUY" ? "🟢" : "🔴"} {trade.side}
                                                            </span>
                                                        </td>
                                                        <td className="text-right text-gray-300">
                                                            ${trade.price.toFixed(4)}
                                                        </td>
                                                        <td className="text-right text-gray-300">
                                                            {trade.quantity.toFixed(6)}
                                                        </td>
                                                        <td className="text-right text-gray-300">
                                                            {formatCurrency(trade.value)}
                                                        </td>
                                                        <td className="text-right text-amber-500/80">
                                                            {formatCurrency(trade.fee || 0)}
                                                        </td>
                                                        <td className="text-right">
                                                            {trade.pnl !== null ? (
                                                                <span className={getPnLColor(trade.pnl)}>
                                                                    {formatCurrency(trade.pnl)}
                                                                </span>
                                                            ) : (
                                                                <span className="text-gray-500">-</span>
                                                            )}
                                                        </td>
                                                        <td className="text-right text-gray-500 text-xs">
                                                            {formatDate(trade.executed_at)}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>

                            {/* Recent Transactions */}
                            {selectedSession.recent_transactions.length > 0 && (
                                <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
                                    <h3 className="text-white font-semibold mb-3">💳 Transações</h3>
                                    <div className="space-y-2">
                                        {selectedSession.recent_transactions.map((tx) => (
                                            <div
                                                key={tx.id}
                                                className="flex justify-between items-center p-3 bg-gray-900/50 rounded-lg"
                                            >
                                                <div>
                                                    <span
                                                        className={`${tx.type === "deposit" ? "text-green-400" : "text-red-400"
                                                            }`}
                                                    >
                                                        {tx.type === "deposit" ? "⬆️ Depósito" : "⬇️ Saque"}
                                                    </span>
                                                    {tx.note && (
                                                        <p className="text-gray-500 text-xs mt-1">{tx.note}</p>
                                                    )}
                                                </div>
                                                <div className="text-right">
                                                    <p
                                                        className={`font-medium ${tx.type === "deposit" ? "text-green-400" : "text-red-400"
                                                            }`}
                                                    >
                                                        {tx.type === "deposit" ? "+" : "-"}
                                                        {formatCurrency(tx.amount)}
                                                    </p>
                                                    <p className="text-gray-500 text-xs">
                                                        {formatDate(tx.created_at)}
                                                    </p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-12 text-center">
                            <p className="text-4xl mb-4">👈</p>
                            <p className="text-gray-400">Selecione uma sessão para ver os detalhes</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Transaction Modal */}
            {transactionModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 w-full max-w-md mx-4">
                        <h3 className="text-xl font-bold text-white mb-4">
                            {transactionModal.type === "deposit" ? "💰 Depositar" : "🏦 Sacar"}
                        </h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-gray-400 text-sm mb-2">Valor (USDT)</label>
                                <input
                                    type="number"
                                    value={transactionAmount}
                                    onChange={(e) => setTransactionAmount(e.target.value)}
                                    placeholder="0.00"
                                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white text-lg"
                                    autoFocus
                                />
                            </div>

                            <div>
                                <label className="block text-gray-400 text-sm mb-2">
                                    Nota <span className="text-gray-500">(opcional)</span>
                                </label>
                                <input
                                    type="text"
                                    value={transactionNote}
                                    onChange={(e) => setTransactionNote(e.target.value)}
                                    placeholder="Ex: Aporte mensal"
                                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white"
                                />
                            </div>
                        </div>

                        <div className="flex gap-3 mt-6">
                            <button
                                onClick={handleTransaction}
                                disabled={loading || !transactionAmount}
                                className={`flex-1 py-2 font-medium rounded-lg disabled:opacity-50 ${transactionModal.type === "deposit"
                                    ? "bg-green-600 hover:bg-green-500 text-white"
                                    : "bg-red-600 hover:bg-red-500 text-white"
                                    }`}
                            >
                                {loading ? "⏳ Processando..." : "Confirmar"}
                            </button>
                            <button
                                onClick={() => {
                                    setTransactionModal(null);
                                    setTransactionAmount("");
                                    setTransactionNote("");
                                }}
                                className="flex-1 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg"
                            >
                                Cancelar
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Info Box */}
            <div className="mt-6 bg-blue-900/20 border border-blue-500/30 rounded-xl p-4">
                <h3 className="text-blue-400 font-semibold mb-2">ℹ️ Como funciona?</h3>
                <ul className="text-gray-300 text-sm space-y-1">
                    <li>• O Paper Trading simula ordens usando preços reais da Binance</li>
                    <li>• Nenhum dinheiro real é envolvido - é apenas simulação</li>
                    <li>• A estratégia é executada automaticamente quando novos candles fecham</li>
                    <li>• Você pode rodar múltiplas sessões simultaneamente</li>
                    <li>• Configure notificações Telegram para receber alertas de trades</li>
                </ul>
            </div>
        </div>
    );
}
