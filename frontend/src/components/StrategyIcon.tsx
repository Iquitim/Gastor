import {
    Activity,
    Zap,
    TrendingUp,
    BarChart2,
    ArrowRightLeft,
    Layers,
    Cpu,
    ShieldCheck,
    Anchor,
    Box
} from "lucide-react";

interface StrategyIconProps {
    icon: string;
    className?: string;
}

const ICON_MAP: Record<string, any> = {
    // Trend
    "trending-up": TrendingUp,
    "activity": Activity,

    // Volatility
    "zap": Zap,
    "layers": Layers,

    // Momentum
    "bar-chart-2": BarChart2,
    "arrow-right-left": ArrowRightLeft,

    // Hybrid/Custom
    "cpu": Cpu,
    "shield-check": ShieldCheck,
    "anchor": Anchor,

    // Default
    "box": Box
};

export default function StrategyIcon({ icon, className = "w-5 h-5" }: StrategyIconProps) {
    const IconComponent = ICON_MAP[icon] || Box;
    return <IconComponent className={className} />;
}
