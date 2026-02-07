"use client";

import { useState, useEffect, useCallback } from "react";
import NoDataBanner from "../../../components/NoDataBanner";
import SavedStrategiesList from "../../../components/SavedStrategiesList";
import { useData } from "../../../context/DataContext";
import api from "../../../lib/api";
import { getStoredSettings } from "../../../lib/settings";
import { useRouter } from "next/navigation";

// ... (constants remain the same)

// ... (constants remain the same)

// Indicadores disponíveis para construir regras
const INDICATORS = [
    { value: "rsi", label: "RSI", category: "oscillators", defaultPeriod: 14 },
    { value: "ema", label: "EMA", category: "moving_averages", defaultPeriod: 21 },
    { value: "sma", label: "SMA", category: "moving_averages", defaultPeriod: 20 },
    { value: "macd", label: "MACD", category: "oscillators", defaultPeriod: 12 },
    { value: "macd_signal", label: "MACD Signal", category: "oscillators", defaultPeriod: 9 },
    { value: "bb_upper", label: "Bollinger Upper", category: "volatility", defaultPeriod: 20 },
    { value: "bb_lower", label: "Bollinger Lower", category: "volatility", defaultPeriod: 20 },
    { value: "stoch_k", label: "Stochastic %K", category: "oscillators", defaultPeriod: 14 },
    { value: "atr", label: "ATR", category: "volatility", defaultPeriod: 14 },
    { value: "close", label: "Preço (Close)", category: "price", defaultPeriod: 0 },
    { value: "volume", label: "Volume", category: "volume", defaultPeriod: 0 },
    { value: "avg_volume", label: "Média de Volume", category: "volume", defaultPeriod: 20 },
    { value: "median", label: "Mediana (Preço)", category: "stats", defaultPeriod: 20 },
    { value: "mad", label: "MAD (Desvio Absoluto Mediano)", category: "stats", defaultPeriod: 20 },
    { value: "zscore_robust", label: "Z-Score Robusto", category: "stats", defaultPeriod: 20 },
];

const OPERATORS = [
    { value: "<", label: "< menor que" },
    { value: ">", label: "> maior que" },
    { value: "<=", label: "≤ menor ou igual" },
    { value: ">=", label: "≥ maior ou igual" },
    { value: "cross_up", label: "cruza para cima" },
    { value: "cross_down", label: "cruza para baixo" },
];

interface Rule {
    id: number;
    indicator: string;
    period: number;
    operator: string;
    valueType: "constant" | "indicator";
    value: number | string;
    valuePeriod: number;
}

interface RuleGroup {
    id: number;
    logic: "AND" | "OR";
    rules: Rule[];
}

const createEmptyRule = (id: number, type: "buy" | "sell" = "buy"): Rule => ({
    id,
    indicator: "rsi",
    period: 14,
    operator: type === "buy" ? "<" : ">",
    valueType: "constant",
    value: type === "buy" ? 30 : 70,
    valuePeriod: 21,
});

const createEmptyGroup = (id: number, type: "buy" | "sell" = "buy"): RuleGroup => ({
    id,
    logic: "AND",
    rules: [createEmptyRule(1, type)],
});

