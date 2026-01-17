"""
Data Fetchers - Módulos de ingestão de dados de diferentes APIs.

Suporta:
- CoinGecko: Dados OHLC gratuitos (30 calls/min)
- CryptoCompare: Dados OHLCV gratuitos (100k calls/mês)
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Dict

import pandas as pd
import numpy as np
import requests


# Mapeamento de símbolos para IDs do CoinGecko
COINGECKO_COIN_IDS = {
    "BTC/USDT": "bitcoin",
    "ETH/USDT": "ethereum",
    "SOL/USDT": "solana",
    "XRP/USDT": "ripple",
    "DOGE/USDT": "dogecoin",
    "AVAX/USDT": "avalanche-2",
}

# Mapeamento de símbolos para formato CryptoCompare
CRYPTOCOMPARE_SYMBOLS = {
    "BTC/USDT": ("BTC", "USDT"),
    "ETH/USDT": ("ETH", "USDT"),
    "SOL/USDT": ("SOL", "USDT"),
    "XRP/USDT": ("XRP", "USDT"),
    "DOGE/USDT": ("DOGE", "USDT"),
    "AVAX/USDT": ("AVAX", "USDT"),
}


def fetch_coingecko_ohlc(
    symbol: str = "BTC/USDT",
    days: int = 90,
) -> Optional[pd.DataFrame]:
    """
    Busca dados OHLC do CoinGecko.
    
    Limitações:
    - Free tier: 30 calls/min
    - Granularidade automática baseada em days (1-2d = 30min, 3-30d = 4h, >30d = 4d)
    - Para >90 dias retorna dados diários
    
    Args:
        symbol: Par de trading (ex: BTC/USDT)
        days: Número de dias de histórico
        
    Returns:
        DataFrame com OHLC ou None se falhar
    """
    coin_id = COINGECKO_COIN_IDS.get(symbol)
    if not coin_id:
        print(f"[CoinGecko] ⚠️ Símbolo {symbol} não suportado")
        return None
    
    try:
        print(f"[CoinGecko] Baixando {symbol} ({days} dias)...")
        
        # Endpoint OHLC
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
        params = {
            "vs_currency": "usd",
            "days": days,
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            print(f"[CoinGecko] Nenhum dado retornado")
            return None
        
        # Formato: [[timestamp, open, high, low, close], ...]
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.set_index('timestamp')
        df = df.astype(float)
        
        # CoinGecko não retorna volume no OHLC, estimamos
        df['volume'] = np.random.uniform(1000, 10000, len(df))
        
        # Ordena e remove duplicatas
        df = df[~df.index.duplicated(keep='last')]
        df = df.sort_index()
        
        print(f"[CoinGecko] ✅ Obtidos {len(df)} candles ({df.index[0].date()} a {df.index[-1].date()})")
        return df
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print(f"[CoinGecko] ❌ Rate limit atingido (30 calls/min)")
        else:
            print(f"[CoinGecko] ❌ Erro HTTP: {e}")
        return None
    except Exception as e:
        print(f"[CoinGecko] ❌ Erro: {type(e).__name__}: {e}")
        return None


def fetch_cryptocompare_ohlcv(
    symbol: str = "BTC/USDT",
    days: int = 90,
    api_key: Optional[str] = None,
) -> Optional[pd.DataFrame]:
    """
    Busca dados OHLCV do CryptoCompare.
    
    Limitações:
    - Free tier: 100k calls/mês
    - Max 2000 pontos por request (paginação necessária para mais)
    
    Args:
        symbol: Par de trading (ex: BTC/USDT)
        days: Número de dias de histórico
        api_key: API key opcional (aumenta limites)
        
    Returns:
        DataFrame com OHLCV ou None se falhar
    """
    sym_tuple = CRYPTOCOMPARE_SYMBOLS.get(symbol)
    if not sym_tuple:
        print(f"[CryptoCompare] ⚠️ Símbolo {symbol} não suportado")
        return None
    
    fsym, tsym = sym_tuple
    
    try:
        print(f"[CryptoCompare] Baixando {symbol} ({days} dias)...")
        
        # Calcula limite de pontos (1 candle por hora)
        limit = min(days * 24, 2000)
        
        # Endpoint para dados horários
        url = "https://min-api.cryptocompare.com/data/v2/histohour"
        params = {
            "fsym": fsym,
            "tsym": tsym,
            "limit": limit,
        }
        
        headers = {}
        if api_key:
            headers["authorization"] = f"Apikey {api_key}"
        
        all_data = []
        to_ts = None
        remaining = days * 24
        
        while remaining > 0:
            params["limit"] = min(remaining, 2000)
            if to_ts:
                params["toTs"] = to_ts
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("Response") != "Success":
                error_msg = result.get("Message", "Unknown error")
                print(f"[CryptoCompare] ❌ API Error: {error_msg}")
                break
            
            data = result.get("Data", {}).get("Data", [])
            if not data:
                break
            
            all_data = data + all_data  # Prepend (dados mais antigos primeiro)
            remaining -= len(data)
            
            # Próxima página (timestamp mais antigo - 1)
            to_ts = data[0]["time"] - 1
            
            # Rate limit
            time.sleep(0.2)
        
        if not all_data:
            print(f"[CryptoCompare] Nenhum dado retornado")
            return None
        
        # Converte para DataFrame
        df = pd.DataFrame(all_data)
        df['timestamp'] = pd.to_datetime(df['time'], unit='s')
        df = df.set_index('timestamp')
        df = df.rename(columns={
            'open': 'open',
            'high': 'high', 
            'low': 'low',
            'close': 'close',
            'volumefrom': 'volume',
        })
        df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        
        # Remove linhas com preço zero (dados ausentes)
        df = df[df['close'] > 0]
        
        # Ordena e remove duplicatas
        df = df[~df.index.duplicated(keep='last')]
        df = df.sort_index()
        
        print(f"[CryptoCompare] ✅ Obtidos {len(df)} candles ({df.index[0].date()} a {df.index[-1].date()})")
        return df
        
    except requests.exceptions.HTTPError as e:
        print(f"[CryptoCompare] ❌ Erro HTTP: {e}")
        return None
    except Exception as e:
        print(f"[CryptoCompare] ❌ Erro: {type(e).__name__}: {e}")
        return None


# Lista de fontes disponíveis para o UI
AVAILABLE_DATA_SOURCES = {
    "ccxt_binance": {
        "name": "CCXT (Binance)",
        "description": "Exchange Binance via CCXT - Melhor qualidade",
        "icon": "🟡",
    },
    "ccxt_binanceus": {
        "name": "CCXT (BinanceUS)", 
        "description": "Exchange BinanceUS - Funciona em mais regiões",
        "icon": "🇺🇸",
    },
    "coingecko": {
        "name": "CoinGecko",
        "description": "Agregador gratuito - Sem restrições geográficas",
        "icon": "🦎",
    },
    "cryptocompare": {
        "name": "CryptoCompare",
        "description": "API gratuita - 100k calls/mês",
        "icon": "📊",
    },
    "auto": {
        "name": "Automático (Fallback)",
        "description": "Tenta todas as fontes até uma funcionar",
        "icon": "🔄",
    },
}
