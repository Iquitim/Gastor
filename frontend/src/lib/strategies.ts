// Lista completa de estratégias do Gastor
// Design minimalista sem emojis

export interface Strategy {
    slug: string;
    name: string;
    category: "reversal" | "trend" | "momentum" | "volatility" | "hybrid";
    icon: string;
    description: string;
    idealFor: string;
    parameters: Record<string, ParameterConfig>;
}

export interface ParameterConfig {
    default: number;
    min: number;
    max: number;
    label: string;
    help?: string;
}

// TODO: Fetch this list from backend (GET /api/strategies) to ensure Single Source of Truth
// Currently must be manually synced with backend/core/strategies_config.py
// Strategies are now fetched from the Backend API to ensure Single Source of Truth.
// This list is intentionally empty to force API usage.
export const STRATEGIES: Strategy[] = [];

// Categorias disponíveis (sem emojis)
export const CATEGORIES = [
    { value: "all", label: "Todas" },
    { value: "reversal", label: "Reversão" },
    { value: "trend", label: "Tendência" },
    { value: "momentum", label: "Momentum" },
    { value: "volatility", label: "Volatilidade" },
    { value: "hybrid", label: "Híbrido" },
    { value: "custom", label: "Personalizadas" },
];

// Helpers
export function getStrategyBySlug(slug: string): Strategy | undefined {
    return STRATEGIES.find(s => s.slug === slug);
}

export function getStrategiesByCategory(category: string): Strategy[] {
    if (category === "all") return STRATEGIES;
    return STRATEGIES.filter(s => s.category === category);
}
