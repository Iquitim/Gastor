"use client";

import { useState, useRef, useEffect } from "react";
import dynamic from "next/dynamic";
import { useData } from "../context/DataContext";
import api, { OHLCVData } from "../lib/api";
import ProtectedRoute from "../components/ProtectedRoute";

const Chart = dynamic(() => import("@/components/Chart"), { ssr: false });

const COINS = [

  { value: "SOL/USDT", label: "SOL/USDT" },
  { value: "ETH/USDT", label: "ETH/USDT" },
  { value: "BTC/USDT", label: "BTC/USDT" },
  { value: "XRP/USDT", label: "XRP/USDT" },
  { value: "AVAX/USDT", label: "AVAX/USDT" },
  { value: "DOGE/USDT", label: "DOGE/USDT" },
];

const DATA_SOURCES = [
  { value: "auto", label: "Automático", description: "Tenta todas as fontes em sequência" },
  { value: "binance", label: "Binance", description: "API oficial Binance (global)" },
  { value: "binance_us", label: "Binance US", description: "API Binance para usuários dos EUA" },
  { value: "coingecko", label: "CoinGecko", description: "Dados agregados de várias exchanges" },
  { value: "cryptocompare", label: "CryptoCompare", description: "Dados históricos confiáveis" },
];

const DAYS_OPTIONS = [30, 60, 90, 120, 180, 365];

const TIMEFRAMES = [
  { value: "1m", label: "1 minuto" },
  { value: "5m", label: "5 minutos" },
  { value: "15m", label: "15 minutos" },
  { value: "1h", label: "1 hora" },
  { value: "4h", label: "4 horas" },
  { value: "1d", label: "1 dia" },
];

