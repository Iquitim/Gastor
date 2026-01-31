"use client";

import { useState, useEffect } from "react";
import StrategyCard from "../../components/StrategyCard";
import NoDataBanner from "../../components/NoDataBanner";
import { STRATEGIES as DEFAULT_STRATEGIES, CATEGORIES, Strategy } from "../../lib/strategies";
import { useData } from "../../context/DataContext";
import api from "../../lib/api";
import { getStoredSettings } from "../../lib/settings";

import { useRouter } from "next/navigation";

interface OptimizationResult {
    rank: number;
    strategy: string;
    params: string;
    pnl: string;
    winRate: string;
    pairs: number;
}

export default function OptimizerPage() {
    const router = useRouter();
    const { hasData, dataInfo } = useData();
    const [selectedCategory, setSelectedCategory] = useState("all");
    const [selectedStrategies, setSelectedStrategies] = useState<string[]>([]);
    const [paramSteps, setParamSteps] = useState(3);
    const [optimizeExecution, setOptimizeExecution] = useState(false);
    const [includeFees, setIncludeFees] = useState(false);
    const [minPairs, setMinPairs] = useState(3);
    const [isRunning, setIsRunning] = useState(false);
    const [results, setResults] = useState<OptimizationResult[]>([]);
    const [error, setError] = useState<string | null>(null);

    const [strategies, setStrategies] = useState<Strategy[]>([]);

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
                setStrategies(DEFAULT_STRATEGIES);
            }
        };
        load();
    }, []);

    const filteredStrategies = strategies.filter(s =>
        selectedCategory === "all" ? true : s.category === selectedCategory
    );

    const toggleStrategy = (slug: string) => {
        setSelectedStrategies(prev =>
            prev.includes(slug)
                ? prev.filter(s => s !== slug)
                : [...prev, slug]
        );
    };

    const selectAll = () => {
        setSelectedStrategies(filteredStrategies.map(s => s.slug));
    };

    const clearAll = () => {
        setSelectedStrategies([]);
    };

    const handleApplyResult = async (result: OptimizationResult) => {
        if (!dataInfo) return;

        const confirmed = confirm("Processar backtest detalhado e aplicar estratégia?");
        if (!confirmed) return;

        // Settings helper
        const { customFee, initialBalance: customBalance } = getStoredSettings(dataInfo.coin);

        try {
            const paramsObj: Record<string, any> = {};
            result.params.split(', ').forEach(pair => {
                const [key, val] = pair.split('=');
                if (key && val) paramsObj[key] = isNaN(Number(val)) ? val : Number(val);
            });

            // Executar backtest completo para obter curva de equity e métricas reais
            const runParams = {
                coin: dataInfo.coin,
                days: parseInt(dataInfo.period) || 90,
                timeframe: dataInfo.timeframe,
                initial_balance: customBalance,
                include_fees: includeFees,
                fee_rate: includeFees ? customFee : 0.0,
                params: paramsObj
            };

            const fullResult = await api.runStrategy(result.strategy, runParams);

            if (!fullResult || (fullResult as any).error) {
                throw new Error("Falha ao executar backtest.");
            }

            await api.setActiveStrategy({
                strategy_slug: result.strategy,
                params: paramsObj,
                coin: dataInfo.coin,
                period: dataInfo.period,
                timeframe: dataInfo.timeframe,
                initial_balance: 10000,
                backtest_metrics: fullResult
            });

            router.push('/results');
        } catch (e) {
            console.error(e);
            alert("Erro ao aplicar estratégia.");
        }
    };




    const handleRunOptimizer = async () => {
        if (selectedStrategies.length === 0 || !hasData || !dataInfo) return;

        // Settings helper
        const { customFee, initialBalance: customBalance } = getStoredSettings(dataInfo.coin);

        setIsRunning(true);
        setError(null);
        setResults([]);

        try {
            const response = await api.runOptimizer({
                strategies: selectedStrategies,
                coin: dataInfo.coin,
                days: parseInt(dataInfo.period) || 90,
                param_steps: paramSteps,
                optimize_execution: optimizeExecution,
                min_pairs: minPairs,
                include_fees: includeFees,
                fee_rate: includeFees ? customFee : 0.0, // Pass custom fee
                initial_balance: customBalance
            });

            // Mapear resultados para o formato esperado
            if (response.results && Array.isArray(response.results)) {
                interface ApiResult {
                    strategy?: string;
                    params?: Record<string, unknown>;
                    metrics?: { total_pnl_pct?: number; win_rate?: number; total_trades?: number };
                }
                const mappedResults: OptimizationResult[] = (response.results as ApiResult[]).map((r, index) => ({
                    rank: index + 1,
                    strategy: r.strategy || 'Unknown',
                    params: Object.entries(r.params || {}).map(([k, v]) => `${k}=${v}`).join(', '),
                    pnl: `${(r.metrics?.total_pnl_pct || 0) >= 0 ? '+' : ''}${(r.metrics?.total_pnl_pct || 0).toFixed(2)}%`,
                    winRate: `${((r.metrics?.win_rate || 0) * 100).toFixed(0)}%`,
                    pairs: r.metrics?.total_trades || 0,
                }));
                setResults(mappedResults);
            }
        } catch (err) {
            console.error("Erro na otimização:", err);
            setError(err instanceof Error ? err.message : "Erro ao executar otimização");
        } finally {
            setIsRunning(false);
        }
    };

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-white">Otimizador de Estratégias</h1>
                <p className="text-slate-400 mt-1">
                    Grid Search automático para encontrar os melhores parâmetros
                </p>
            </div>

            {/* No Data Warning */}
            {!hasData && <NoDataBanner pageName="Otimizador" />}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Configuration */}
                <div className="lg:col-span-1 space-y-6">
                    {/* Category Filter */}
                    <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
                        <h2 className="text-lg font-semibold text-white mb-3">Categoria</h2>
                        <div className="flex flex-wrap gap-2">
                            {CATEGORIES.map((cat) => (
                                <button
                                    key={cat.value}
                                    onClick={() => setSelectedCategory(cat.value)}
                                    className={`px-2 py-1 rounded text-xs font-medium transition-colors ${selectedCategory === cat.value
                                        ? "bg-emerald-600 text-white"
                                        : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                                        }`}
                                >
                                    {cat.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Strategy Selection */}
                    <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
                        <div className="flex items-center justify-between mb-3">
                            <h2 className="text-lg font-semibold text-white">Estratégias</h2>
                            <div className="flex gap-2">
                                <button onClick={selectAll} className="text-xs text-emerald-400 hover:underline">
                                    Todas
                                </button>
                                <button onClick={clearAll} className="text-xs text-slate-400 hover:underline">
                                    Limpar
                                </button>
                            </div>
                        </div>
                        <div className="space-y-2 max-h-[300px] overflow-y-auto">
                            {filteredStrategies.map((strategy) => (
                                <StrategyCard
                                    key={strategy.slug}
                                    slug={strategy.slug}
                                    name={strategy.name}
                                    category={strategy.category}
                                    icon={strategy.icon}
                                    description={strategy.description}
                                    isSelected={selectedStrategies.includes(strategy.slug)}
                                    onClick={() => toggleStrategy(strategy.slug)}
                                />
                            ))}
                        </div>
                        <p className="text-sm text-slate-400 mt-3">
                            {selectedStrategies.length} estratégia(s) selecionada(s)
                        </p>
                    </div>


                </div>

                {/* Results */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Configuration (Moved) */}
                    <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-white">Configurações e Execução</h2>
                            <button
                                onClick={handleRunOptimizer}
                                disabled={selectedStrategies.length === 0 || isRunning}
                                className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium rounded-md transition-colors"
                            >
                                {isRunning ? "Otimizando..." : "Iniciar Otimização"}
                            </button>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">
                                    Granularidade (steps)
                                </label>
                                <select
                                    value={paramSteps}
                                    onChange={(e) => setParamSteps(Number(e.target.value))}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-white text-sm"
                                >
                                    <option value={2}>2 (Rápido)</option>
                                    <option value={3}>3 (Padrão)</option>
                                    <option value={5}>5 (Detalhado)</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm text-slate-400 mb-1">
                                    Mínimo de Trades
                                </label>
                                <input
                                    type="number"
                                    value={minPairs}
                                    onChange={(e) => setMinPairs(Number(e.target.value))}
                                    min={1}
                                    max={20}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-white text-sm"
                                />
                            </div>

                            <div className="flex flex-col justify-center space-y-2">
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={optimizeExecution}
                                        onChange={(e) => setOptimizeExecution(e.target.checked)}
                                        className="rounded bg-slate-800 border-slate-600 text-emerald-500"
                                    />
                                    <span className="text-sm text-slate-300">Otimizar Sizing</span>
                                </label>

                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={includeFees}
                                        onChange={(e) => setIncludeFees(e.target.checked)}
                                        className="rounded bg-slate-800 border-slate-600 text-emerald-500"
                                    />
                                    <span className="text-sm text-slate-300">Considerar Taxas</span>
                                </label>
                            </div>

                            <div className="flex items-center justify-end text-right">
                                <p className="text-xs text-slate-500">
                                    {selectedStrategies.length} estratégias selecionadas
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
                        <h2 className="text-lg font-semibold text-white mb-4">Resultados</h2>

                        {results.length === 0 ? (
                            <div className="text-center py-12 text-slate-400">
                                <p>Selecione estratégias e execute a otimização</p>
                                <p className="text-sm mt-2">O otimizador testará todas as combinações de parâmetros</p>
                            </div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="text-left text-slate-400 text-sm border-b border-slate-700">
                                            <th className="pb-3 pr-4">#</th>
                                            <th className="pb-3 pr-4">Estratégia</th>
                                            <th className="pb-3 pr-4">Parâmetros</th>
                                            <th className="pb-3 pr-4">PnL</th>
                                            <th className="pb-3 pr-4">Win Rate</th>
                                            <th className="pb-3">Pares</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {results.map((result, idx) => (
                                            <tr key={idx} className={`border-b ${idx < 3 ? 'bg-slate-800/80 border-emerald-900/30' : 'border-slate-800 hover:bg-slate-800/50'}`}>
                                                <td className="py-4 pl-4 pr-1">
                                                    <div className={`flex items-center justify-center w-8 h-8 rounded-full font-bold shadow-lg ${idx === 0 ? "bg-gradient-to-br from-yellow-400 to-yellow-600 text-black ring-2 ring-yellow-400/50" :
                                                        idx === 1 ? "bg-gradient-to-br from-slate-300 to-slate-500 text-black ring-2 ring-slate-400/50" :
                                                            idx === 2 ? "bg-gradient-to-br from-orange-400 to-orange-600 text-white ring-2 ring-orange-500/50" :
                                                                "bg-slate-800 text-slate-500 text-sm"
                                                        }`}>
                                                        {result.rank}
                                                    </div>
                                                </td>
                                                <td className="py-4 pr-4">
                                                    <div className="font-medium text-white">{result.strategy}</div>
                                                    {idx < 3 && <div className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider mt-0.5">Top PERFORMANCE</div>}
                                                </td>
                                                <td className="py-4 pr-4 text-slate-400 text-xs font-mono">{result.params}</td>
                                                <td className={`py-4 pr-4 font-bold text-lg ${idx < 3 ? "text-emerald-400" : "text-emerald-500/80"}`}>{result.pnl}</td>
                                                <td className="py-4 pr-4 text-white font-medium">{result.winRate}</td>
                                                <td className="py-4 text-slate-300">{result.pairs}</td>
                                                <td className="py-4 pr-4 text-right">
                                                    {idx < 3 && (
                                                        <button
                                                            onClick={() => handleApplyResult(result)}
                                                            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded shadow-lg shadow-emerald-900/20 transition-all hover:scale-105 active:scale-95"
                                                        >
                                                            APLICAR
                                                        </button>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
