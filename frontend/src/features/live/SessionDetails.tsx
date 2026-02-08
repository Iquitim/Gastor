"use client";

import { useMemo, useState } from "react";
import { MousePointerClick } from "lucide-react";
import InteractiveChart from "./InteractiveChart";
import { SessionDetails as SessionDetailsType } from "./types";

interface SessionDetailsProps {
    selectedSession: SessionDetailsType | null;
    loading: boolean;
    formatCurrency: (value: number) => string;
    formatDate: (dateStr: string | null) => string;
    getPnLColor: (pnl: number) => string;
    onStopSession: (id: number) => void;
    onDeleteSession: (id: number, force: boolean) => void;
    onResetSession: (id: number) => void;
    onTransaction: (type: "deposit" | "withdrawal", sessionId: number) => void;
}

export default function SessionDetails({
    selectedSession,
    loading,
    formatCurrency,
    formatDate,
    getPnLColor,
    onStopSession,
    onDeleteSession,
    onResetSession,
    onTransaction
}: SessionDetailsProps) {

    if (!selectedSession) {
        return (
            <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-12 text-center flex flex-col items-center justify-center">
                <MousePointerClick className="w-16 h-16 text-gray-600 mb-4" />
                <p className="text-gray-400">Selecione uma sessão para ver os detalhes</p>
            </div>
        );
    }

    // Calcula patrimônio e equity para display
    const equity = useMemo(() => {
        const cash = selectedSession.session.current_balance;
        const qty = selectedSession.position?.quantity || 0;
        const currentPrice = selectedSession.triggers?.current_price || (selectedSession.position?.current_price || 0);
        return cash + (qty * currentPrice);
    }, [selectedSession]);

    const pnlGlobal = useMemo(() => {
        const initial = selectedSession.session.initial_balance;
        return equity - initial;
    }, [equity, selectedSession]);

    const pnlGlobalPct = useMemo(() => {
        const initial = selectedSession.session.initial_balance;
        return (pnlGlobal / initial) * 100;
    }, [pnlGlobal, selectedSession]);

    return (
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
                                onClick={() => onStopSession(selectedSession.session.id)}
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
                                        onDeleteSession(selectedSession.session.id, true);
                                    }
                                } else {
                                    if (confirm("Tem certeza que deseja deletar esta sessão?")) {
                                        onDeleteSession(selectedSession.session.id, false);
                                    }
                                }
                            }}
                            disabled={loading}
                            className="px-3 py-1.5 bg-red-700 hover:bg-red-600 text-white text-sm rounded-lg"
                        >
                            Deletar
                        </button>
                        <button
                            onClick={() => onResetSession(selectedSession.session.id)}
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
                            {formatCurrency(equity)}
                        </p>
                    </div>

                    {/* Global PnL Card */}
                    <div className="bg-black/30 rounded-lg p-3">
                        <p className="text-gray-400 text-xs">PnL Global</p>
                        <p className={`text-lg font-bold ${getPnLColor(pnlGlobal)}`}>
                            {pnlGlobal >= 0 ? "+" : ""}
                            {formatCurrency(pnlGlobal)} ({pnlGlobalPct.toFixed(2)}%)
                        </p>
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
                        onClick={() => onTransaction("deposit", selectedSession.session.id)}
                        className="flex-1 px-4 py-2 bg-green-900/50 hover:bg-green-900/70 border border-green-500/30 text-green-400 rounded-lg"
                    >
                        Depositar
                    </button>
                    <button
                        onClick={() => onTransaction("withdrawal", selectedSession.session.id)}
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
    );
}
