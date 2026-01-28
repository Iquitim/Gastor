"""
Market Data Routes
==================

Endpoints for fetching market data (OHLCV + indicators).
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from enum import Enum

from core.data_loader import get_market_data

router = APIRouter()


class DataSource(str, Enum):
    auto = "auto"
    binance = "binance"
    binance_us = "binance_us"
    coingecko = "coingecko"
    cryptocompare = "cryptocompare"


@router.get("/")
async def fetch_market_data(
    coin: str = Query(default="SOL/USDT", description="Par de trading (ex: SOL/USDT)"),
    days: int = Query(default=90, ge=1, le=365, description="Número de dias de histórico"),
    timeframe: str = Query(default="1h", description="Timeframe (1h, 4h, 1d)"),
    source: DataSource = Query(default=DataSource.auto, description="Fonte de dados")
):
    """
    Busca dados de mercado (OHLCV) com indicadores calculados.
    
    - **coin**: Par de trading (ex: SOL/USDT)
    - **days**: Dias de histórico (1-365)
    - **timeframe**: Intervalo dos candles (1h, 4h, 1d)
    - **source**: Fonte de dados (auto, binance, coingecko, etc)
    
    Retorna DataFrame com colunas: timestamp, open, high, low, close, volume + indicadores
    """
    try:
        result = await get_market_data(coin, days, timeframe, source.value)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados: {str(e)}")


@router.get("/latest")
async def get_latest_price(
    coin: str = Query(default="SOL/USDT", description="Par de trading")
):
    """
    Busca o preço mais recente de uma moeda.
    """
    try:
        result = await get_market_data(coin, days=1, timeframe="1h")
        if result["data"]:
            latest = result["data"][-1]
            return {
                "coin": coin,
                "price": latest["close"],
                "timestamp": latest["timestamp"],
            }
        return {
            "coin": coin,
            "price": 0.0,
            "timestamp": None,
            "message": "Sem dados disponíveis"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar preço: {str(e)}")
