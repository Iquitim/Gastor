"use client";

import { useEffect, useRef, useState } from "react";
import { createChart, ColorType, IChartApi, AreaSeries } from "lightweight-charts";

interface EquityData {
    time: number; // Unix timestamp
    value: number;
}

interface EquityChartProps {
    data: EquityData[];
    height?: number;
}

export default function EquityChart({ data, height = 300 }: EquityChartProps) {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);

    useEffect(() => {
        if (!chartContainerRef.current || data.length === 0) return;

        // Cleanup
        if (chartRef.current) {
            try {
                chartRef.current.remove();
            } catch (e) {
                console.warn(e);
            }
            chartRef.current = null;
        }

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

        const areaSeries = chart.addSeries(AreaSeries, {
            lineColor: "#10b981",
            topColor: "rgba(16, 185, 129, 0.4)",
            bottomColor: "rgba(16, 185, 129, 0.0)",
        });

        // Ensure data is sorted and valid
        const validData = data
            .filter(d => d.time && !isNaN(d.value))
            .sort((a, b) => a.time - b.time)
            .map(d => ({ time: d.time as any, value: d.value }));

        if (validData.length > 0) {
            areaSeries.setData(validData);
            chart.timeScale().fitContent();
        }

        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({ width: chartContainerRef.current.clientWidth });
            }
        };

        window.addEventListener("resize", handleResize);

        return () => {
            window.removeEventListener("resize", handleResize);
            if (chartRef.current) {
                try {
                    chartRef.current.remove();
                } catch (e) {
                    console.warn(e);
                }
            }
        };
    }, [data, height]);

    return (
        <div className="relative w-full">
            {data.length === 0 ? (
                <div
                    className="flex items-center justify-center bg-slate-900 rounded-lg border border-slate-700"
                    style={{ height }}
                >
                    <p className="text-slate-400">Sem dados de evolução</p>
                </div>
            ) : (
                <div ref={chartContainerRef} className="rounded-lg overflow-hidden" />
            )}
        </div>
    );
}
