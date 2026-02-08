"use client";

import { useState, useEffect } from "react";
import api from "../../../lib/api";
import ProtectedRoute from "../../../components/ProtectedRoute";

function UserPanelContent() {
    const [activeTab, setActiveTab] = useState("keys");
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

    // Data States
    const [keys, setKeys] = useState<any[]>([]);
    const [telegram, setTelegram] = useState<any>({ configured: false, chat_id: "", is_active: true });
    const [strategies, setStrategies] = useState<any[]>([]);
    const [config, setConfig] = useState<any>({
        exchange_fee: 0.001,
        slippage_overrides: {},
        backtest_initial_balance: 10000,
        backtest_use_compound: true,
        backtest_position_size: 1,
        paper_initial_balance: 10000,
        paper_default_coin: "SOL/USDT",
        paper_default_timeframe: "1h",
        paper_use_compound: true,
        system_defaults: {},
        supported_coins: []
    });

    const [newKey, setNewKey] = useState({ label: "", api_key: "", api_secret: "" });
    const [newSlippage, setNewSlippage] = useState({ coin: "SOL/USDT", value: 0.001 });

    useEffect(() => {
        loadData();
    }, [activeTab]);

    const loadData = async () => {
        setLoading(true);
        try {
            if (activeTab === "keys") {
                const data = await api.getUserKeys();
                setKeys(data);
            } else if (activeTab === "telegram") {
                const data = await api.getTelegramConfig();
                setTelegram(data);
            } else if (activeTab === "config") {
                const data = await api.getUserConfig();
                setConfig(data);
                // Sync with current telegram state
                syncToLocalStorage(data, telegram.chat_id || "");
            } else if (activeTab === "strategies") {
                const data = await api.getUserStrategies();
                setStrategies(data);
            }
        } catch (err: any) {
            console.error(err);
            showMessage(err.message || "Erro ao carregar dados", "error");
        } finally {
            setLoading(false);
        }
    };

    const showMessage = (text: string, type: "success" | "error") => {
        setMessage({ text, type });
        setTimeout(() => setMessage(null), 5000);
    };

    // --- Handlers ---

    const handleAddKey = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await api.addUserKey({ ...newKey, exchange: "binance" });
            showMessage("Chave adicionada com sucesso!", "success");
            setNewKey({ label: "", api_key: "", api_secret: "" });
            loadData();
        } catch (err: any) {
            showMessage(err.message, "error");
        }
    };

    const handleDeleteKey = async (id: number) => {
        if (!confirm("Tem certeza?")) return;
        try {
            await api.deleteUserKey(id);
            showMessage("Chave removida!", "success");
            loadData();
        } catch (err: any) {
            showMessage(err.message, "error");
        }
    };

    const handleSaveTelegram = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await api.updateTelegramConfig(telegram);
            showMessage("Configuração do Telegram salva!", "success");
        } catch (err: any) {
            showMessage(err.message, "error");
        }
    };

    const handleTestTelegram = async () => {
        try {
            await api.testTelegram();
            showMessage("Mensagem de teste enviada! Verifique seu Telegram.", "success");
        } catch (err: any) {
            showMessage(err.message, "error");
        }
    };

    const syncToLocalStorage = (newConfig: any, telegramId: string) => {
        try {
            const settings = {
                initialBalance: newConfig.backtest_initial_balance,
                useCompound: newConfig.backtest_use_compound,
                paperTradingBalance: newConfig.paper_initial_balance,
                paperTradingCoin: newConfig.paper_default_coin,
                paperTradingTimeframe: newConfig.paper_default_timeframe,
                telegramChatId: telegramId,
                // Fees
                exchangeFee: newConfig.exchange_fee,
                slippageOverrides: newConfig.slippage_overrides
            };
            localStorage.setItem("gastor_settings", JSON.stringify(settings));
        } catch (e) {
            console.error("Failed to sync settings locally", e);
        }
    };

    const handleSaveConfig = async () => {
        try {
            // Remove 'system_defaults' and 'supported_coins' before sending
            const { system_defaults, supported_coins, ...dataToSend } = config;
            await api.updateUserConfig(dataToSend);

            // Sync to local storage for other components
            syncToLocalStorage(config, telegram.chat_id || "");

            showMessage("Configurações atualizadas!", "success");
        } catch (err: any) {
            showMessage(err.message, "error");
        }
    };

    return (
        <div className="max-w-6xl mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold text-white mb-6">Painel do Usuário</h1>

            {message && (
                <div className={`p-4 mb-6 rounded ${message.type === "success" ? "bg-emerald-500/20 text-emerald-300" : "bg-red-500/20 text-red-300"}`}>
                    {message.text}
                </div>
            )}

            {/* Tabs */}
            <div className="flex space-x-4 mb-8 border-b border-slate-700 overflow-x-auto">
                {[
                    { id: "keys", label: "🔑 Chaves API", desc: "Binance" },
                    { id: "config", label: "⚙️ Configurações", desc: "Backtest & Paper Trading" },
                    { id: "telegram", label: "📱 Notificações", desc: "Alertas" },
                    { id: "strategies", label: "🛠️ Estratégias", desc: "Meus algoritmos" },
                ].map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`pb-4 px-4 text-left transition-colors whitespace-nowrap ${activeTab === tab.id
                            ? "border-b-2 border-emerald-500 text-white"
                            : "text-slate-400 hover:text-slate-200"
                            }`}
                    >
                        <div className="font-medium text-sm md:text-base">{tab.label}</div>
                        <div className="text-xs opacity-70 hidden md:block">{tab.desc}</div>
                    </button>
                ))}
            </div>

            {loading && <div className="text-center py-8 text-slate-500">Carregando...</div>}

            {!loading && (
                <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">

                    {/* KEYS TAB */}
                    {activeTab === "keys" && (
                        <div>
                            <h2 className="text-xl font-semibold text-white mb-4">Gerenciar Chaves de API</h2>
                            <p className="text-slate-400 mb-6 text-sm">
                                Suas chaves são criptografadas (AES-256) antes de serem salvas. Ninguém, nem os administradores, podem vê-las.
                            </p>

                            {/* List */}
                            <div className="space-y-3 mb-8">
                                {keys.map((k) => (
                                    <div key={k.id} className="flex items-center justify-between p-4 bg-slate-800 rounded-lg">
                                        <div>
                                            <div className="font-bold text-white">{k.label || "Sem nome"}</div>
                                            <div className="text-xs text-slate-400 font-mono">Binance • {k.api_key_masked}</div>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <span className={`px-2 py-0.5 text-xs rounded ${k.is_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                                                {k.is_active ? 'Ativa' : 'Inativa'}
                                            </span>
                                            <button
                                                onClick={() => handleDeleteKey(k.id)}
                                                className="text-red-400 hover:text-red-300 text-sm underline"
                                            >
                                                Remover
                                            </button>
                                        </div>
                                    </div>
                                ))}
                                {keys.length === 0 && <div className="text-slate-500 italic">Nenhuma chave cadastrada.</div>}
                            </div>

                            {/* Add Form */}
                            <div className="border-t border-slate-700 pt-6">
                                <h3 className="text-lg font-medium text-white mb-4">Adicionar Nova Chave</h3>
                                <form onSubmit={handleAddKey} className="grid gap-4 max-w-lg">
                                    <input
                                        type="text"
                                        placeholder="Apelido (ex: Conta Principal)"
                                        value={newKey.label}
                                        onChange={(e) => setNewKey({ ...newKey, label: e.target.value })}
                                        className="bg-slate-800 border-slate-700 rounded px-3 py-2 text-white"
                                        required
                                    />
                                    <input
                                        type="text"
                                        placeholder="API Key (Binance)"
                                        value={newKey.api_key}
                                        onChange={(e) => setNewKey({ ...newKey, api_key: e.target.value })}
                                        className="bg-slate-800 border-slate-700 rounded px-3 py-2 text-white font-mono"
                                        required
                                    />
                                    <input
                                        type="password"
                                        placeholder="Secret Key"
                                        value={newKey.api_secret}
                                        onChange={(e) => setNewKey({ ...newKey, api_secret: e.target.value })}
                                        className="bg-slate-800 border-slate-700 rounded px-3 py-2 text-white font-mono"
                                        required
                                    />
                                    <button type="submit" className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2 rounded">
                                        Salvar com Segurança 🔒
                                    </button>
                                </form>
                            </div>
                        </div>
                    )}

                    {/* TELEGRAM TAB */}
                    {activeTab === "telegram" && (
                        <div>
                            <h2 className="text-xl font-semibold text-white mb-4">Configurar Notificações</h2>
                            <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded text-sm text-blue-200">
                                1. Inicie uma conversa com o bot <b>@SeuBotOuGastorBot</b><br />
                                2. Envie <code>/start</code><br />
                                3. Cole seu <b>Chat ID</b> abaixo.
                            </div>

                            <form onSubmit={handleSaveTelegram} className="max-w-lg space-y-4">
                                <div>
                                    <label className="block text-sm text-slate-400 mb-1">Chat ID</label>
                                    <input
                                        type="text"
                                        value={telegram.chat_id || ""}
                                        onChange={(e) => setTelegram({ ...telegram, chat_id: e.target.value })}
                                        className="w-full bg-slate-800 border-slate-700 rounded px-3 py-2 text-white font-mono"
                                        placeholder="123456789"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm text-slate-400 mb-1">Bot Token Personalizado (Opcional)</label>
                                    <input
                                        type="password"
                                        placeholder={telegram.bot_token_masked || "Deixe em branco para usar o bot padrão"}
                                        onChange={(e) => setTelegram({ ...telegram, bot_token: e.target.value })}
                                        className="w-full bg-slate-800 border-slate-700 rounded px-3 py-2 text-white font-mono"
                                    />
                                    <p className="text-xs text-slate-500 mt-1">Só preencha se quiser usar seu próprio bot.</p>
                                </div>

                                <div className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={telegram.is_active}
                                        onChange={(e) => setTelegram({ ...telegram, is_active: e.target.checked })}
                                        className="rounded bg-slate-700 border-slate-600"
                                    />
                                    <label className="text-white text-sm">Ativar notificações</label>
                                </div>

                                <div className="flex gap-4 pt-2">
                                    <button type="submit" className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2 rounded">
                                        Salvar Configuração
                                    </button>
                                    <button
                                        type="button"
                                        onClick={handleTestTelegram}
                                        className="px-4 bg-slate-700 hover:bg-slate-600 text-white rounded border border-slate-600"
                                    >
                                        🔔 Testar
                                    </button>
                                </div>
                            </form>
                        </div>
                    )}

                    {/* CONFIG TAB */}
                    {activeTab === "config" && (
                        <div>
                            <div className="flex justify-between items-center mb-6">
                                <div>
                                    <h2 className="text-xl font-semibold text-white">Configurações Gerais</h2>
                                    <p className="text-slate-400 text-sm">Defina padrões para simulação e execução.</p>
                                </div>
                                <button
                                    onClick={handleSaveConfig}
                                    className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg shadow-lg hover:shadow-emerald-500/20 transition-all"
                                >
                                    Salvar Tudo
                                </button>
                            </div>

                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                                {/* Backtest Settings */}
                                <div className="bg-slate-800 rounded-lg p-5 border border-slate-700 shadow-sm">
                                    <h3 className="text-lg font-medium text-emerald-400 mb-4 flex items-center gap-2">
                                        📈 Backtest
                                    </h3>
                                    <div className="space-y-4">
                                        <div>
                                            <label className="block text-sm text-slate-400 mb-1">Capital Inicial ($)</label>
                                            <input
                                                type="number"
                                                value={config.backtest_initial_balance}
                                                onChange={(e) => setConfig({ ...config, backtest_initial_balance: parseFloat(e.target.value) })}
                                                className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm text-slate-400 mb-1">Tamanho da Posição (0.1 a 1.0)</label>
                                            <div className="flex items-center gap-2">
                                                <input
                                                    type="number"
                                                    step="0.01"
                                                    max="1"
                                                    min="0.01"
                                                    value={config.backtest_position_size}
                                                    onChange={(e) => setConfig({ ...config, backtest_position_size: parseFloat(e.target.value) })}
                                                    className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white"
                                                />
                                                <span className="text-slate-400 text-sm">{(config.backtest_position_size * 100).toFixed(0)}%</span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2 pt-2">
                                            <input
                                                type="checkbox"
                                                checked={config.backtest_use_compound}
                                                onChange={(e) => setConfig({ ...config, backtest_use_compound: e.target.checked })}
                                                className="rounded bg-slate-700 border-slate-600 text-emerald-500 focus:ring-emerald-500 focus:ring-offset-slate-800"
                                            />
                                            <label className="text-slate-300 text-sm">Usar Juros Compostos</label>
                                        </div>
                                    </div>
                                </div>

                                {/* Paper Trading Settings */}
                                <div className="bg-slate-800 rounded-lg p-5 border border-slate-700 shadow-sm">
                                    <h3 className="text-lg font-medium text-blue-400 mb-4 flex items-center gap-2">
                                        🎮 Paper Trading
                                    </h3>
                                    <div className="space-y-4">
                                        <div>
                                            <label className="block text-sm text-slate-400 mb-1">Capital Inicial ($)</label>
                                            <input
                                                type="number"
                                                value={config.paper_initial_balance}
                                                onChange={(e) => setConfig({ ...config, paper_initial_balance: parseFloat(e.target.value) })}
                                                className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white"
                                            />
                                        </div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <label className="block text-sm text-slate-400 mb-1">Moeda Padrão</label>
                                                <select
                                                    value={config.paper_default_coin}
                                                    onChange={(e) => setConfig({ ...config, paper_default_coin: e.target.value })}
                                                    className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white"
                                                >
                                                    {config.supported_coins?.map((coin: string) => (
                                                        <option key={coin} value={coin}>{coin}</option>
                                                    ))}
                                                </select>
                                            </div>
                                            <div>
                                                <label className="block text-sm text-slate-400 mb-1">Timeframe</label>
                                                <select
                                                    value={config.paper_default_timeframe}
                                                    onChange={(e) => setConfig({ ...config, paper_default_timeframe: e.target.value })}
                                                    className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white"
                                                >
                                                    {["1m", "5m", "15m", "1h", "4h", "1d"].map((tf) => (
                                                        <option key={tf} value={tf}>{tf}</option>
                                                    ))}
                                                </select>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2 pt-2">
                                            <input
                                                type="checkbox"
                                                checked={config.paper_use_compound}
                                                onChange={(e) => setConfig({ ...config, paper_use_compound: e.target.checked })}
                                                className="rounded bg-slate-700 border-slate-600 text-blue-500 focus:ring-blue-500 focus:ring-offset-slate-800"
                                            />
                                            <label className="text-slate-300 text-sm">Usar Juros Compostos</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Fees Section */}
                            <div className="mt-8 pt-8 border-t border-slate-700">
                                <h3 className="text-lg font-medium text-white mb-4">Taxas e Slippage</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    <div className="p-4 bg-slate-800 rounded-lg border border-slate-700">
                                        <label className="block text-xs text-slate-400 mb-1">Taxa da Exchange Maker/Taker</label>
                                        <div className="flex items-center gap-2">
                                            <input
                                                type="number"
                                                step="0.0001"
                                                value={config.exchange_fee}
                                                onChange={(e) => setConfig({ ...config, exchange_fee: parseFloat(e.target.value) })}
                                                className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white"
                                            />
                                            <span className="text-slate-400 text-sm">{(config.exchange_fee * 100).toFixed(2)}%</span>
                                        </div>
                                    </div>

                                    {config.supported_coins?.map((coin: string) => {
                                        const defaultVal = config.system_defaults?.[coin] || 0.003;
                                        const overrideVal = config.slippage_overrides?.[coin];
                                        const currentVal = overrideVal !== undefined ? overrideVal : defaultVal;
                                        const isModified = overrideVal !== undefined;

                                        return (
                                            <div key={coin} className={`p-4 rounded-lg border ${isModified ? 'bg-slate-800 border-emerald-500/50' : 'bg-slate-800 border-slate-700'}`}>
                                                <div className="flex justify-between items-center mb-2">
                                                    <span className="font-bold text-white text-sm">{coin}</span>
                                                    {isModified && <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded">Modificado</span>}
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <input
                                                        type="number"
                                                        step="0.0001"
                                                        value={currentVal}
                                                        onChange={(e) => {
                                                            const newVal = parseFloat(e.target.value);
                                                            setConfig((prev: any) => ({
                                                                ...prev,
                                                                slippage_overrides: {
                                                                    ...prev.slippage_overrides,
                                                                    [coin]: newVal
                                                                }
                                                            }));
                                                        }}
                                                        className="w-full bg-slate-900 border-slate-600 rounded px-2 py-1 text-sm text-white focus:border-emerald-500"
                                                    />
                                                    <span className="text-xs text-slate-500 w-10 text-right">
                                                        {(currentVal * 100).toFixed(2)}%
                                                    </span>
                                                </div>
                                                <div className="mt-1 text-[10px] text-slate-500 text-right">
                                                    Default: {defaultVal}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>
                    )}


                    {/* STRATEGIES TAB */}
                    {activeTab === "strategies" && (
                        <div>
                            <div className="flex justify-between items-center mb-6">
                                <div>
                                    <h2 className="text-xl font-semibold text-white">Minhas Estratégias</h2>
                                    <p className="text-slate-400 text-sm">Gerencie os algoritmos criados no Strategy Builder.</p>
                                </div>
                                <a href="/strategies/builder" className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg text-sm">
                                    + Nova Estratégia
                                </a>
                            </div>

                            <div className="space-y-4">
                                {strategies.length === 0 ? (
                                    <div className="text-center py-12 bg-slate-800 rounded-lg border border-slate-700 border-dashed">
                                        <div className="text-4xl mb-4">🧪</div>
                                        <h3 className="text-lg font-medium text-white mb-2">Nenhuma estratégia encontrada</h3>
                                        <p className="text-slate-400 mb-6">Crie sua primeira estratégia no Builder para começar.</p>
                                        <a href="/strategies/builder" className="text-emerald-400 hover:text-emerald-300 underline">Ir para o Builder &rarr;</a>
                                    </div>
                                ) : (
                                    strategies.map((s) => (
                                        <div key={s.id} className="p-4 bg-slate-800 rounded-lg border border-slate-700 hover:border-emerald-500/50 transition-colors">
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <h3 className="font-bold text-white text-lg">{s.name}</h3>
                                                    {s.description && <p className="text-sm text-slate-400 mb-2">{s.description}</p>}
                                                    <div className="flex gap-2 text-xs font-mono mt-2">
                                                        <span className="px-2 py-1 bg-slate-900 rounded text-slate-300">{s.coin}</span>
                                                        <span className="px-2 py-1 bg-slate-900 rounded text-slate-300">{s.timeframe}</span>
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <div className="text-xs text-slate-500 mb-1">Criada em</div>
                                                    <div className="text-sm text-slate-300 mb-3">{new Date(s.created_at).toLocaleDateString()}</div>

                                                    <div className="flex gap-2 justify-end">
                                                        <a
                                                            href={`/strategies/builder?load=${s.id}`}
                                                            className="px-3 py-1 bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 text-xs rounded border border-blue-600/30 transition-colors"
                                                        >
                                                            Editar
                                                        </a>
                                                        <button
                                                            onClick={async () => {
                                                                if (confirm(`Tem certeza que deseja excluir "${s.name}"?`)) {
                                                                    try {
                                                                        await api.deleteCustomStrategy(s.id);
                                                                        loadData(); // Refresh list
                                                                        showMessage("Estratégia removida!", "success");
                                                                    } catch (e: any) {
                                                                        showMessage("Erro ao excluir: " + e.message, "error");
                                                                    }
                                                                }
                                                            }}
                                                            className="px-3 py-1 bg-red-600/20 text-red-400 hover:bg-red-600/30 text-xs rounded border border-red-600/30 transition-colors"
                                                        >
                                                            Excluir
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    )}

                </div>
            )}
        </div>
    );
}

export default function UserPanelPage() {
    return (
        <ProtectedRoute>
            <UserPanelContent />
        </ProtectedRoute>
    );
}
