import { Session } from "./types";
import { MousePointerClick } from "lucide-react";

interface SessionListProps {
    sessions: Session[];
    selectedSessionId: number | null;
    onSessionSelect: (id: number) => void;
    formatCurrency: (value: number) => string;
    getPnLColor: (pnl: number) => string;
}

export default function SessionList({
    sessions,
    selectedSessionId,
    onSessionSelect,
    formatCurrency,
    getPnLColor
}: SessionListProps) {
    return (
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
                            onClick={() => onSessionSelect(session.id)}
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
                                <span className="text-gray-500 text-xs font-mono">
                                    {session.slot ? `Slot ${session.slot}` : `#${session.id}`}
                                </span>
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
    );
}
