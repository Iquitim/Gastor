import React from 'react';
import StrategyIcon from "./StrategyIcon";

interface StrategyCardProps {
    slug: string;
    name: string;
    category: string;
    icon?: string;
    description: string;
    isSelected?: boolean;
    onClick?: () => void;
}

const categoryColors: Record<string, string> = {
    reversal: "bg-purple-500/10 text-purple-400 border-purple-500/30",
    trend: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    momentum: "bg-orange-500/10 text-orange-400 border-orange-500/30",
    volatility: "bg-pink-500/10 text-pink-400 border-pink-500/30",
    hybrid: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
};

const categoryLabels: Record<string, string> = {
    reversal: "Reversão",
    trend: "Tendência",
    momentum: "Momentum",
    volatility: "Volatilidade",
    hybrid: "Híbrido",
};

export default function StrategyCard({
    name,
    category,
    icon,
    description,
    isSelected = false,
    onClick,
}: StrategyCardProps) {
    const categoryColor = categoryColors[category] || "bg-slate-500/10 text-slate-400 border-slate-500/30";
    const categoryLabel = categoryLabels[category] || category;

    return (
        <div
            onClick={onClick}
            className={`
        p-4 rounded-lg border cursor-pointer transition-all duration-200
        ${isSelected
                    ? "bg-emerald-500/10 border-emerald-500 ring-1 ring-emerald-500"
                    : "bg-slate-800/50 border-slate-700 hover:border-slate-600 hover:bg-slate-800"
                }
      `}
        >
            <div className="flex items-start justify-between">
                <div>
                    <h3 className="font-semibold text-white flex items-center gap-2">
                        {icon && <StrategyIcon icon={icon} className="w-5 h-5 text-gray-400" />}
                        {name}
                    </h3>
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${categoryColor} mt-1 inline-block`}>
                        {categoryLabel}
                    </span>
                </div>
                {isSelected && (
                    <div className="text-emerald-400">
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                    </div>
                )}
            </div>
            <p className="mt-2 text-sm text-slate-400">{description}</p>
        </div>
    );
}
