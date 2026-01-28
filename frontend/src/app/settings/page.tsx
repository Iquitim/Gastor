"use client";

import { useState, useEffect } from "react";

interface CoinConfig {
    enabled: boolean;
    fee: number;
    slippage: number;
}

const DEFAULT_COINS: Record<string, CoinConfig> = {
    "BTC/USDT": { enabled: true, fee: 0.10, slippage: 0.10 },
    "ETH/USDT": { enabled: true, fee: 0.10, slippage: 0.12 },
    "SOL/USDT": { enabled: true, fee: 0.10, slippage: 0.15 },
    "XRP/USDT": { enabled: true, fee: 0.10, slippage: 0.12 },
    "AVAX/USDT": { enabled: false, fee: 0.10, slippage: 0.25 },
    "DOGE/USDT": { enabled: false, fee: 0.10, slippage: 0.20 },
};

export default function SettingsPage() {
    const [coins, setCoins] = useState(DEFAULT_COINS);
    const [initialBalance, setInitialBalance] = useState(10000);
    const [positionSize, setPositionSize] = useState(100);
    const [useCompound, setUseCompound] = useState(false);
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        const saved = localStorage.getItem("gastor_settings");
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                if (parsed.coins) setCoins(parsed.coins);
                if (parsed.initialBalance) setInitialBalance(parsed.initialBalance);
                if (parsed.positionSize) setPositionSize(parsed.positionSize);
                if (parsed.useCompound !== undefined) setUseCompound(parsed.useCompound);
            } catch (e) {
                console.error("Erro ao carregar configurações", e);
            }
        }
    }, []);

    const handleCoinChange = (coin: string, field: keyof CoinConfig, value: number | boolean) => {
        setCoins(prev => ({
            ...prev,
            [coin]: { ...prev[coin], [field]: value }
        }));
        setSaved(false);
    };

    const handleReset = () => {
        if (confirm("Restaurar todas as configurações para o padrão?")) {
            setCoins(DEFAULT_COINS);
            setInitialBalance(10000);
            setPositionSize(100);
            setUseCompound(false);
            localStorage.removeItem("gastor_settings");
            setSaved(false);
        }
    };

    const handleSave = () => {
        const settings = {
            coins,
            initialBalance,
            positionSize,
            useCompound
        };
        localStorage.setItem("gastor_settings", JSON.stringify(settings));
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    return (
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white">Configurações</h1>
                <p className="text-slate-400 mt-1">
                    Ajuste taxas, slippage e parâmetros de execução
                </p>
            </div>

            {/* General Settings */}
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-6 mb-6">
                <h2 className="text-lg font-semibold text-white mb-4">Parâmetros Gerais</h2>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                    <div>
                        <label className="block text-sm text-slate-400 mb-1">
                            Capital Inicial ($)
                        </label>
                        <input
                            type="number"
                            value={initialBalance}
                            onChange={(e) => setInitialBalance(Number(e.target.value))}
                            min={100}
                            className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-white"
                        />
                    </div>

                    <div>
                        <label className="block text-sm text-slate-400 mb-1">
                            Tamanho da Posição (%)
                        </label>
                        <input
                            type="number"
                            value={positionSize}
                            onChange={(e) => setPositionSize(Number(e.target.value))}
                            min={1}
                            max={100}
                            className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-white"
                        />
                    </div>

                    <div className="flex items-end">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={useCompound}
                                onChange={(e) => setUseCompound(e.target.checked)}
                                className="rounded bg-slate-800 border-slate-600 text-emerald-500"
                            />
                            <span className="text-slate-300">Juros Compostos</span>
                        </label>
                    </div>
                </div>
            </div>

            {/* Coin Settings */}
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-6 mb-6">
                <h2 className="text-lg font-semibold text-white mb-4">Taxas por Moeda</h2>

                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="text-left text-slate-400 text-sm border-b border-slate-700">
                                <th className="pb-3 pr-4">Moeda</th>
                                <th className="pb-3 pr-4">Ativo</th>
                                <th className="pb-3 pr-4">Taxa Exchange (%)</th>
                                <th className="pb-3 pr-4">Slippage (%)</th>
                                <th className="pb-3">Taxa Total (%)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {Object.entries(coins).map(([coin, config]) => (
                                <tr key={coin} className="border-b border-slate-800">
                                    <td className="py-3 pr-4 text-white font-medium">{coin}</td>
                                    <td className="py-3 pr-4">
                                        <input
                                            type="checkbox"
                                            checked={config.enabled}
                                            onChange={(e) => handleCoinChange(coin, "enabled", e.target.checked)}
                                            className="rounded bg-slate-800 border-slate-600 text-emerald-500"
                                        />
                                    </td>
                                    <td className="py-3 pr-4">
                                        <input
                                            type="number"
                                            value={config.fee}
                                            onChange={(e) => handleCoinChange(coin, "fee", Number(e.target.value))}
                                            step={0.01}
                                            min={0}
                                            max={1}
                                            disabled={!config.enabled}
                                            className="w-20 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-white text-sm disabled:opacity-50"
                                        />
                                    </td>
                                    <td className="py-3 pr-4">
                                        <input
                                            type="number"
                                            value={config.slippage}
                                            onChange={(e) => handleCoinChange(coin, "slippage", Number(e.target.value))}
                                            step={0.01}
                                            min={0}
                                            max={2}
                                            disabled={!config.enabled}
                                            className="w-20 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-white text-sm disabled:opacity-50"
                                        />
                                    </td>
                                    <td className={`py-3 ${config.enabled ? "text-emerald-400" : "text-slate-500"}`}>
                                        {(config.fee + config.slippage).toFixed(2)}%
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <p className="text-xs text-slate-500 mt-4">
                    A taxa total é cobrada em cada operação (compra e venda). Um trade completo tem custo de 2× a taxa total.
                </p>
            </div>

            {/* Save Button */}
            {/* Save Button */}
            <div className="flex justify-end gap-3">
                <button
                    onClick={handleReset}
                    className="px-4 py-2 bg-slate-800 hover:bg-red-900/40 text-slate-300 hover:text-red-200 border border-slate-700 hover:border-red-800 font-medium rounded-md transition-colors"
                >
                    Restaurar Padrões
                </button>
                <button
                    onClick={handleSave}
                    className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-md transition-colors"
                >
                    {saved ? "Salvo!" : "Salvar Configurações"}
                </button>
            </div>
        </div>
    );
}
