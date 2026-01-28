"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import api from "@/lib/api";

interface DataContextType {
    hasData: boolean;
    dataInfo: {
        coin: string;
        timeframe: string;
        period: string;
        candles: number;
    } | null;
    chartData: any[];
    setDataLoaded: (info: { coin: string; timeframe: string; period: string; candles: number }, data: any[]) => void;
    clearData: () => void;
}

const DataContext = createContext<DataContextType | undefined>(undefined);

export function DataProvider({ children }: { children: ReactNode }) {
    const [dataInfo, setDataInfo] = useState<DataContextType["dataInfo"]>(null);
    const [chartData, setChartData] = useState<any[]>([]);

    // Restore context on mount
    useEffect(() => {
        const checkPersistence = async () => {
            // Only restore if we don't have data yet
            if (dataInfo) return;

            try {
                const context = await api.getMarketContext();
                if (context) {
                    console.log("Restoring market context...", context);
                    const result = await api.getMarketData(context.coin, context.days, context.timeframe);

                    if (result.data && result.data.length > 0) {
                        const info = {
                            coin: context.coin,
                            timeframe: context.timeframe,
                            period: `${context.days} dias`,
                            candles: result.data.length
                        };

                        setDataInfo(info);
                        setChartData(result.data);
                    }
                }
            } catch (e) {
                console.error("Failed to restore market context", e);
            }
        };

        checkPersistence();
    }, []); // Run once on mount

    const setDataLoaded = (info: { coin: string; timeframe: string; period: string; candles: number }, data: any[]) => {
        setDataInfo(info);
        setChartData(data);

        // Save context
        const days = parseInt(info.period) || 90; // Extract days
        api.setMarketContext({
            coin: info.coin,
            timeframe: info.timeframe,
            days: days
        }).catch(e => console.error("Failed to save context", e));
    };

    const clearData = () => {
        setDataInfo(null);
        setChartData([]);

        // Limpar persistência no backend
        api.clearMarketContext().catch(console.error);
        api.clearActiveStrategy().catch(console.error);
    };

    return (
        <DataContext.Provider value={{
            hasData: dataInfo !== null,
            dataInfo,
            chartData,
            setDataLoaded,
            clearData,
        }}>
            {children}
        </DataContext.Provider>
    );
}

export function useData() {
    const context = useContext(DataContext);
    if (context === undefined) {
        throw new Error("useData must be used within a DataProvider");
    }
    return context;
}
