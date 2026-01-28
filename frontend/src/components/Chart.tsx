"use client";

import { useEffect, useRef, useState, forwardRef, useImperativeHandle } from "react";
import { createChart, ColorType, Time, CandlestickSeries, LineSeries, HistogramSeries, IChartApi } from "lightweight-charts";

interface OHLCData {
    time: Time;
    open: number;
    high: number;
    low: number;
    close: number;
}

interface ChartProps {
    data: OHLCData[];
    indicators?: {
        ema9?: number[];
        ema21?: number[];
    };
    trades?: {
        time: Time;
        type: "BUY" | "SELL";
        price: number;
    }[];
    height?: number;
}

const Chart = forwardRef((props: ChartProps, ref) => {
    const { data, indicators, trades, height = 400 } = props;
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useImperativeHandle(ref, () => ({
        resetZoom: () => {
            if (chartRef.current && data.length > 0) {
                // Focar nos últimos 50 candles
                const visibleRange = 50;
                const total = data.length;
                chartRef.current.timeScale().setVisibleLogicalRange({
                    from: total - visibleRange,
                    to: total,
                });
            }
        },
        fitContent: () => {
            if (chartRef.current) {
                chartRef.current.timeScale().fitContent();
            }
        }
    }));

    useEffect(() => {
        if (!chartContainerRef.current || data.length === 0) return;

        // Cleanup previous chart if it exists and hasn't been removed (safety check)
        try {
            if (chartRef.current) {
                chartRef.current.remove();
                chartRef.current = null;
            }
        } catch (e) {
            console.warn("Chart cleanup warning:", e);
        }

        // Create chart
        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: "#0f172a" },
                textColor: "#94a3b8",
            },
            grid: {
                vertLines: { color: "#1e293b" },
                horzLines: { color: "#1e293b" },
            },
            width: chartContainerRef.current.clientWidth,
            height: height,
            crosshair: {
                mode: 1,
            },
            rightPriceScale: {
                borderColor: "#1e293b",
            },
            timeScale: {
                borderColor: "#1e293b",
                timeVisible: true,
                secondsVisible: false,
            },
        });

        chartRef.current = chart;

        // Candlestick series
        const candlestickSeries = chart.addSeries(CandlestickSeries, {
            upColor: "#10b981",
            downColor: "#ef4444",
            borderDownColor: "#ef4444",
            borderUpColor: "#10b981",
            wickDownColor: "#ef4444",
            wickUpColor: "#10b981",
        });

        candlestickSeries.setData(data);

        // EMA indicators
        if (indicators?.ema9 && indicators.ema9.length > 0) {
            const ema9Series = chart.addSeries(LineSeries, {
                color: "#3b82f6",
                lineWidth: 1,
            });
            const ema9Data = indicators.ema9.map((value, index) => ({
                time: data[index]?.time,
                value,
            })).filter(d => d.time && !isNaN(d.value));
            ema9Series.setData(ema9Data);
        }

        if (indicators?.ema21 && indicators.ema21.length > 0) {
            const ema21Series = chart.addSeries(LineSeries, {
                color: "#f59e0b",
                lineWidth: 1,
            });
            const ema21Data = indicators.ema21.map((value, index) => ({
                time: data[index]?.time,
                value,
            })).filter(d => d.time && !isNaN(d.value));
            ema21Series.setData(ema21Data);
        }


        // Trade markers (Vertical Lines via Histogram)
        if (trades && trades.length > 0) {
            const tradeSeries = chart.addSeries(HistogramSeries, {
                priceScaleId: 'trade_overlay', // Separate scale
                priceFormat: {
                    type: 'volume',
                },
                priceLineVisible: false,
                lastValueVisible: false,
            });

            // Configure scale to full height
            chart.priceScale('trade_overlay').applyOptions({
                visible: false,
                scaleMargins: { top: 0, bottom: 0 },
            });

            const tradeData = trades.map((trade) => ({
                time: trade.time,
                value: 1, // Full height relative to scale
                color: trade.type === "BUY"
                    ? "rgba(16, 185, 129, 0.3)" // Green transparent
                    : "rgba(239, 68, 68, 0.3)", // Red transparent
            }));

            // Remove duplicates (if multiple trades in same candle, prioritize last or mix?)
            // Lightweight charts fails if duplicate times.
            // Let's deduplicate by time.
            const uniqueTrades = new Map();
            tradeData.forEach(t => uniqueTrades.set(t.time, t));
            const sortedTrades = Array.from(uniqueTrades.values()).sort((a, b) => (a.time as number) - (b.time as number));

            tradeSeries.setData(sortedTrades);
        }

        // Fit content initially
        chart.timeScale().fitContent();
        setIsLoading(false);

        // Resize handler
        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({ width: chartContainerRef.current.clientWidth });
            }
        };

        window.addEventListener("resize", handleResize);

        return () => {
            window.removeEventListener("resize", handleResize);
            try {
                chart.remove();
            } catch (e) {
                console.warn("Chart removal warning:", e);
            }
            chartRef.current = null;
        };
    }, [data, indicators, trades, height]);

    return (
        <div className="relative w-full">
            {/* Legend */}
            <div className="absolute top-3 left-3 z-10 flex flex-col gap-1 pointer-events-none">
                {data.length > 0 && (
                    <div className="flex items-center gap-2 bg-slate-900/50 px-2 py-1 rounded backdrop-blur-sm border border-slate-700/50">
                        <div className="w-4 h-0 border-b-2 border-dotted border-white/70"></div>
                        <span className="text-xs font-medium text-slate-300">Preço Atual</span>
                    </div>
                )}
                {indicators?.ema9 && indicators.ema9.length > 0 && (
                    <div className="flex items-center gap-2 bg-slate-900/50 px-2 py-1 rounded backdrop-blur-sm border border-slate-700/50">
                        <div className="w-3 h-0.5 bg-blue-500 rounded-full"></div>
                        <span className="text-xs font-medium text-blue-500">EMA 9</span>
                    </div>
                )}
                {indicators?.ema21 && indicators.ema21.length > 0 && (
                    <div className="flex items-center gap-2 bg-slate-900/50 px-2 py-1 rounded backdrop-blur-sm border border-slate-700/50">
                        <div className="w-3 h-0.5 bg-amber-500 rounded-full"></div>
                        <span className="text-xs font-medium text-amber-500">EMA 21</span>
                    </div>
                )}
            </div>

            {isLoading && data.length > 0 && (
                <div className="absolute inset-0 flex items-center justify-center bg-slate-900/50">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
                </div>
            )}
            {data.length === 0 ? (
                <div
                    className="flex items-center justify-center bg-slate-900 rounded-lg border border-slate-700"
                    style={{ height }}
                >
                    <p className="text-slate-400">Carregue dados para visualizar o gráfico</p>
                </div>
            ) : (
                <div ref={chartContainerRef} className="rounded-lg overflow-hidden" />
            )}
        </div>
    );
});

Chart.displayName = "Chart";
export default Chart;