export default function BuilderPage() {
    const router = useRouter();
    const { hasData, dataInfo } = useData();
    const [strategyName, setStrategyName] = useState("");
    const [buyGroups, setBuyGroups] = useState<RuleGroup[]>([createEmptyGroup(1, "buy")]);
    const [sellGroups, setSellGroups] = useState<RuleGroup[]>([createEmptyGroup(1, "sell")]);
    const [buyLogic, setBuyLogic] = useState<"AND" | "OR">("OR");
    const [sellLogic, setSellLogic] = useState<"AND" | "OR">("OR");
    const [isTesting, setIsTesting] = useState(false);
    const [testResult, setTestResult] = useState<string | null>(null);
    const [showLoadModal, setShowLoadModal] = useState(false);

    // Define handleLoad first with useCallback
    const handleLoad = useCallback((strategy: any) => {
        if (strategy.rules) {
            setStrategyName(strategy.name);
            setBuyGroups(strategy.rules.buy || [createEmptyGroup(1, "buy")]);
            setSellGroups(strategy.rules.sell || [createEmptyGroup(1, "sell")]);
            setBuyLogic(strategy.rules.buyLogic || "OR");
            setSellLogic(strategy.rules.sellLogic || "OR");
            setShowLoadModal(false);
        } else if (strategy.parameters) {
            // Fallback for system strategies if needed, though they are not fully editable
        }
    }, []);

    // Load strategy from URL param if present
    // Load strategy from URL param if present
    useEffect(() => {
        const loadId = new URLSearchParams(window.location.search).get("load");
        if (loadId) {
            // Need to fix getStrategy to support custom IDs properly or use a specific endpoint
            // backend get_strategy supports "custom_ID" slug format
            api.getStrategy(`custom_${loadId}`).then(strategy => {
                if (strategy) {
                    handleLoad(strategy);
                    // Clean URL
                    window.history.replaceState({}, "", "/strategies/builder");
                }
            }).catch(err => {
                console.error("Erro ao carregar estratégia:", err);
                // setLoadError("Erro ao carregar estratégia para edição: " + err.message);
            });
        }
    }, [handleLoad]);

    // ... (rest of the component)

    // Add rule to group
    const addRuleToGroup = (section: "buy" | "sell", groupId: number) => {
        const setGroups = section === "buy" ? setBuyGroups : setSellGroups;
        setGroups(prev => prev.map(g => {
            if (g.id === groupId) {
                const newId = Math.max(...g.rules.map(r => r.id), 0) + 1;
                return { ...g, rules: [...g.rules, createEmptyRule(newId, section)] };
            }
            return g;
        }));
    };

    // Remove rule from group
    const removeRuleFromGroup = (section: "buy" | "sell", groupId: number, ruleId: number) => {
        const setGroups = section === "buy" ? setBuyGroups : setSellGroups;
        setGroups(prev => prev.map(g => {
            if (g.id === groupId) {
                const newRules = g.rules.filter(r => r.id !== ruleId);
                return { ...g, rules: newRules.length ? newRules : [createEmptyRule(1, section)] };
            }
            return g;
        }));
    };

    // Update rule
    const updateRule = (section: "buy" | "sell", groupId: number, ruleId: number, updates: Partial<Rule>) => {
        const setGroups = section === "buy" ? setBuyGroups : setSellGroups;
        setGroups(prev => prev.map(g => {
            if (g.id === groupId) {
                return {
                    ...g,
                    rules: g.rules.map(r => r.id === ruleId ? { ...r, ...updates } : r)
                };
            }
            return g;
        }));
    };

    // Add group
    const addGroup = (section: "buy" | "sell") => {
        const setGroups = section === "buy" ? setBuyGroups : setSellGroups;
        setGroups(prev => {
            const newId = Math.max(...prev.map(g => g.id), 0) + 1;
            return [...prev, createEmptyGroup(newId, section)];
        });
    };

    // Remove group
    const removeGroup = (section: "buy" | "sell", groupId: number) => {
        const setGroups = section === "buy" ? setBuyGroups : setSellGroups;
        setGroups(prev => {
            const newGroups = prev.filter(g => g.id !== groupId);
            return newGroups.length ? newGroups : [createEmptyGroup(1, section)];
        });
    };

    // Render rule
    const renderRule = (section: "buy" | "sell", groupId: number, rule: Rule) => {
        const indicatorConfig = INDICATORS.find(i => i.value === rule.indicator);
        const hasPeriod = indicatorConfig && indicatorConfig.defaultPeriod > 0;

        return (
            <div key={rule.id} className="bg-slate-800/50 rounded-lg p-3 space-y-3">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {/* Indicator */}
                    <div>
                        <label className="text-xs text-slate-400">Indicador</label>
                        <select
                            value={rule.indicator}
                            onChange={(e) => {
                                const newInd = INDICATORS.find(i => i.value === e.target.value);
                                updateRule(section, groupId, rule.id, {
                                    indicator: e.target.value,
                                    period: newInd?.defaultPeriod || 14
                                });
                            }}
                            className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white"
                        >
                            {INDICATORS.map(ind => (
                                <option key={ind.value} value={ind.value}>{ind.label}</option>
                            ))}
                        </select>
                    </div>

                    {/* Period */}
                    {hasPeriod && (
                        <div>
                            <label className="text-xs text-slate-400">Período</label>
                            <input
                                type="number"
                                value={rule.period}
                                onChange={(e) => updateRule(section, groupId, rule.id, { period: Number(e.target.value) })}
                                min={1}
                                max={200}
                                className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white"
                            />
                        </div>
                    )}

                    {/* Operator */}
                    <div>
                        <label className="text-xs text-slate-400">Operador</label>
                        <select
                            value={rule.operator}
                            onChange={(e) => updateRule(section, groupId, rule.id, { operator: e.target.value })}
                            className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white"
                        >
                            {OPERATORS.map(op => (
                                <option key={op.value} value={op.value}>{op.label}</option>
                            ))}
                        </select>
                    </div>

                    {/* Value Type */}
                    <div>
                        <label className="text-xs text-slate-400">Comparar com</label>
                        <select
                            value={rule.valueType}
                            onChange={(e) => updateRule(section, groupId, rule.id, {
                                valueType: e.target.value as "constant" | "indicator",
                                value: e.target.value === "constant" ? 30 : "ema"
                            })}
                            className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white"
                        >
                            <option value="constant">Valor</option>
                            <option value="indicator">Indicador</option>
                        </select>
                    </div>
                </div>

                {/* Value / Indicator */}
                <div className="flex items-center gap-3">
                    {rule.valueType === "constant" ? (
                        <div className="flex-1">
                            <input
                                type="number"
                                value={rule.value as number}
                                onChange={(e) => updateRule(section, groupId, rule.id, { value: Number(e.target.value) })}
                                step={0.1}
                                className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white"
                            />
                        </div>
                    ) : (
                        <>
                            <div className="flex-1">
                                <select
                                    value={rule.value as string}
                                    onChange={(e) => updateRule(section, groupId, rule.id, { value: e.target.value })}
                                    className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white"
                                >
                                    {INDICATORS.map(ind => (
                                        <option key={ind.value} value={ind.value}>{ind.label}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="w-20">
                                <input
                                    type="number"
                                    value={rule.valuePeriod}
                                    onChange={(e) => updateRule(section, groupId, rule.id, { valuePeriod: Number(e.target.value) })}
                                    min={1}
                                    max={200}
                                    className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white"
                                    placeholder="Período"
                                />
                            </div>
                        </>
                    )}

                    <button
                        onClick={() => removeRuleFromGroup(section, groupId, rule.id)}
                        className="text-red-400 hover:text-red-300 p-1"
                        title="Remover regra"
                    >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                    </button>
                </div>
            </div>
        );
    };

    // Render group
    const renderGroup = (section: "buy" | "sell", group: RuleGroup, groupIndex: number, totalGroups: number) => {
        const color = section === "buy" ? "emerald" : "red";
        const setGroups = section === "buy" ? setBuyGroups : setSellGroups;

        return (
            <div key={group.id} className={`border-l-4 ${section === "buy" ? "border-emerald-500" : "border-red-500"} pl-4`}>
                <div className="flex items-center justify-between mb-3">
                    <span className={`text-${color}-400 font-semibold`}>Grupo {groupIndex + 1}</span>
                    <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2 text-sm">
                            <span className="text-slate-400">Lógica:</span>
                            <button
                                onClick={() => setGroups(prev => prev.map(g =>
                                    g.id === group.id ? { ...g, logic: "AND" } : g
                                ))}
                                className={`px-2 py-0.5 rounded ${group.logic === "AND"
                                    ? "bg-blue-600 text-white"
                                    : "bg-slate-700 text-slate-300"
                                    }`}
                            >
                                AND
                            </button>
                            <button
                                onClick={() => setGroups(prev => prev.map(g =>
                                    g.id === group.id ? { ...g, logic: "OR" } : g
                                ))}
                                className={`px-2 py-0.5 rounded ${group.logic === "OR"
                                    ? "bg-amber-600 text-white"
                                    : "bg-slate-700 text-slate-300"
                                    }`}
                            >
                                OR
                            </button>
                        </div>
                        {totalGroups > 1 && (
                            <button
                                onClick={() => removeGroup(section, group.id)}
                                className="text-red-400 hover:text-red-300"
                                title="Remover grupo"
                            >
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                            </button>
                        )}
                    </div>
                </div>

                <div className="space-y-2">
                    {group.rules.map((rule, idx) => (
                        <div key={rule.id}>
                            {idx > 0 && (
                                <div className="flex justify-center my-2">
                                    <span className={`px-3 py-0.5 rounded-full text-xs font-bold ${group.logic === "AND"
                                        ? "bg-blue-600 text-white"
                                        : "bg-amber-600 text-white"
                                        }`}>
                                        {group.logic}
                                    </span>
                                </div>
                            )}
                            {renderRule(section, group.id, rule)}
                        </div>
                    ))}
                </div>

                <button
                    onClick={() => addRuleToGroup(section, group.id)}
                    className="mt-3 w-full py-1 text-sm border border-dashed border-slate-600 text-slate-400 hover:border-slate-500 hover:text-slate-300 rounded"
                >
                    + Adicionar Regra
                </button>
            </div>
        );
    };

    // Render section (buy/sell)
    const renderSection = (section: "buy" | "sell") => {
        const groups = section === "buy" ? buyGroups : sellGroups;
        const logic = section === "buy" ? buyLogic : sellLogic;
        const setLogic = section === "buy" ? setBuyLogic : setSellLogic;
        const title = section === "buy" ? "Regras de COMPRA" : "Regras de VENDA";

        return (
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-4">
                <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>

                {groups.length > 1 && (
                    <div className="flex items-center justify-center gap-2 mb-4 text-sm">
                        <span className="text-slate-400">Grupos combinados com:</span>
                        <button
                            onClick={() => setLogic("AND")}
                            className={`px-3 py-1 rounded ${logic === "AND" ? "bg-blue-600 text-white" : "bg-slate-700 text-slate-300"
                                }`}
                        >
                            AND
                        </button>
                        <button
                            onClick={() => setLogic("OR")}
                            className={`px-3 py-1 rounded ${logic === "OR" ? "bg-amber-600 text-white" : "bg-slate-700 text-slate-300"
                                }`}
                        >
                            OR
                        </button>
                    </div>
                )}

                <div className="space-y-6">
                    {groups.map((group, idx) => (
                        <div key={group.id}>
                            {idx > 0 && (
                                <div className="flex justify-center my-4">
                                    <span className={`px-4 py-1 rounded-full text-sm font-bold ${logic === "AND" ? "bg-blue-600 text-white" : "bg-amber-600 text-white"
                                        }`}>
                                        {logic}
                                    </span>
                                </div>
                            )}
                            {renderGroup(section, group, idx, groups.length)}
                        </div>
                    ))}
                </div>

                <button
                    onClick={() => addGroup(section)}
                    className="mt-4 w-full py-2 border border-dashed border-slate-600 text-slate-400 hover:border-slate-500 hover:text-slate-300 rounded"
                >
                    + Adicionar Grupo
                </button>
            </div>
        );
    };

    const getStrategyRules = () => ({
        buy: buyGroups,
        sell: sellGroups,
        buyLogic,
        sellLogic
    });

    const validateStrategy = (): string | null => {
        // Verificar regras idênticas
        const buyJson = JSON.stringify(buyGroups.map(g => ({ ...g, id: 0, rules: g.rules.map(r => ({ ...r, id: 0 })) })));
        const sellJson = JSON.stringify(sellGroups.map(g => ({ ...g, id: 0, rules: g.rules.map(r => ({ ...r, id: 0 })) })));

        if (buyJson === sellJson) {
            return "As regras de COMPRA e VENDA são idênticas. Isso causará perdas imediatas.";
        }

        for (const bg of buyGroups) {
            for (const br of bg.rules) {
                for (const sg of sellGroups) {
                    for (const sr of sg.rules) {
                        if (br.indicator === sr.indicator &&
                            br.period === sr.period &&
                            br.operator === sr.operator &&
                            br.value == sr.value &&
                            br.valueType === sr.valueType) {
                            return `⚠️ Lógica Inválida: A regra de Compra (${br.indicator} ${br.operator} ${br.value}) é idêntica a uma regra de Venda.`;
                        }
                    }
                }
            }
        }
        return null;
    };

    const runBacktest = async () => {
        if (!dataInfo) throw new Error("Sem dados carregados");

        const { customFee, initialBalance, useCompound } = getStoredSettings(dataInfo.coin);

        const rules = getStrategyRules();
        const runParams = {
            coin: dataInfo.coin,
            days: parseInt(dataInfo.period) || 90,
            timeframe: dataInfo.timeframe,
            initial_balance: initialBalance,
            use_compound: useCompound,
            sizing_method: "fixo", // Explicitly set sizing method
            include_fees: customFee !== undefined,
            fee_rate: customFee !== undefined ? (customFee ?? 0.0) : 0.0,
            params: { rules }
        };

        return await api.runStrategy("custom", runParams);
    };

    const handleTest = async () => {
        if (!dataInfo) return;

        const error = validateStrategy();
        if (error) {
            setTestResult(error);
            return;
        }

        setIsTesting(true);
        setTestResult(null);
        try {
            const result = await runBacktest();

            if (result && result.metrics) {
                const profit = result.metrics.total_pnl_pct.toFixed(2);
                const trades = result.metrics.total_trades;
                const sign = result.metrics.total_pnl >= 0 ? "+" : "";
                setTestResult(`Resultado: ${trades} trades, Lucro: ${sign}${profit}%`);
            } else {
                setTestResult("Teste finalizado sem métricas (0 trades?)");
            }
        } catch (e: any) {
            console.error(e);
            setTestResult(e.message || "Erro ao executar teste");
        } finally {
            setIsTesting(false);
        }
    };

    const handleApply = async () => {
        if (!dataInfo) return;
        if (!strategyName) {
            alert("Dê um nome para a estratégia antes de aplicar.");
            return;
        }

        const error = validateStrategy();
        if (error) {
            alert(error);
            return;
        }

        // Recuperar settings localmente para usar no setActiveStrategy
        const { initialBalance, useCompound, customFee } = getStoredSettings(dataInfo.coin);

        try {
            const result = await runBacktest();

            await api.setActiveStrategy({
                strategy_slug: "custom", // Slug especial
                params: {
                    name: strategyName,
                    rules: getStrategyRules()
                },
                coin: dataInfo.coin,
                period: dataInfo.period,
                timeframe: dataInfo.timeframe,
                initial_balance: initialBalance,
                use_compound: useCompound, /**/
                sizing_method: "fixo",
                include_fees: customFee !== undefined,
                fee_rate: customFee !== undefined ? (customFee ?? 0.0) : 0.0,
                backtest_metrics: result
            });

            router.push('/results');
        } catch (e: any) {
            console.error(e);
            alert(e.message || "Erro ao aplicar estratégia.");
        }
    };

    const handleSave = async () => {
        if (!dataInfo) {
            alert("Carregue dados de mercado primeiro.");
            return;
        }
        if (!strategyName) {
            alert("Dê um nome para a estratégia.");
            return;
        }

        const error = validateStrategy();
        if (error) {
            alert(error);
            return;
        }

        try {
            await api.saveCustomStrategy({
                name: strategyName,
                description: `Criada no Builder para ${dataInfo.coin}`,
                coin: dataInfo.coin,
                period: dataInfo.period,
                timeframe: dataInfo.timeframe,
                rules: getStrategyRules()
            });
            alert("Estratégia salva com sucesso!");
        } catch (e: any) {
            console.error(e);
            alert("Erro ao salvar: " + e.message);
        }
    };



    return (
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-white">Construtor de Estratégias</h1>
                <p className="text-slate-400 mt-1">
                    Monte estratégias personalizadas combinando regras com lógica AND/OR
                </p>
            </div>

            {/* No Data Warning */}
            {!hasData && <NoDataBanner pageName="Construtor de Estratégias" />}

            {/* Strategy Name */}
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-4 mb-6">
                <div className="flex flex-col sm:flex-row gap-4">
                    <div className="flex-1">
                        <label className="block text-sm text-slate-400 mb-1">Nome da Estratégia</label>
                        <input
                            type="text"
                            value={strategyName}
                            onChange={(e) => setStrategyName(e.target.value)}
                            placeholder="Ex: Z-Score Robusto"
                            className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-white"
                        />
                    </div>
                    <div className="flex items-end gap-2">
                        <button
                            onClick={() => {
                                setStrategyName("");
                                setBuyGroups([createEmptyGroup(1, "buy")]);
                                setSellGroups([createEmptyGroup(1, "sell")]);
                                setTestResult(null);
                            }}
                            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-md"
                        >
                            Limpar
                        </button>
                    </div>
                </div>
            </div>

            {/* Rules Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {renderSection("buy")}
                {renderSection("sell")}
            </div>

            {/* Actions */}
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-4 mb-6">
                <div className="flex flex-wrap gap-4">
                    <button
                        onClick={handleTest}
                        disabled={isTesting}
                        className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-md"
                    >
                        {isTesting ? "Testando..." : "Testar"}
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={!strategyName}
                        className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 text-white rounded-md"
                    >
                        Salvar
                    </button>
                    <button
                        onClick={() => setShowLoadModal(true)}
                        className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-md"
                    >
                        Carregar
                    </button>
                    <button
                        onClick={handleApply}
                        disabled={!strategyName}
                        className="flex-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-700 text-white rounded-md"
                    >
                        Aplicar
                    </button>
                </div>

                {testResult && (
                    <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-md text-blue-300">
                        {testResult}
                    </div>
                )}
            </div>

            {/* Help */}
            <div className="bg-slate-900/50 rounded-lg border border-slate-800 p-4">
                <h4 className="font-semibold text-white mb-2">Como Funciona</h4>
                <ul className="text-sm text-slate-400 space-y-1">
                    <li>• <strong>Regras:</strong> Condições individuais (ex: RSI &lt; 30)</li>
                    <li>• <strong>Grupos:</strong> Conjunto de regras combinadas com AND ou OR</li>
                    <li>• <strong>AND:</strong> Todas as condições devem ser verdadeiras</li>
                    <li>• <strong>OR:</strong> Pelo menos uma condição deve ser verdadeira</li>
                    <li>• <strong>Cruzamento:</strong> Use operadores de cruzamento para detectar quando um indicador cruza outro</li>
                </ul>
            </div>
            {showLoadModal && (
                <SavedStrategiesList
                    onLoad={handleLoad}
                    onClose={() => setShowLoadModal(false)}
                />
            )}
        </div>
    );
}
