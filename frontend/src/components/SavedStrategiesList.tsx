"use client";

import { useEffect, useState } from "react";
import api from "../lib/api";

interface SavedStrategiesListProps {
    onLoad: (strategy: any) => void;
    onClose: () => void;
}

export default function SavedStrategiesList({ onLoad, onClose }: SavedStrategiesListProps) {
    const [strategies, setStrategies] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const loadList = async () => {
        setLoading(true);
        try {
            const list = await api.listCustomStrategies();
            setStrategies(list);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadList();
    }, []);

    const handleDelete = async (id: number) => {
        if (!confirm("Tem certeza que deseja excluir esta estratégia?")) return;
        try {
            await api.deleteCustomStrategy(id);
            loadList();
        } catch (e) {
            alert("Erro ao excluir");
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
            <div className="bg-slate-900 rounded-lg border border-slate-700 w-full max-w-2xl max-h-[80vh] flex flex-col">
                <div className="p-4 border-b border-slate-700 flex justify-between items-center bg-slate-800 rounded-t-lg">
                    <h3 className="text-lg font-bold text-white">Carregar Estratégia</h3>
                    <button onClick={onClose} className="text-slate-400 hover:text-white">✕</button>
                </div>

                <div className="p-4 overflow-y-auto flex-1">
                    {loading ? (
                        <div className="text-center text-slate-400 py-8">Carregando...</div>
                    ) : strategies.length === 0 ? (
                        <div className="text-center text-slate-400 py-8">Nenhuma estratégia salva.</div>
                    ) : (
                        <div className="space-y-3">
                            {strategies.map((s) => (
                                <div key={s.id} className="bg-slate-800 p-3 rounded border border-slate-700 flex justify-between items-center hover:border-slate-500 transition-colors">
                                    <div>
                                        <div className="font-semibold text-white">{s.name}</div>
                                        <div className="text-xs text-slate-400">
                                            {s.coin} • {s.timeframe} • {new Date(s.created_at).toLocaleDateString()}
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => onLoad(s)}
                                            className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded"
                                        >
                                            Carregar
                                        </button>
                                        <button
                                            onClick={() => handleDelete(s.id)}
                                            className="px-2 py-1 text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded"
                                        >
                                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                            </svg>
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
