"use client";

import { useState, useMemo } from "react";

interface InteractiveChartProps {
    data: { time: number; open: number; high: number; low: number; close: number }[];
}

const InteractiveChart: React.FC<InteractiveChartProps> = ({ data }) => {
    const [hoveredCandle, setHoveredCandle] = useState<any>(null);

    const { width, height, minPrice, maxPrice, range, adjMin, adjRange, candleWidth, gap, scaleY } = useMemo(() => {
        const width = 600;
        const height = 200;
        const allPrices = data.flatMap(d => [d.high, d.low]);
        const minPrice = Math.min(...allPrices);
        const maxPrice = Math.max(...allPrices);
        const range = maxPrice - minPrice || 1;
        const padding = range * 0.1;
        const adjMin = minPrice - padding;
        const adjRange = range + padding * 2;
        const candleWidth = Math.max(3, (width / data.length) * 0.7);
        const gap = (width / data.length) * 0.15;
        const scaleY = (price: number) => height - ((price - adjMin) / adjRange) * height;

        return { width, height, minPrice, maxPrice, range, adjMin, adjRange, candleWidth, gap, scaleY };
    }, [data]);

    const displayCandle = hoveredCandle || data[data.length - 1];

    if (!data || data.length === 0) return null;

    return (
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 mt-4">
            {/* Header: OHLC Stats */}
            <div className="flex justify-between items-center mb-4 text-xs font-mono">
                <div className="flex flex-wrap gap-4 md:gap-6">
                    <span className="text-gray-400">Abertura: <span className={displayCandle.open > displayCandle.close ? "text-red-400" : "text-green-400"}>{displayCandle.open.toFixed(2)}</span></span>
                    <span className="text-gray-400">Máxima: <span className="text-gray-200">{displayCandle.high.toFixed(2)}</span></span>
                    <span className="text-gray-400">Mínima: <span className="text-gray-200">{displayCandle.low.toFixed(2)}</span></span>
                    <span className="text-gray-400">Fechamento: <span className={displayCandle.close >= displayCandle.open ? "text-green-400" : "text-red-400"}>{displayCandle.close.toFixed(2)}</span></span>
                </div>
                <div className="text-gray-500 whitespace-nowrap ml-4">
                    Horário: {new Date(displayCandle.time * 1000).toLocaleTimeString()}
                </div>
            </div>

            {/* Chart */}
            <div className="w-full h-48 relative cursor-crosshair">
                <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full" preserveAspectRatio="none">
                    {data.map((candle, i) => {
                        const x = (i / data.length) * width + gap;
                        const isGreen = candle.close >= candle.open;
                        const color = isGreen ? "#22c55e" : "#ef4444";
                        const bodyTop = scaleY(Math.max(candle.open, candle.close));
                        const bodyBottom = scaleY(Math.min(candle.open, candle.close));
                        const bodyHeight = Math.max(1, bodyBottom - bodyTop);
                        const wickX = x + candleWidth / 2;

                        return (
                            <g key={i}
                                onMouseEnter={() => setHoveredCandle(candle)}
                                onMouseLeave={() => setHoveredCandle(null)}
                            >
                                {/* Invisible Hit Area (Larger) */}
                                <rect
                                    x={x - gap / 2}
                                    y={0}
                                    width={candleWidth + gap}
                                    height={height}
                                    fill="transparent"
                                />

                                {/* Wick */}
                                <line
                                    x1={wickX}
                                    y1={scaleY(candle.high)}
                                    x2={wickX}
                                    y2={scaleY(candle.low)}
                                    stroke={color}
                                    strokeWidth="1"
                                    className="pointer-events-none"
                                />
                                {/* Body */}
                                <rect
                                    x={x}
                                    y={bodyTop}
                                    width={candleWidth}
                                    height={bodyHeight}
                                    fill={color}
                                    className="pointer-events-none"
                                />
                            </g>
                        );
                    })}

                    {/* Linha de Preço Atual (Dotted) */}
                    <line
                        x1="0"
                        y1={scaleY(displayCandle.close)}
                        x2={width}
                        y2={scaleY(displayCandle.close)}
                        stroke="#ffffff"
                        strokeOpacity="0.2"
                        strokeDasharray="4"
                    />
                </svg>
            </div>
        </div>
    );
};

export default InteractiveChart;
