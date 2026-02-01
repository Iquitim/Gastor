"use client";

import { useState, useEffect, useCallback } from "react";
import { useData } from "../../context/DataContext";
import api from "../../lib/api";
import NoDataBanner from "../../components/NoDataBanner";
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
    };
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
}

interface Strategy {
    slug: string;
    name: string;
    icon: string;
    category: string;
}

export default function LiveTradingPage() {
    const { hasData, dataInfo } = useData();

    // State
    const [sessions, setSessions] = useState<Session[]>([]);
    const [selectedSession, setSelectedSession] = useState<SessionDetails | null>(null);
    const [strategies, setStrategies] = useState<Strategy[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Form state
    const [selectedStrategy, setSelectedStrategy] = useState("");
    const [telegramChatId, setTelegramChatId] = useState("");
    const [showNewSessionForm, setShowNewSessionForm] = useState(false);

    // Transaction modal
    const [transactionModal, setTransactionModal] = useState<{
        type: "deposit" | "withdrawal";
        sessionId: number;
    } | null>(null);
    const [transactionAmount, setTransactionAmount] = useState("");
    const [transactionNote, setTransactionNote] = useState("");

    // Load data
    const loadSessions = useCallback(async () => {
        try {
            const data = await api.getLiveSessions() as Session[];
            setSessions(data);
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
            setSelectedSession(data);
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
        if (selectedSession?.session.status === "running") {
            const interval = setInterval(() => {
                loadSessionDetails(selectedSession.session.id);
            }, 3000);
            return () => clearInterval(interval);
        }
    }, [selectedSession, loadSessionDetails]);

    // Handlers
    const handleStartSession = async () => {
        if (!selectedStrategy || !dataInfo) {
            setError("Selecione uma estratégia");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const settings = getStoredSettings();

            await api.startLiveSession({
                strategy_slug: selectedStrategy,
                coin: dataInfo.coin,
                timeframe: dataInfo.timeframe,
                initial_balance: settings.initialBalance,
                telegram_chat_id: telegramChatId || undefined,
            });

            await loadSessions();
            setShowNewSessionForm(false);
            setSelectedStrategy("");
            setTelegramChatId("");
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

    const handleDeleteSession = async (sessionId: number) => {
        if (!confirm("Tem certeza? Esta ação é irreversível.")) return;

        setLoading(true);
        try {
            await api.deleteLiveSession(sessionId);
            await loadSessions();
            if (selectedSession?.session.id === sessionId) {
                setSelectedSession(null);
            }
        } catch (e: unknown) {
            const errorMessage = e instanceof Error ? e.message : "Erro ao deletar sessão";
            setError(errorMessage);
        } finally {
            setLoading(false);
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

    if (!hasData) {
        return <NoDataBanner pageName="Paper Trading" />;
    }

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
                        <div>
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

                        {/* Telegram */}
                        <div>
                            <label className="block text-gray-400 text-sm mb-2">
                                Telegram Chat ID <span className="text-gray-500">(opcional)</span>
                            </label>
                            <input
                                type="text"
                                value={telegramChatId}
                                onChange={(e) => setTelegramChatId(e.target.value)}
                                placeholder="Ex: 123456789"
                                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white"
                            />
                        </div>
                    </div>

                    <div className="mt-4 p-3 bg-blue-900/20 border border-blue-500/30 rounded-lg">
                        <p className="text-blue-400 text-sm">
                            📍 Par: <strong>{dataInfo?.coin}</strong> | Timeframe: <strong>{dataInfo?.timeframe}</strong>
                        </p>
                        <p className="text-blue-300 text-xs mt-1">
                            Saldo inicial será carregado das configurações (Settings)
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
                                        onClick={() => loadSessionDetails(session.id)}
                                        className={`p-4 rounded-lg cursor-pointer transition-all ${selectedSession?.session.id === session.id
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
                                                {formatCurrency(session.current_balance)}
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
                                        {selectedSession.session.status === "running" ? (
                                            <button
                                                onClick={() => handleStopSession(selectedSession.session.id)}
                                                disabled={loading}
                                                className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white text-sm rounded-lg"
                                            >
                                                ⏹️ Parar
                                            </button>
                                        ) : (
                                            <button
                                                onClick={() => handleDeleteSession(selectedSession.session.id)}
                                                disabled={loading}
                                                className="px-3 py-1.5 bg-red-900 hover:bg-red-800 text-white text-sm rounded-lg"
                                            >
                                                🗑️ Deletar
                                            </button>
                                        )}
                                        <button
                                            onClick={() => handleResetSession(selectedSession.session.id)}
                                            disabled={loading}
                                            className="px-3 py-1.5 bg-yellow-600 hover:bg-yellow-500 text-white text-sm rounded-lg"
                                        >
                                            🔄 Reset
                                        </button>
                                    </div>
                                </div>

                                {/* Balance Cards */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <div className="bg-black/30 rounded-lg p-3">
                                        <p className="text-gray-400 text-xs">Saldo Inicial</p>
                                        <p className="text-lg font-bold text-white">
                                            {formatCurrency(selectedSession.session.initial_balance)}
                                        </p>
                                    </div>
                                    <div className="bg-black/30 rounded-lg p-3">
                                        <p className="text-gray-400 text-xs">Saldo Atual</p>
                                        <p className="text-lg font-bold text-white">
                                            {formatCurrency(selectedSession.session.current_balance)}
                                        </p>
                                    </div>
                                    <div className="bg-black/30 rounded-lg p-3">
                                        <p className="text-gray-400 text-xs">PnL Total</p>
                                        <p className={`text-lg font-bold ${getPnLColor(selectedSession.session.pnl)}`}>
                                            {selectedSession.session.pnl >= 0 ? "+" : ""}
                                            {formatCurrency(selectedSession.session.pnl)} ({selectedSession.session.pnl_pct.toFixed(2)}%)
                                        </p>
                                    </div>
                                    <div className="bg-black/30 rounded-lg p-3">
                                        <p className="text-gray-400 text-xs">Win Rate</p>
                                        <p className="text-lg font-bold text-white">
                                            {selectedSession.metrics.win_rate.toFixed(1)}%
                                        </p>
                                    </div>
                                </div>

                                {/* Deposit/Withdraw Buttons */}
                                <div className="flex gap-3 mt-4">
                                    <button
                                        onClick={() =>
                                            setTransactionModal({ type: "deposit", sessionId: selectedSession.session.id })
                                        }
                                        className="flex-1 px-4 py-2 bg-green-900/50 hover:bg-green-900/70 border border-green-500/30 text-green-400 rounded-lg"
                                    >
                                        💰 Depositar
                                    </button>
                                    <button
                                        onClick={() =>
                                            setTransactionModal({ type: "withdrawal", sessionId: selectedSession.session.id })
                                        }
                                        className="flex-1 px-4 py-2 bg-red-900/50 hover:bg-red-900/70 border border-red-500/30 text-red-400 rounded-lg"
                                    >
                                        🏦 Sacar
                                    </button>
                                </div>
                            </div>

                            {/* Position */}
                            {selectedSession.position && (
                                <div className="bg-blue-900/20 border border-blue-500/30 rounded-xl p-4">
                                    <h3 className="text-blue-400 font-semibold mb-3">📊 Posição Aberta</h3>
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
