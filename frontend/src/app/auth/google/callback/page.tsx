"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "../../../../context/AuthContext";

function GoogleCallbackContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { loginWithGoogle, isAuthenticated } = useAuth();
    const [error, setError] = useState<string | null>(null);
    const [isProcessing, setIsProcessing] = useState(true);

    useEffect(() => {
        const code = searchParams.get("code");
        const errorParam = searchParams.get("error");

        if (errorParam) {
            setError("Login cancelado ou erro na autenticação do Google");
            setIsProcessing(false);
            return;
        }

        if (!code) {
            setError("Código de autorização não encontrado");
            setIsProcessing(false);
            return;
        }

        const processCallback = async () => {
            try {
                await loginWithGoogle(code);
                router.push("/");
            } catch (err) {
                setError(err instanceof Error ? err.message : "Erro ao fazer login com Google");
                setIsProcessing(false);
            }
        };

        processCallback();
    }, [searchParams, loginWithGoogle, router]);

    // If already authenticated, redirect
    useEffect(() => {
        if (isAuthenticated) {
            router.push("/");
        }
    }, [isAuthenticated, router]);

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center px-4">
                <div className="max-w-md w-full text-center">
                    <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-6 py-8 rounded-xl">
                        <svg className="w-12 h-12 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        <h2 className="text-xl font-semibold mb-2">Erro no Login</h2>
                        <p className="text-sm mb-6">{error}</p>
                        <button
                            onClick={() => router.push("/login")}
                            className="bg-slate-800 hover:bg-slate-700 text-white px-6 py-2 rounded-lg transition-colors"
                        >
                            Voltar para Login
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center px-4">
            <div className="text-center">
                <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-emerald-500 mx-auto mb-6"></div>
                <h2 className="text-xl font-semibold text-white mb-2">Autenticando com Google...</h2>
                <p className="text-slate-400">Aguarde enquanto processamos seu login</p>
            </div>
        </div>
    );
}

// Loading fallback for Suspense
function LoadingFallback() {
    return (
        <div className="min-h-screen flex items-center justify-center px-4">
            <div className="text-center">
                <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-emerald-500 mx-auto mb-6"></div>
                <h2 className="text-xl font-semibold text-white mb-2">Carregando...</h2>
            </div>
        </div>
    );
}

export default function GoogleCallbackPage() {
    return (
        <Suspense fallback={<LoadingFallback />}>
            <GoogleCallbackContent />
        </Suspense>
    );
}
