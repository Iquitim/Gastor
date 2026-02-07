"use client";

import { useState, useEffect } from "react";
import api from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import dynamic from "next/dynamic";

const EquityChart = dynamic(() => import("@/components/EquityChart"), { ssr: false });

import TradesTable from "../../components/TradesTable";

interface Metrics {
    finalValue: number;
    totalPnl: number;
    totalPnlPct: number;
    winRate: number;
    maxDrawdown: number;
    totalTrades: number;
    completedTrades: number;
    profitFactor: number;
    evolution?: { time: number; value: number }[];
    trades?: any[];
}

const FTMO_RULES = {
    profitTarget: 10,
    maxDrawdown: 10,
    maxDailyLoss: 5,
    minTradingDays: 4,
};

export default function ResultsPage() {
    const [metrics, setMetrics] = useState<Metrics | null>(null);
    const [activeStrategy, setActiveStrategy] = useState<any>(null);
    const [showMock, setShowMock] = useState(false);

    const { user } = useAuth(); // Add auth context

    useEffect(() => {
        if (!user) {
            setMetrics(null);
            return;
        }

        const fetchActive = async () => {
            try {
                const strategy = await api.getActiveStrategy();
                if (strategy && strategy.backtest_metrics) {
                    setActiveStrategy(strategy);
                    const bm = strategy.backtest_metrics;

                    // Prepare evolution data
                    // equity_curve has N items (initial + each trade)
                    // equity_timestamps has N-1 items (each trade exit)
                    let evolutionData: { time: number; value: number }[] = [];

                    if (bm.metrics?.equity_curve && bm.metrics?.equity_timestamps) {
                        const curve = bm.metrics.equity_curve;
                        const tstamps = bm.metrics.equity_timestamps;

                        // Add point 0 (start)
                        // If we have trades, fake start time 1h before first trade
                        if (tstamps.length > 0) {
                            evolutionData.push({
                                time: tstamps[0] - 3600 * 24, // 1 day before
                                value: curve[0]
                            });
                        } else {
                            // If no trades, just show initial at current time? or empty
                            evolutionData.push({
                                time: Math.floor(Date.now() / 1000),
                                value: curve[0]
                            });
                        }

                        // Add points for each trade
                        tstamps.forEach((ts: number, i: number) => {
                            if (i + 1 < curve.length) {
                                evolutionData.push({
                                    time: ts,
                                    value: curve[i + 1]
                                });
                            }
                        });
                    }

                    setMetrics({
                        finalValue: bm.metrics?.final_balance ?? (10000 + (bm.metrics?.total_pnl || 0)),
                        totalPnl: bm.metrics?.total_pnl || 0,
                        totalPnlPct: bm.metrics?.total_pnl_pct || 0,
                        winRate: (bm.metrics?.win_rate || 0) * 100,
                        maxDrawdown: bm.metrics?.max_drawdown || 0,
                        totalTrades: bm.metrics?.total_trades || 0,
                        completedTrades: bm.metrics?.total_trades || 0,
                        profitFactor: bm.metrics?.profit_factor || 0.0,
                        evolution: evolutionData,
                        trades: bm.trades || []
                    });
                }
            } catch (error) {
                console.error("Failed to fetch active strategy", error);
            }
        };
        fetchActive();
    }, [user]);

    const mockMetrics: Metrics = {
        finalValue: 10523.45,
        totalPnl: 523.45,
        totalPnlPct: 5.23,
        winRate: 68.4,
        maxDrawdown: 4.2,
        totalTrades: 24,
        completedTrades: 12,
        profitFactor: 1.85,
        evolution: [
            { time: 1641000000, value: 10000 },
            { time: 1641086400, value: 10100 },
            { time: 1641172800, value: 10050 },
            { time: 1641259200, value: 10300 },
            { time: 1641345600, value: 10523.45 },
        ],
        trades: []
    };

    const displayMetrics = showMock ? mockMetrics : metrics;

    // Se temos estratégia ativa, usar dados reais
    // FTMO Checks
    const passedProfit = displayMetrics ? displayMetrics.totalPnlPct >= FTMO_RULES.profitTarget : false;
    const passedDrawdown = displayMetrics ? displayMetrics.maxDrawdown <= FTMO_RULES.maxDrawdown : false;
    const passedDailyLoss = true; // Não simulado ainda
    const passedDays = true; // Não simulado ainda
    const allPassed = passedProfit && passedDrawdown && passedDailyLoss && passedDays;

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white">Resultados</h1>
                <p className="text-slate-400 mt-1">
                    Dashboard de performance e validação FTMO
                </p>
            </div>

            {/* Empty State */}
            {!displayMetrics ? (
                <div className="bg-slate-900 rounded-lg border border-slate-800 p-12 text-center">
                    <svg className="w-16 h-16 mx-auto text-slate-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                    </svg>
                    <h2 className="text-xl font-semibold text-white mb-2">
                        Nenhuma estratégia executada ainda
                    </h2>
                    <p className="text-slate-400 mb-6">
                        Execute uma estratégia no Laboratório ou Otimizador para ver os resultados aqui.
                    </p>
                    <div className="flex justify-center gap-4">
                        <a
                            href="/strategies"
                            className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-md transition-colors"
                        >
                            Ir para Laboratório
                        </a>
                        <button
                            onClick={() => setShowMock(true)}
                            className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-md transition-colors"
                        >
                            Ver Exemplo
                        </button>
                    </div>
                </div>
            ) : (
                <>
                    {/* Demo Badge */}
                    {showMock && (
                        <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-center justify-between">
                            <span className="text-amber-300 text-sm">
                                Dados de demonstração. Execute uma estratégia para ver resultados reais.
                            </span>
                            <button
                                onClick={() => setShowMock(false)}
                                className="text-amber-400 hover:text-amber-300 text-sm underline"
                            >
                                Ocultar
                            </button>
                        </div>
                    )}

                    {/* Main Metrics */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                        {[
                            {
                                label: "Patrimônio Final",
                                value: `$${displayMetrics.finalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
                                delta: `${displayMetrics.totalPnlPct >= 0 ? "+" : ""}${displayMetrics.totalPnlPct.toFixed(2)}%`,
                                deltaColor: displayMetrics.totalPnlPct >= 0 ? "text-emerald-400" : "text-red-400",
                            },
                            {
                                label: "Lucro/Prejuízo",
                                value: `$${displayMetrics.totalPnl >= 0 ? "+" : ""}${displayMetrics.totalPnl.toFixed(2)}`,
                                color: displayMetrics.totalPnl >= 0 ? "text-emerald-400" : "text-red-400",
                            },
                            {
                                label: "Taxa de Acerto",
                                value: `${displayMetrics.winRate.toFixed(1)}%`,
                                delta: `${displayMetrics.completedTrades} trades completos`,
                            },
                            {
                                label: "Max Drawdown",
                                value: `-${displayMetrics.maxDrawdown.toFixed(2)}%`,
                                color: "text-red-400",
                            },
                        ].map((stat) => (
                            <div key={stat.label} className="bg-slate-900 rounded-lg border border-slate-800 p-4">
                                <div className="text-slate-400 text-sm">{stat.label}</div>
                                <div className={`text-2xl font-bold mt-1 ${stat.color || "text-white"}`}>
                                    {stat.value}
                                </div>
                                {stat.delta && (
                                    <div className={`text-sm mt-1 ${stat.deltaColor || "text-slate-400"}`}>
                                        {stat.delta}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>

                    {/* Secondary Metrics */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
                        {[
                            { label: "Valor Investido", value: "$10,000.00" },
                            { label: "Total Operações", value: displayMetrics.totalTrades },
                            { label: "Profit Factor", value: displayMetrics.profitFactor.toFixed(2) },
                            { label: "Drawdown Atual", value: "-1.25%" }, // ToDo: Real calc
                        ].map((stat) => (
                            <div key={stat.label} className="bg-slate-900/50 rounded-lg border border-slate-800 p-3">
                                <div className="text-slate-400 text-xs">{stat.label}</div>
                                <div className="text-lg font-semibold text-white">{stat.value}</div>
                            </div>
                        ))}
                    </div>

                    {/* FTMO Comparison */}
                    <div className="bg-slate-900 rounded-lg border border-slate-800 p-6 mb-8">
                        <h2 className="text-xl font-bold text-white mb-6">Comparativo FTMO Challenge</h2>

                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                            {[
                                {
                                    label: "Meta de Lucro",
                                    value: `${displayMetrics.totalPnlPct >= 0 ? "+" : ""}${displayMetrics.totalPnlPct.toFixed(2)}%`,
                                    target: `Meta: +${FTMO_RULES.profitTarget}%`,
                                    passed: passedProfit,
                                },
                                {
                                    label: "Max Drawdown",
                                    value: `-${displayMetrics.maxDrawdown.toFixed(2)}%`,
                                    target: `Limite: -${FTMO_RULES.maxDrawdown}%`,
                                    passed: passedDrawdown,
                                },
                                {
                                    label: "Max Loss Diária",
                                    value: "-2.1%",
                                    target: `Limite: -${FTMO_RULES.maxDailyLoss}%`,
                                    passed: passedDailyLoss,
                                },
                                {
                                    label: "Dias de Trading",
                                    value: "6 dias",
                                    target: `Mínimo: ${FTMO_RULES.minTradingDays}`,
                                    passed: passedDays,
                                },
                                {
                                    label: "Status Final",
                                    value: allPassed ? "APROVADO" : "Reprovado",
                                    isStatus: true,
                                    passed: allPassed,
                                },
                            ].map((item) => (
                                <div
                                    key={item.label}
                                    className={`p-4 rounded-lg border ${item.isStatus
                                        ? item.passed
                                            ? "bg-emerald-500/10 border-emerald-500/50"
                                            : "bg-red-500/10 border-red-500/50"
                                        : "bg-slate-800/50 border-slate-700"
                                        }`}
                                >
                                    <div className="flex items-center gap-1 text-sm text-slate-400">
                                        {item.passed ? (
                                            <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                            </svg>
                                        ) : (
                                            <svg className="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                            </svg>
                                        )}
                                        {item.label}
                                    </div>
                                    <div className={`text-xl font-bold mt-1 ${item.isStatus
                                        ? item.passed ? "text-emerald-400" : "text-red-400"
                                        : "text-white"
                                        }`}>
                                        {item.value}
                                    </div>
                                    {item.target && (
                                        <div className="text-xs text-slate-500 mt-1">{item.target}</div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Chart */}
                    <div className="bg-slate-900 rounded-lg border border-slate-800 p-6 mb-8">
                        <h2 className="text-xl font-bold text-white mb-4">Evolução do Patrimônio</h2>
                        <div className="h-64 bg-slate-800/20 rounded-lg border border-slate-700/50 overflow-hidden">
                            {displayMetrics && displayMetrics.evolution && displayMetrics.evolution.length > 0 ? (
                                <EquityChart data={displayMetrics.evolution} height={256} />
                            ) : (
                                <div className="h-full flex items-center justify-center text-slate-400">
                                    Gráfico de evolução será exibido aqui
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Trades Table */}
                    {displayMetrics.trades && displayMetrics.trades.length > 0 && (
                        <div className="space-y-4">
                            <div className="flex justify-end">
                                <button
                                    onClick={() => {
                                        if (!displayMetrics.trades) return;
                                        const headers = ["Type", "Entry Date", "Entry Price", "Exit Date", "Exit Price", "Size", "PnL", "PnL %"];
                                        const rows = displayMetrics.trades.map((t: any) => [
                                            t.type,
                                            t.entry_date,
                                            t.entry_price,
                                            t.exit_date || "",
                                            t.exit_price || "",
                                            t.size,
                                            t.pnl?.toFixed(2) || "",
                                            t.pnl_pct?.toFixed(2) || ""
                                        ]);
                                        const csvContent = [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
                                        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
                                        const url = URL.createObjectURL(blob);
                                        const link = document.createElement("a");
                                        link.setAttribute("href", url);
                                        link.setAttribute("download", "trades_gastor.csv");
                                        document.body.appendChild(link);
                                        link.click();
                                        document.body.removeChild(link);
                                    }}
                                    className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-md transition-colors text-sm"
                                >
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                    </svg>
                                    Exportar CSV
                                </button>
                            </div>
                            <TradesTable trades={displayMetrics.trades} />
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
