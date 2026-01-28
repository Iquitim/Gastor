"use client";

import Link from "next/link";

interface NoDataBannerProps {
    pageName: string;
}

export default function NoDataBanner({ pageName }: NoDataBannerProps) {
    return (
        <div className="mb-6 p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
            <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div className="flex-1">
                    <h3 className="text-amber-300 font-medium">Dados não carregados</h3>
                    <p className="text-amber-200/80 text-sm mt-1">
                        Para usar o {pageName}, primeiro carregue os dados de mercado no Dashboard.
                        Você pode explorar a interface, mas não poderá executar operações.
                    </p>
                    <Link
                        href="/"
                        className="inline-flex items-center gap-1 mt-3 px-4 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-sm font-medium rounded-md transition-colors"
                    >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                        </svg>
                        Ir para o Dashboard
                    </Link>
                </div>
            </div>
        </div>
    );
}
