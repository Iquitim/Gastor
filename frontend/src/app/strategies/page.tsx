"use client";

import { useState, useEffect } from "react";
import StrategyCard from "@/components/StrategyCard";
import LinkedText from "@/components/LinkedText";
import NoDataBanner from "@/components/NoDataBanner";
import dynamic from "next/dynamic";
import { STRATEGIES as DEFAULT_STRATEGIES, CATEGORIES, Strategy } from "@/lib/strategies";
import { useData } from "@/context/DataContext";
import api from "@/lib/api";
import TradesTable from "@/components/TradesTable";
import { getStoredSettings } from "@/lib/settings";

const Chart = dynamic(() => import("@/components/Chart"), { ssr: false });

interface StrategyResults {
    trades: number;
    pnl: string;
    winRate: string;
    maxDD: string;
}

export default function StrategiesPage() {
    const { hasData, dataInfo, chartData } = useData();
    const [selectedCategory, setSelectedCategory] = useState("all");
    const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
    const [isRunning, setIsRunning] = useState(false);
    const [results, setResults] = useState<StrategyResults | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [currentParams, setCurrentParams] = useState<Record<string, any>>({});
    const [trades, setTrades] = useState<any[]>([]);
    const [fullTrades, setFullTrades] = useState<any[]>([]); // Table trades
    const [rawResult, setRawResult] = useState<any>(null); // Raw backtest result for 'Apply'
    const [includeFees, setIncludeFees] = useState(true);

    const [strategies, setStrategies] = useState<Strategy[]>([]);
    const [isLoadingStrategies, setIsLoadingStrategies] = useState(true);

    // Load Strategies from API
    useEffect(() => {
        const load = async () => {
            try {
                const list = await api.listStrategies();
                const mapped = list.map(s => ({
                    ...s,
                    category: s.category as any,
                    idealFor: s.idealFor || "Personalizada",
                    parameters: s.parameters || {}
                }));
                setStrategies(mapped);
            } catch (e) {
                console.error("Failed to load strategies", e);
                setStrategies(DEFAULT_STRATEGIES); // Fallback
            } finally {
                setIsLoadingStrategies(false);
            }
        };
        load();
    }, []);

    const filteredStrategies = strategies.filter(s =>
        selectedCategory === "all" ? true : s.category === selectedCategory
    );
    const selectedStrategyData = strategies.find(s => s.slug === selectedStrategy);

    // Initialize params when strategy changes
    useEffect(() => {
        if (selectedStrategyData) {
            const initialParams: Record<string, any> = ({});
            Object.entries(selectedStrategyData.parameters).forEach(([key, param]) => {
                initialParams[key] = param.default;
            });
            setCurrentParams(initialParams);
        } else {
            setCurrentParams({});
        }
    }, [selectedStrategy]);

    const handleRunStrategy = async () => {
        if (!selectedStrategy || !hasData || !dataInfo) return;

        // Settings helper
        const { customFee, initialBalance: customBalance, useCompound } = getStoredSettings(dataInfo.coin);

        setIsRunning(true);
        setError(null);
        setResults(null);
        setTrades([]);
        setFullTrades([]);
        setRawResult(null);

        try {
            const result = await api.runStrategy(selectedStrategy, {
                coin: dataInfo.coin,
                days: parseInt(dataInfo.period) || 90,
                timeframe: dataInfo.timeframe,
                initial_balance: customBalance,
                use_compound: useCompound,
                sizing_method: "fixo", // Assuming this is fixed for now
                params: currentParams, // Send only key-value pairs
                include_fees: includeFees, // Pass includeFees to API
                fee_rate: includeFees ? customFee : 0.0, // Pass custom fee if fees enabled
            });

            setRawResult(result);

            setResults({
                trades: result.metrics.total_trades,
                pnl: `${result.metrics.total_pnl_pct >= 0 ? '+' : ''}${result.metrics.total_pnl_pct.toFixed(2)}%`,
                winRate: `${(result.metrics.win_rate * 100).toFixed(0)}%`,
                maxDD: `${result.metrics.max_drawdown.toFixed(1)}%`
            });

            // Map trades for chart if present
            if (result.trades) {
                // Store full trades for table
                setFullTrades(result.trades);

                // Prepare trades for chart (Entries and Exits)
                const chartTrades: any[] = [];

                result.trades.forEach((t: any) => {
                    // Entry Marker
                    const entryTime = t.entry_ts !== undefined ? t.entry_ts : (new Date(t.entry_date).getTime() / 1000);
                    chartTrades.push({
                        time: entryTime,
                        type: "BUY", // Always Green for Entry
                        price: t.entry_price
                    });

                    // Exit Marker (if closed)
                    if (t.status === "CLOSED" && t.exit_ts) {
                        chartTrades.push({
                            time: t.exit_ts,
                            type: "SELL", // SELL (Red) for Exit
                            price: t.exit_price
                        });
                    }
                });

                console.log("Debug Trades:", {
                    count: chartTrades.length,
                    sample: chartTrades[0]
                });

                setTrades(chartTrades);
            }

        } catch (err) {
            console.error("Erro ao executar estratégia:", err);
            setError(err instanceof Error ? err.message : "Erro ao executar backtest");
        } finally {
            setIsRunning(false);
        }
    };

    const handleApplyStrategy = async () => {
        if (!selectedStrategy || !rawResult) return;

        try {
            await api.setActiveStrategy({
                strategy_slug: selectedStrategy,
                params: currentParams,
                coin: dataInfo?.coin || "SOL/USDT",
                period: dataInfo?.period || "90 dias",
                timeframe: dataInfo?.timeframe || "1h",
                initial_balance: 10000,
                backtest_metrics: rawResult
            });
            alert("Estratégia aplicada com sucesso! Confira na aba Resultados.");
        } catch (e) {
            console.error(e);
            setError("Erro ao aplicar estratégia.");
        }
    };

    // Helper to format currency
    const formatCurrency = (val: number, minimumFractionDigits = 2) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits
        }).format(val);
    };

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-white">Laboratório de Estratégias</h1>
                <p className="text-slate-400 mt-1">
                    Selecione uma estratégia e execute backtest
                </p>
            </div>

            {/* No Data Warning */}
            {!hasData && <NoDataBanner pageName="Laboratório de Estratégias" />}

            {/* Category Filter */}
            <div className="flex flex-wrap gap-2 mb-6">
                {CATEGORIES.map((cat) => (
                    <button
                        key={cat.value}
                        onClick={() => setSelectedCategory(cat.value)}
                        className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${selectedCategory === cat.value
                            ? "bg-emerald-600 text-white"
                            : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                            }`}
                    >
                        {cat.label}
                    </button>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Strategy List */}
                <div className="lg:col-span-1">
                    <h2 className="text-lg font-semibold text-white mb-4">
                        Estratégias ({filteredStrategies.length})
                    </h2>
                    <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                        {filteredStrategies.map((strategy) => (
                            <StrategyCard
                                key={strategy.slug}
                                slug={strategy.slug}
                                name={strategy.name}
                                category={strategy.category}
                                icon={strategy.icon}
                                description={strategy.description}
                                isSelected={selectedStrategy === strategy.slug}
                                onClick={() => setSelectedStrategy(strategy.slug)}
                            />
                        ))}
                    </div>
                </div>

                {/* Main Content */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Strategy Info & Run Button */}
                    <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
                        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                            <div>
                                <h3 className="text-white font-medium">
                                    {selectedStrategyData
                                        ? selectedStrategyData.name
                                        : "Selecione uma estratégia"
                                    }
                                </h3>
                                <p className="text-slate-400 text-sm">
                                    {selectedStrategyData
                                        ? <LinkedText text={selectedStrategyData.description} />
                                        : "Clique em uma estratégia na lista ao lado"
                                    }
                                </p>
                                {selectedStrategyData && (
                                    <p className="text-xs text-emerald-400 mt-1">
                                        Ideal para: <LinkedText text={selectedStrategyData.idealFor} />
                                    </p>
                                )}
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={handleApplyStrategy}
                                    disabled={!results}
                                    className="px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-md transition-colors"
                                    title={!results ? "Execute o backtest primeiro" : "Definir como estratégia oficial"}
                                >
                                    Aplicar Oficialmente
                                </button>
                                <button
                                    onClick={handleRunStrategy}
                                    disabled={!selectedStrategy || isRunning || !hasData}
                                    className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium rounded-md transition-colors"
                                    title={!hasData ? "Carregue dados no Dashboard primeiro" : undefined}
                                >
                                    {isRunning ? "Executando..." : "Executar Backtest"}
                                </button>
                            </div>
                        </div>

                        {error && (
                            <div className="mt-4 p-3 bg-red-900/50 border border-red-700 rounded text-red-200 text-sm">
                                {error}
                            </div>
                        )}
                    </div>

                    {/* Parameters (if strategy selected) */}
                    {selectedStrategyData && Object.keys(selectedStrategyData.parameters).length > 0 && (
                        <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
                            <h3 className="text-lg font-semibold text-white mb-4">Parâmetros</h3>
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                                {Object.entries(selectedStrategyData.parameters).map(([key, param]) => (
                                    <div key={key}>
                                        <label className="block text-sm text-slate-400 mb-1">
                                            {param.label}
                                        </label>
                                        <input
                                            type="number"
                                            value={currentParams[key] ?? param.default}
                                            min={param.min}
                                            max={param.max}
                                            onChange={(e) => setCurrentParams({
                                                ...currentParams,
                                                [key]: parseFloat(e.target.value)
                                            })}
                                            className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                                        />
                                    </div>
                                ))}
                                <div>
                                    <label className="block text-sm text-transparent mb-1 select-none">
                                        Opções
                                    </label>
                                    <label className="flex items-center gap-2 cursor-pointer bg-slate-800 px-3 py-2 rounded-md border border-slate-700 hover:border-slate-600 transition-colors h-[38px] mb-2">
                                        <input
                                            type="checkbox"
                                            checked={includeFees}
                                            onChange={(e) => setIncludeFees(e.target.checked)}
                                            className="rounded bg-slate-900 border-slate-600 text-emerald-500 focus:ring-emerald-500 focus:ring-offset-slate-900"
                                        />
                                        <span className="text-sm text-slate-300 select-none">Considerar Taxas</span>
                                    </label>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Results */}
                    {results && (
                        <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
                            <h3 className="text-lg font-semibold text-white mb-4">Resultados</h3>
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                                {[
                                    { label: "Trades", value: results.trades },
                                    { label: "PnL", value: results.pnl, color: results.pnl.startsWith('-') ? "text-red-400" : "text-emerald-400" },
                                    { label: "Win Rate", value: results.winRate },
                                    { label: "Max DD", value: results.maxDD, color: "text-red-400" },
                                ].map((stat) => (
                                    <div key={stat.label} className="text-center">
                                        <div className="text-slate-400 text-sm">{stat.label}</div>
                                        <div className={`text-xl font-bold ${stat.color || "text-white"}`}>
                                            {stat.value}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Chart */}
                    <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
                        <h3 className="text-lg font-semibold text-white mb-4">Gráfico com Trades</h3>
                        <div className="mb-4">
                            <Chart data={chartData} trades={trades} height={400} />

                            {/* Legend */}
                            <div className="mt-4 flex flex-wrap items-center justify-center gap-6 text-sm text-slate-400 border-t border-slate-800 pt-4">
                                <div className="flex items-center gap-2">
                                    <div className="w-0.5 h-4 bg-emerald-500"></div>
                                    <span>Compra (Long/Cover)</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-0.5 h-4 bg-red-500"></div>
                                    <span>Venda (Short/Exit)</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Trade History Table */}
                    {fullTrades.length > 0 && results && (
                        <TradesTable trades={fullTrades} />
                    )}
                </div>
            </div>
        </div>
    );
}
