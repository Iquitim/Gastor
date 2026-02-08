"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import { useRouter } from "next/navigation";

export default function AdminDashboard() {
    const { user, isLoading } = useAuth();
    const router = useRouter();

    const [activeTab, setActiveTab] = useState("overview");
    const [stats, setStats] = useState<any>(null);
    const [users, setUsers] = useState<any[]>([]);
    const [config, setConfig] = useState<any>(null);
    const [loadingConfig, setLoadingConfig] = useState(false);

    // Protect route
    useEffect(() => {
        if (!isLoading) {
            if (!user || user.role !== "admin") {
                router.push("/live"); // Redirect non-admins
            } else {
                fetchData();
            }
        }
    }, [user, isLoading, router]);

    const fetchData = async () => {
        try {
            const [statsData, usersData, configData] = await Promise.all([
                api.getSystemStats(),
                api.getUsers(),
                api.getSystemConfig()
            ]);
            setStats(statsData);
            setUsers(usersData);
            setConfig(configData);
        } catch (err) {
            console.error("Failed to fetch admin data", err);
        }
    };

    const handleBlockUnblock = async (userId: number, is_active: boolean) => {
        try {
            if (is_active) {
                await api.blockUser(userId);
            } else {
                await api.unblockUser(userId);
            }
            // Refresh users
            const updatedUsers = await api.getUsers();
            setUsers(updatedUsers);
        } catch (e) {
            alert("Falha ao atualizar status do usuário");
        }
    };

    const handleUpdateConfig = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            setLoadingConfig(true);
            await api.updateSystemConfig({ max_users: config.max_users });
            alert("Configuração atualizada!");
        } catch (e) {
            alert("Falha ao atualizar configuração");
        } finally {
            setLoadingConfig(false);
        }
    }

    if (isLoading || !user || user.role !== "admin") {
        return <div className="flex h-screen items-center justify-center bg-slate-950 text-emerald-500">Carregando Painel Admin...</div>;
    }

    return (
        <div className="min-h-screen bg-slate-950 p-6 text-slate-100">
            <div className="mb-8 flex items-center justify-between">
                <h1 className="text-3xl font-bold text-emerald-400">🛡️ Centro de Comando Admin</h1>
                <div className="flex space-x-2">
                    <button
                        onClick={() => setActiveTab("overview")}
                        className={`px-4 py-2 rounded-lg transition-colors ${activeTab === "overview" ? "bg-emerald-600 text-white" : "bg-slate-800 hover:bg-slate-700"}`}
                    >
                        Visão Geral
                    </button>
                    <button
                        onClick={() => setActiveTab("users")}
                        className={`px-4 py-2 rounded-lg transition-colors ${activeTab === "users" ? "bg-emerald-600 text-white" : "bg-slate-800 hover:bg-slate-700"}`}
                    >
                        Usuários e Governança
                    </button>
                    <button
                        onClick={() => setActiveTab("settings")}
                        className={`px-4 py-2 rounded-lg transition-colors ${activeTab === "settings" ? "bg-emerald-600 text-white" : "bg-slate-800 hover:bg-slate-700"}`}
                    >
                        Configurações do Sistema
                    </button>
                </div>
            </div>

            {/* OVERVIEW TAB */}
            {activeTab === "overview" && stats && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div className="bg-slate-900 p-6 rounded-xl border border-slate-800">
                        <h3 className="text-slate-400 text-sm font-medium uppercase">Sessões Ativas</h3>
                        <p className="text-3xl font-bold text-emerald-400 mt-2">{stats.active_sessions}</p>
                    </div>
                    <div className="bg-slate-900 p-6 rounded-xl border border-slate-800">
                        <h3 className="text-slate-400 text-sm font-medium uppercase">Usuários Ativos</h3>
                        <p className="text-3xl font-bold text-blue-400 mt-2">{stats.active_users}</p>
                    </div>
                    <div className="bg-slate-900 p-6 rounded-xl border border-slate-800">
                        <h3 className="text-slate-400 text-sm font-medium uppercase">Uso de CPU</h3>
                        <p className="text-3xl font-bold text-purple-400 mt-2">{stats.cpu_usage}%</p>
                        <div className="w-full bg-slate-800 h-2 mt-2 rounded-full overflow-hidden">
                            <div className="bg-purple-500 h-full" style={{ width: `${stats.cpu_usage}%` }}></div>
                        </div>
                    </div>
                    <div className="bg-slate-900 p-6 rounded-xl border border-slate-800">
                        <h3 className="text-slate-400 text-sm font-medium uppercase">Uso de RAM</h3>
                        <p className="text-3xl font-bold text-orange-400 mt-2">{stats.ram_usage}%</p>
                        <div className="w-full bg-slate-800 h-2 mt-2 rounded-full overflow-hidden">
                            <div className="bg-orange-500 h-full" style={{ width: `${stats.ram_usage}%` }}></div>
                        </div>
                    </div>
                </div>
            )}

            {/* USERS TAB */}
            {activeTab === "users" && (
                <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                    <div className="p-6 border-b border-slate-800">
                        <h2 className="text-xl font-bold">Gerenciamento de Usuários</h2>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm text-slate-400">
                            <thead className="bg-slate-800 text-slate-200 uppercase font-medium">
                                <tr>
                                    <th className="p-4">ID</th>
                                    <th className="p-4">Usuário</th>
                                    <th className="p-4">Email</th>
                                    <th className="p-4">Função</th>
                                    <th className="p-4">Sessões Ativas</th>
                                    <th className="p-4">Status</th>
                                    <th className="p-4 text-right">Ações</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {users.map((u) => (
                                    <tr key={u.id} className="hover:bg-slate-800/50">
                                        <td className="p-4">{u.id}</td>
                                        <td className="p-4 font-medium text-white">{u.username}</td>
                                        <td className="p-4">{u.email}</td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded-full text-xs font-bold ${u.role === 'admin' ? 'bg-purple-500/10 text-purple-400' : 'bg-slate-700 text-slate-300'}`}>
                                                {u.role.toUpperCase()}
                                            </span>
                                        </td>
                                        <td className="p-4 text-center">{u.active_sessions}</td>
                                        <td className="p-4">
                                            {u.is_active ? (
                                                <span className="text-emerald-400 flex items-center gap-1">
                                                    ● Ativo
                                                </span>
                                            ) : (
                                                <span className="text-red-400 flex items-center gap-1">
                                                    ● Bloqueado
                                                </span>
                                            )}
                                        </td>
                                        <td className="p-4 text-right">
                                            {u.role !== 'admin' && (
                                                <button
                                                    onClick={() => handleBlockUnblock(u.id, u.is_active)}
                                                    className={`px-3 py-1 rounded text-xs font-bold transition-colors ${u.is_active ? 'bg-red-500/10 text-red-400 hover:bg-red-500/20' : 'bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20'}`}
                                                >
                                                    {u.is_active ? 'Banir Usuário' : 'Desbanir Usuário'}
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* SETTINGS TAB */}
            {activeTab === "settings" && config && (
                <div className="max-w-xl mx-auto bg-slate-900 rounded-xl border border-slate-800 p-8">
                    <h2 className="text-xl font-bold mb-6">Configuração do Sistema</h2>
                    <form onSubmit={handleUpdateConfig} className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-2">
                                Máximo de Usuários Permitidos
                            </label>
                            <input
                                type="number"
                                value={config.max_users}
                                onChange={(e) => setConfig({ ...config, max_users: parseInt(e.target.value) })}
                                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                            />
                            <p className="text-xs text-slate-500 mt-2">
                                Se o número de usuários registrados exceder este limite, novos registros serão bloqueados.
                            </p>
                        </div>
                        <button
                            type="submit"
                            disabled={loadingConfig}
                            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2 px-4 rounded-lg transition-colors disabled:opacity-50"
                        >
                            {loadingConfig ? "Salvando..." : "Salvar Configuração"}
                        </button>
                    </form>
                </div>
            )}
        </div>
    );
}
