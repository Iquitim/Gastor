"use client";

interface Trade {
    id: number;
    entry_date: string;
    entry_price: number;
    exit_date?: string;
    exit_price?: number;
    size: number;
    fee?: number;
    pnl: number;
    pnl_pct?: number;
    type: "BUY" | "SELL";
    exit_balance?: number;
}

interface TradesTableProps {
    trades: Trade[];
}

export default function TradesTable({ trades }: TradesTableProps) {
    if (!trades || trades.length === 0) return null;

    // Helper to format currency
    const formatCurrency = (val: number, minimumFractionDigits = 2) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits
        }).format(val);
    };

    return (
        <div className="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden">
            <div className="p-4 border-b border-slate-800">
                <h3 className="text-lg font-semibold text-white">Histórico de Operações</h3>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                    <thead className="text-xs text-slate-400 uppercase bg-slate-800/50">
                        <tr>
                            <th className="px-4 py-3">#</th>
                            <th className="px-4 py-3">Entrada</th>
                            <th className="px-4 py-3">Saída</th>
                            <th className="px-4 py-3 text-right">Investido</th>
                            <th className="px-4 py-3 text-right">Taxas</th>
                            <th className="px-4 py-3 text-right">PnL Líq.</th>
                            <th className="px-4 py-3 text-right">Saldo Total</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                        {trades.map((trade) => {
                            const entryDate = new Date(trade.entry_date).toLocaleDateString() + " " + new Date(trade.entry_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                            const exitDate = trade.exit_date
                                ? new Date(trade.exit_date).toLocaleDateString() + " " + new Date(trade.exit_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                                : "Em aberto";
                            const pnlColor = trade.pnl >= 0 ? "text-emerald-400" : "text-red-400";
                            const fee = trade.fee || 0;

                            return (
                                <tr key={trade.id} className="hover:bg-slate-800/50 transition-colors">
                                    <td className="px-4 py-3 font-medium text-slate-400">{trade.id}</td>
                                    <td className="px-4 py-3">
                                        <div className="text-white">{entryDate}</div>
                                        <div className="text-slate-500 text-xs">@ {formatCurrency(trade.entry_price)}</div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="text-white">{exitDate}</div>
                                        {trade.exit_price && (
                                            <div className="text-slate-500 text-xs">@ {formatCurrency(trade.exit_price)}</div>
                                        )}
                                    </td>
                                    <td className="px-4 py-3 text-right text-slate-300">
                                        {formatCurrency(trade.size || 0, 0)}
                                    </td>
                                    <td className="px-4 py-3 text-right text-red-400/80">
                                        -{formatCurrency(fee)}
                                    </td>
                                    <td className={`px-4 py-3 text-right font-bold ${pnlColor}`}>
                                        {trade.pnl >= 0 ? "+" : ""}{formatCurrency(trade.pnl)}
                                        <span className="block text-xs font-normal opacity-70">
                                            {trade.pnl_pct?.toFixed(2)}%
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-right font-medium text-white">
                                        {formatCurrency(trade.exit_balance || 0)}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
