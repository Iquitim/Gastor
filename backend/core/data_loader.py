"""
Data Loader Module
===================

Busca dados OHLCV de diferentes fontes (Binance, CoinGecko, etc).
"""

import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any
import numpy as np
import pandas as pd
from core.indicators import calc_ema, calc_rsi


async def fetch_binance_klines(
    symbol: str,
    interval: str = "1h",
    days: int = 90,
) -> List[Dict[str, Any]]:
    """
    Busca dados OHLCV da API pública da Binance.
    
    Args:
        symbol: Par de trading (ex: "SOLUSDT")
        interval: Intervalo do candle (1h, 4h, 1d)
        days: Número de dias de histórico
        
    Returns:
        Lista de candles com open, high, low, close, volume
    """
    base_url = "https://api.binance.com/api/v3/klines"
    
    # Calcular timestamps
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    
    # Mapear intervalo
    interval_map = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "1h", "4h": "4h", "1d": "1d"}
    binance_interval = interval_map.get(interval, "1h")
    
    all_candles = []
    current_start = start_time
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while current_start < end_time:
            params = {
                "symbol": symbol,
                "interval": binance_interval,
                "startTime": current_start,
                "endTime": end_time,
                "limit": 1000,
            }
            
            try:
                response = await client.get(base_url, params=params)
                
                if response.status_code != 200:
                    print(f"Binance API error: {response.status_code}")
                    break
                
                data = response.json()
                
                if not data:
                    break
                
                for candle in data:
                    all_candles.append({
                        "time": int(candle[0] / 1000),  # UNIX timestamp (seconds)
                        "open": float(candle[1]),
                        "high": float(candle[2]),
                        "low": float(candle[3]),
                        "close": float(candle[4]),
                        "volume": float(candle[5]),
                    })
                
                # Preparar próxima iteração
                if len(data) < 1000:
                    break
                current_start = data[-1][0] + 1
                
            except Exception as e:
                print(f"Erro ao buscar dados Binance: {e}")
                break
    
    # Remove the last candle if it's the current (unfinished) one
    # Binance kline time is Open Time.
    if all_candles:
        last_candle_time = all_candles[-1]["time"] * 1000 # back to ms
        # Calculate theoretical close time of the last candle
        interval_ms_map = {"1m": 60000, "5m": 300000, "15m": 900000, "30m": 1800000, "1h": 3600000, "4h": 14400000, "1d": 86400000}
        duration = interval_ms_map.get(interval, 3600000) # Default 1h
        
        last_candle_close_time = last_candle_time + duration
        now_ms = int(datetime.now().timestamp() * 1000)
        
        # If the candle hasn't closed yet, remove it to ensure stability
        if last_candle_close_time > now_ms:
            all_candles.pop()

    return all_candles


def convert_coin_to_symbol(coin: str) -> str:
    """
    Converte formato de par (SOL/USDT) para formato Binance (SOLUSDT).
    """
    return coin.replace("/", "").upper()


async def get_market_data(
    coin: str,
    days: int = 90,
    timeframe: str = "1h",
    source: str = "auto"
) -> Dict[str, Any]:
    """
    Busca dados de mercado de forma unificada.
    
    Args:
        coin: Par de trading (ex: "SOL/USDT")
        days: Número de dias
        timeframe: Intervalo (1h, 4h, 1d)
        source: Fonte de dados (auto, binance, etc)
        
    Returns:
        Dict com coin, data (OHLCV), indicators disponíveis
    """
    symbol = convert_coin_to_symbol(coin)
    
    # Por enquanto só Binance implementada
    candles = await fetch_binance_klines(symbol, timeframe, days)
    
    # Calcular indicadores se houver dados
    if candles:
        try:
            df = pd.DataFrame(candles)
            # Garantir tipos numéricos
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].astype(float)
            
            # Calcular indicadores
            df['ema_9'] = calc_ema(df['close'], 9)
            df['ema_21'] = calc_ema(df['close'], 21)
            df['rsi_14'] = calc_rsi(df['close'], 14)
            
            # Atualizar candles com indicadores (tratar NaN como None para JSON)
            df = df.replace({np.nan: None})
            
            # Reconstruir lista de candles com indicadores
            # Otimização: iterar e atualizar um a um para garantir o dicionário original
            indicators_subset = df[['ema_9', 'ema_21', 'rsi_14']]
            for i, candle in enumerate(candles):
                candle['ema_9'] = indicators_subset['ema_9'].iloc[i]
                candle['ema_21'] = indicators_subset['ema_21'].iloc[i]
                candle['rsi_14'] = indicators_subset['rsi_14'].iloc[i]

        except Exception as e:
            # Imprimir erro mas não falhar a request principal
            import traceback
            traceback.print_exc()
            print(f"Erro ao calcular indicadores no data_loader: {e}")
            
    return {
        "coin": coin,
        "days": days,
        "timeframe": timeframe,
        "source": "binance",
        "data": candles,
        "indicators": ["ema_9", "ema_21", "rsi_14"],
    }