function DashboardContent() {
  const { setDataLoaded, hasData, dataInfo, chartData } = useData();
  const [selectedCoin, setSelectedCoin] = useState("SOL/USDT");
  const [selectedDays, setSelectedDays] = useState(90);
  const [selectedSource, setSelectedSource] = useState("auto");
  const [selectedTimeframe, setSelectedTimeframe] = useState("1h");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState({
    price: "—",
    change: "—",
    volume: "—",
    rsi: "—"
  });

  const chartRef = useRef(null);

  // Calcular estatísticas quando dados mudam
  useEffect(() => {
    if (chartData.length > 0) {
      const last = chartData[chartData.length - 1];
      const prevIndex = chartData.length > 24 ? chartData.length - 25 : 0;
      const prev = chartData[prevIndex];

      // Preço
      const currentPrice = last.close;

      // Variação 24h (aproximada)
      const refPrice = prev ? prev.close : last.open;
      const changePct = ((currentPrice - refPrice) / refPrice) * 100;

      // Volume
      const vol = last.volume;

      // RSI
      const rsi = last.rsi_14;

      setStats({
        price: `$${currentPrice.toFixed(2)}`,
        change: `${changePct >= 0 ? "+" : ""}${changePct.toFixed(2)}%`,
        volume: `$${(vol * currentPrice).toLocaleString('en-US', { maximumFractionDigits: 0 })}`,
        rsi: rsi ? rsi.toFixed(2) : "—"
      });
    }
  }, [chartData]);

  // Preparar indicadores para o gráfico
  const indicators = {
    ema9: chartData.map(d => d.ema_9).filter(v => v !== undefined && v !== null) as number[],
    ema21: chartData.map(d => d.ema_21).filter(v => v !== undefined && v !== null) as number[],
  };

  const handleLoadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await api.getMarketData(selectedCoin, selectedDays, selectedTimeframe);

      // Atualizar contexto global de dados carregados
      setDataLoaded({
        coin: selectedCoin,
        timeframe: selectedTimeframe,
        period: `${selectedDays} dias`,
        candles: result.data?.length || Math.floor(selectedDays * (selectedTimeframe === "1h" ? 24 : selectedTimeframe === "4h" ? 6 : 1)),
      }, result.data || []);

      // Auto-focar no gráfico
      setTimeout(() => {
        (chartRef.current as any)?.resetZoom();
      }, 500);

    } catch (err) {
      console.error("Erro ao carregar dados:", err);
      setError(err instanceof Error ? err.message : "Erro ao carregar dados");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <p className="text-slate-400 mt-1">
          Análise de mercado e visualização de dados
        </p>
      </div>

      {/* Controls */}
      <div className="bg-slate-900 rounded-lg border border-slate-800 p-4 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Coin Selector */}
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">
              Moeda
            </label>
            <select
              value={selectedCoin}
              onChange={(e) => setSelectedCoin(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              {COINS.map((coin) => (
                <option key={coin.value} value={coin.value}>
                  {coin.label}
                </option>
              ))}
            </select>
          </div>

          {/* Data Source Selector */}
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">
              Fonte de Dados
            </label>
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              {DATA_SOURCES.map((source) => (
                <option key={source.value} value={source.value}>
                  {source.label}
                </option>
              ))}
            </select>
          </div>

          {/* Timeframe Selector */}
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">
              Timeframe
            </label>
            <select
              value={selectedTimeframe}
              onChange={(e) => setSelectedTimeframe(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              {TIMEFRAMES.map((tf) => (
                <option key={tf.value} value={tf.value}>
                  {tf.label}
                </option>
              ))}
            </select>
          </div>

          {/* Days Selector */}
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">
              Período
            </label>
            <select
              value={selectedDays}
              onChange={(e) => setSelectedDays(Number(e.target.value))}
              className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              {DAYS_OPTIONS.map((days) => (
                <option key={days} value={days}>
                  {days} dias
                </option>
              ))}
            </select>
          </div>

          {/* Load Button */}
          <div className="flex items-end">
            <button
              onClick={handleLoadData}
              disabled={isLoading}
              className="w-full px-6 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-800 disabled:cursor-not-allowed text-white font-medium rounded-md transition-colors"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Carregando...
                </span>
              ) : (
                "Carregar Dados"
              )}
            </button>
          </div>
        </div>

        {/* Source description */}
        <p className="text-xs text-slate-500 mt-2">
          {DATA_SOURCES.find(s => s.value === selectedSource)?.description}
        </p>

        {/* Error message */}
        {error && (
          <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-md text-red-300">
            ⚠️ {error}
          </div>
        )}

        {/* Success message */}
        {hasData && dataInfo && !isLoading && (
          <div className="mt-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-md text-emerald-300">
            ✅ Dados carregados: {dataInfo.coin} | {dataInfo.timeframe} | {dataInfo.period} | ~{dataInfo.candles} candles
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="bg-slate-900 rounded-lg border border-slate-800 p-4 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">
            Gráfico — {selectedCoin}
          </h2>
          <button
            onClick={() => (chartRef.current as any)?.resetZoom()}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
            </svg>
            Focar Agora
          </button>
        </div>
        <Chart ref={chartRef} data={chartData as never[]} height={500} indicators={indicators} />
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Preço Atual", value: stats.price, color: "text-white" },
          { label: "Variação 24h", value: stats.change, color: stats.change.startsWith("-") ? "text-red-500" : "text-emerald-500" },
          { label: "Volume 24h", value: stats.volume, color: "text-white" },
          { label: "RSI (14)", value: stats.rsi, color: parseFloat(stats.rsi) > 70 ? "text-red-500" : parseFloat(stats.rsi) < 30 ? "text-emerald-500" : "text-white" },
        ].map((stat) => (
          <div
            key={stat.label}
            className="bg-slate-900 rounded-lg border border-slate-800 p-4"
          >
            <div className="text-slate-400 text-sm">{stat.label}</div>
            <div className={`text-2xl font-bold mt-1 ${stat.color}`}>{stat.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Dashboard() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}
