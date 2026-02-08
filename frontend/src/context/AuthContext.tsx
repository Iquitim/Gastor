"use client";

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import api, { getStoredToken, removeStoredToken } from "../lib/api";

// =============================================================================
// TYPES
// =============================================================================

export interface User {
    id: number;
    username: string;
    email: string;
    telegram_chat_id: string | null;
    is_active: boolean;
    role: string;
}

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (username: string, email: string, password: string) => Promise<void>;
    loginWithGoogle: (code: string) => Promise<void>;
    logout: () => void;
    refreshUser: () => Promise<void>;
}

// =============================================================================
// CONTEXT
// =============================================================================

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// =============================================================================
// PROVIDER
// =============================================================================

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const router = useRouter();
    const pathname = usePathname();

    // Rotas públicas que não requerem autenticação
    const publicRoutes = ['/', '/login', '/register', '/auth/google/callback'];

    // Helper para verificar rota pública (insensível a trailing slash e query params)
    const isRoutePublic = (path: string) => {
        if (!path) return false;
        // Normaliza removendo trailing slash se existir (e não for root)
        const normalized = path.endsWith('/') && path.length > 1 ? path.slice(0, -1) : path;
        return publicRoutes.some(route =>
            normalized === route ||
            normalized.startsWith(route + '?')
        );
    };

    useEffect(() => {
        const initAuth = async () => {
            const token = getStoredToken();
            let currentUser = null;

            if (token) {
                try {
                    currentUser = await api.getCurrentUser();
                    setUser(currentUser);

                    // Sync Settings globally on load
                    try {
                        const config = await api.getUserConfig();
                        const telegram = await api.getTelegramConfig().catch(() => ({ chat_id: "" }));

                        const settings = {
                            initialBalance: config.backtest_initial_balance,
                            useCompound: config.backtest_use_compound,
                            paperTradingBalance: config.paper_initial_balance,
                            paperTradingCoin: config.paper_default_coin,
                            paperTradingTimeframe: config.paper_default_timeframe,
                            telegramChatId: telegram.chat_id || "",
                            // Fees
                            exchangeFee: config.exchange_fee,
                            slippageOverrides: config.slippage_overrides
                        };
                        localStorage.setItem("gastor_settings", JSON.stringify(settings));
                    } catch (configErr) {
                        console.error("Failed to sync settings on auth init", configErr);
                    }

                } catch (error) {
                    console.error("Failed to fetch user:", error);
                    removeStoredToken();
                }
            }

            setIsLoading(false);

            // Redirecionamento baseado em autenticação
            if (currentUser) {
                // Se está logado e tenta acessar login/register, manda para live
                if (pathname === '/login' || pathname === '/register') {
                    router.push('/live');
                }
            } else {
                const isPublic = isRoutePublic(pathname);

                if (!isPublic && !token) { // Se não tem token e rota não é pública
                    // Permitir assets estáticos e API
                    if (!pathname.startsWith('/_next') && !pathname.startsWith('/static') && !pathname.startsWith('/api')) {
                        router.push('/login');
                    }
                }
            }
        };

        initAuth();
    }, [pathname]); // Executa na montagem e troca de rota

    const login = useCallback(async (email: string, password: string) => {
        const response = await api.login(email, password);
        setUser(response.user as User);
    }, []);

    const register = useCallback(async (username: string, email: string, password: string) => {
        await api.register({ username, email, password });
        // After register, auto-login
        await login(email, password);
    }, [login]);

    const loginWithGoogle = useCallback(async (code: string) => {
        const redirectUri = typeof window !== 'undefined'
            ? `${window.location.origin}/auth/google/callback`
            : undefined;
        const response = await api.googleCallback(code, redirectUri);
        setUser(response.user as User);
    }, []);

    const logout = useCallback(() => {
        api.logout();
        setUser(null);
    }, []);

    const refreshUser = useCallback(async () => {
        try {
            const userData = await api.getCurrentUser();
            setUser(userData);
        } catch (error) {
            console.error("Failed to refresh user:", error);
            logout();
        }
    }, [logout]);

    // Evitar flash de conteúdo protegido enquando carrega
    const isPublic = isRoutePublic(pathname);

    // Se estiver carregando, bloqueia rotas protegidas
    if (isLoading && !isPublic) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-950">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-emerald-500"></div>
            </div>
        );
    }

    // Se NÃO estiver carregando, mas NÃO tiver usuário e for rota protegida -> Bloqueia também (evita FOUC na navegação)
    // O useEffect vai redirecionar em breve, mas enquanto isso não mostramos o conteúdo protegido.
    if (!isLoading && !user && !isPublic) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-950">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-emerald-500"></div>
            </div>
        );
    }

    return (
        <AuthContext.Provider
            value={{
                user,
                isLoading,
                isAuthenticated: user !== null,
                login,
                register,
                loginWithGoogle,
                logout,
                refreshUser,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

// =============================================================================
// HOOK
// =============================================================================

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
