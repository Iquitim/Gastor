"use client";

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";
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

    // Check token and fetch user on mount
    useEffect(() => {
        const initAuth = async () => {
            const token = getStoredToken();
            if (token) {
                try {
                    const userData = await api.getCurrentUser();
                    setUser(userData);
                } catch (error) {
                    console.error("Failed to fetch user:", error);
                    removeStoredToken();
                }
            }
            setIsLoading(false);
        };

        initAuth();
    }, []);

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
