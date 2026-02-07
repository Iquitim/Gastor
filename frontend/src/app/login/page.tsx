"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../../context/AuthContext";
import api from "../../lib/api";

// Google Icon SVG
const GoogleIcon = () => (
    <svg className="w-5 h-5" viewBox="0 0 24 24">
        <path
            fill="#4285F4"
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        />
        <path
            fill="#34A853"
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        />
        <path
            fill="#FBBC05"
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        />
        <path
            fill="#EA4335"
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        />
    </svg>
);

export default function LoginPage() {
    const router = useRouter();
    const { login, isAuthenticated, isLoading } = useAuth();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isGoogleLoading, setIsGoogleLoading] = useState(false);

    // Redirect if already logged in
    if (!isLoading && isAuthenticated) {
        router.push("/");
        return null;
    }

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError(null);
        setIsSubmitting(true);

        try {
            await login(email, password);
            router.push("/");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao fazer login");
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleGoogleLogin = async () => {
        setError(null);
        setIsGoogleLoading(true);

        try {
            const { url } = await api.getGoogleAuthUrl();
            window.location.href = url;
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao iniciar login com Google");
            setIsGoogleLoading(false);
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-emerald-500"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center px-4">
            <div className="max-w-md w-full">
                {/* Logo */}
                <div className="text-center mb-8">
                    <div className="flex items-center justify-center gap-3">
                        <img src="/logo.png" alt="Gastor" className="h-16 w-auto object-contain" />
                        <h1 className="text-4xl font-bold text-emerald-500">Gastor</h1>
                    </div>
                    <p className="text-slate-400 mt-2">Entre na sua conta</p>
                </div>

                {/* Form Card */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-xl">
                    {/* Error Message */}
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg text-sm mb-6">
                            {error}
                        </div>
                    )}

                    {/* Google Login Button */}
                    <button
                        onClick={handleGoogleLogin}
                        disabled={isGoogleLoading}
                        className="w-full bg-white hover:bg-gray-100 disabled:bg-gray-200 disabled:cursor-not-allowed text-gray-800 font-medium py-3 px-4 rounded-lg transition-all duration-200 flex items-center justify-center gap-3 mb-6"
                    >
                        {isGoogleLoading ? (
                            <>
                                <span className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-gray-600"></span>
                                Conectando...
                            </>
                        ) : (
                            <>
                                <GoogleIcon />
                                Entrar com Google
                            </>
                        )}
                    </button>

                    {/* Divider */}
                    <div className="relative my-6">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-slate-700"></div>
                        </div>
                        <div className="relative flex justify-center text-sm">
                            <span className="px-4 bg-slate-900 text-slate-500">ou</span>
                        </div>
                    </div>

                    {/* Email/Password Form */}
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* Email */}
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                                Email
                            </label>
                            <input
                                id="email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                                placeholder="seu@email.com"
                            />
                        </div>

                        {/* Password */}
                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                                Senha
                            </label>
                            <input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                                placeholder="••••••••"
                            />
                        </div>

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-800 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-lg transition-all duration-200 flex items-center justify-center gap-2"
                        >
                            {isSubmitting ? (
                                <>
                                    <span className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white"></span>
                                    Entrando...
                                </>
                            ) : (
                                "Entrar"
                            )}
                        </button>
                    </form>

                    {/* Register Link */}
                    <div className="mt-6 text-center text-sm text-slate-400">
                        Não tem uma conta?{" "}
                        <Link href="/register" className="text-emerald-500 hover:text-emerald-400 font-medium">
                            Criar conta
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
