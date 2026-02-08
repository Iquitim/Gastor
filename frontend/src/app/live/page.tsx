"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import api from "../../lib/api";
import { getStoredSettings } from "../../lib/settings";

// Imported Features
import { Session, SessionDetails as SessionDetailsType, Strategy } from "../../features/live/types";
import SessionList from "../../features/live/SessionList";
import NewSessionForm from "../../features/live/NewSessionForm";
import SessionDetails from "../../features/live/SessionDetails";

export default function LiveTradingPage() {

    // State
    const [sessions, setSessions] = useState<Session[]>([]);
    const [selectedSession, setSelectedSession] = useState<SessionDetailsType | null>(null);
    const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);
    const selectedSessionIdRef = useRef<number | null>(null); // To avoid race conditions
    const deletedSessionIds = useRef<Set<number>>(new Set()); // To avoid polling bringing back deleted sessions

    const [strategies, setStrategies] = useState<Strategy[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Settings State (Synced with API & LocalStorage)
    const [settings, setSettings] = useState(getStoredSettings());

    // Form state
    const [selectedStrategy, setSelectedStrategy] = useState("");
    const [selectedSlot, setSelectedSlot] = useState(1); // Default Slot 1
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
            const data = await api.getLiveSession(sessionId) as SessionDetailsType;

            // Check for race condition
            if (selectedSessionIdRef.current === sessionId) {
                setSelectedSession(data);
            }
        } catch (e) {
            console.error("Failed to load session details", e);
        }
    }, []);

    // Load Settings on Mount (Ensure freshness)
    useEffect(() => {
        const syncSettings = async () => {
            try {
                const config = await api.getUserConfig();
                const telegram = await api.getTelegramConfig().catch(() => ({ chat_id: "" })); // Fail safe

                const newSettings = {
                    initialBalance: config.backtest_initial_balance,
                    useCompound: config.backtest_use_compound,
                    paperTradingBalance: config.paper_initial_balance,
                    paperTradingCoin: config.paper_default_coin,
                    paperTradingTimeframe: config.paper_default_timeframe,
                    telegramChatId: telegram.chat_id || "",
                    exchangeFee: config.exchange_fee,
                    slippageOverrides: config.slippage_overrides
                };

                // Update LocalStorage
                localStorage.setItem("gastor_settings", JSON.stringify(newSettings));

                // Update State
                setSettings(newSettings);
            } catch (e) {
                console.error("Failed to sync settings", e);
            }
        };

        syncSettings();
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
            await api.startLiveSession({
                strategy_slug: selectedStrategy,
                coin: settings.paperTradingCoin,
                timeframe: settings.paperTradingTimeframe,
                initial_balance: settings.paperTradingBalance,
                telegram_chat_id: settings.telegramChatId || undefined,
                slot: selectedSlot,
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
        // Add to ignored list immediately to prevent polling from bringing it back
        deletedSessionIds.current.add(sessionId);

        // Feedback imediato - remove da UI antes da API responder
        if (selectedSession?.session.id === sessionId) {
            setSelectedSession(null);
            setSelectedSessionId(null);
        }
        setSessions(prev => prev.filter(s => s.id !== sessionId));

        try {
            await api.deleteLiveSession(sessionId, force);
        } catch (e: unknown) {
            const errorMessage = e instanceof Error ? e.message : "Erro ao deletar sessão";
            setError(errorMessage);
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
                <NewSessionForm
                    strategies={strategies}
                    sessions={sessions}
                    settings={settings}
                    selectedStrategy={selectedStrategy}
                    selectedSlot={selectedSlot}
                    loading={loading}
                    onStrategyChange={setSelectedStrategy}
                    onSlotChange={setSelectedSlot}
                    onStart={handleStartSession}
                    onCancel={() => setShowNewSessionForm(false)}
                />
            )}

            <div className="grid lg:grid-cols-3 gap-6">
                {/* Sessions List */}
                <div className="lg:col-span-1">
                    <SessionList
                        sessions={sessions}
                        selectedSessionId={selectedSessionId}
                        onSessionSelect={handleSessionSelect}
                        formatCurrency={formatCurrency}
                        getPnLColor={getPnLColor}
                    />
                </div>

                {/* Session Details */}
                <div className="lg:col-span-2">
                    <SessionDetails
                        selectedSession={selectedSession}
                        loading={loading}
                        formatCurrency={formatCurrency}
                        formatDate={formatDate}
                        getPnLColor={getPnLColor}
                        onStopSession={handleStopSession}
                        onDeleteSession={handleDeleteSession}
                        onResetSession={handleResetSession}
                        onTransaction={(type, sessionId) => setTransactionModal({ type, sessionId })}
                    />
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
        </div>
    );
}
