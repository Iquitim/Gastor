import { Strategy, Session } from "./types";
import Link from "next/link";

interface NewSessionFormProps {
    strategies: Strategy[];
    sessions: Session[];
    settings: any;
    selectedStrategy: string;
    selectedSlot: number;
    loading: boolean;
    onStrategyChange: (slug: string) => void;
    onSlotChange: (slot: number) => void;
    onStart: () => void;
    onCancel: () => void;
}

export default function NewSessionForm({
    strategies,
    sessions,
    settings,
    selectedStrategy,
    selectedSlot,
    loading,
    onStrategyChange,
    onSlotChange,
    onStart,
    onCancel
}: NewSessionFormProps) {
    return (
        <div className="mb-6 p-6 bg-gray-800/50 border border-gray-700 rounded-xl">
            <h2 className="text-lg font-semibold text-white mb-4">Iniciar Nova Sessão</h2>

            <div className="grid md:grid-cols-2 gap-4">
                {/* Strategy */}
                <div>
                    <label className="block text-gray-400 text-sm mb-2">Estratégia</label>
                    <select
                        value={selectedStrategy}
                        onChange={(e) => onStrategyChange(e.target.value)}
                        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white"
                    >
                        <option value="">Selecione...</option>
                        {strategies.map((s) => (
                            <option key={s.slug} value={s.slug}>
                                {s.name}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Slot Selection */}
                <div>
                    <label className="block text-gray-400 text-sm mb-2">Slot da Sessão</label>
                    <select
                        value={selectedSlot}
                        onChange={(e) => onSlotChange(Number(e.target.value))}
                        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white"
                    >
                        {[1, 2, 3, 4, 5].map((slot) => {
                            const activeSession = sessions.find(s => s.id && (s as any).slot === slot && s.status === 'running');
                            return (
                                <option key={slot} value={slot}>
                                    Slot {slot} {activeSession ? `(Ocupado: ${activeSession.strategy_slug})` : "(Livre)"}
                                </option>
                            );
                        })}
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                        Selecionar um slot ocupado irá substituir a sessão anterior.
                    </p>
                </div>
            </div>

            <div className="mt-4 p-3 bg-blue-900/20 border border-blue-500/30 rounded-lg">
                <p className="text-blue-400 text-sm">
                    📍 Configurações carregadas de Settings:
                </p>
                <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                    <div>
                        <span className="text-gray-400">Par:</span>{" "}
                        <strong className="text-white">{settings.paperTradingCoin}</strong>
                    </div>
                    <div>
                        <span className="text-gray-400">Timeframe:</span>{" "}
                        <strong className="text-white">{settings.paperTradingTimeframe}</strong>
                    </div>
                    <div>
                        <span className="text-gray-400">Saldo:</span>{" "}
                        <strong className="text-white">${settings.paperTradingBalance?.toLocaleString()}</strong>
                    </div>
                    <div>
                        <span className="text-gray-400">Telegram:</span>{" "}
                        <strong className={settings.telegramChatId ? "text-green-400" : "text-gray-500"}>
                            {settings.telegramChatId ? "✓ Configurado" : "Não configurado"}
                        </strong>
                    </div>
                </div>
                <p className="text-blue-300 text-xs mt-2">
                    <Link href="/user/panel" className="underline hover:text-blue-200">Alterar configurações →</Link>
                </p>
            </div>

            <div className="flex gap-3 mt-4">
                <button
                    onClick={onStart}
                    disabled={loading || !selectedStrategy}
                    className="px-6 py-2 bg-green-600 hover:bg-green-500 text-white font-medium rounded-lg disabled:opacity-50"
                >
                    {loading ? "⏳ Iniciando..." : "🚀 Iniciar"}
                </button>
                <button
                    onClick={onCancel}
                    className="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg"
                >
                    Cancelar
                </button>
            </div>
        </div>
    );
}
