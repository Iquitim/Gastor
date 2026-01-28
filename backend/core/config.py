"""
Trading Configuration - Fees and Settings per Coin
===================================================

Configurações de taxas e custos de operação para cada moeda suportada.
Sem dependências do Streamlit - puro Python para uso no backend.
"""

from typing import Dict, Optional

# Taxa fixa da exchange (Binance Spot)
# Maker: 0.1% | Taker: 0.1% (sem desconto BNB)
EXCHANGE_FEE = 0.001  # 0.1%

# Slippage estimado por moeda (CONSERVADOR)
SLIPPAGE_BY_COIN: Dict[str, float] = {
    # Alta liquidez - slippage menor
    "BTC/USDT": 0.001,    # 0.10% - Maior liquidez do mercado
    "ETH/USDT": 0.0012,   # 0.12% - Segunda maior liquidez
    
    # Média liquidez
    "SOL/USDT": 0.0015,   # 0.15% - Boa liquidez
    "XRP/USDT": 0.0012,   # 0.12% - Alta liquidez histórica
    "DOGE/USDT": 0.002,   # 0.20% - Volátil, spreads maiores
    
    # Menor liquidez / Mais voláteis
    "AVAX/USDT": 0.0025,  # 0.25% - Liquidez moderada
}

# Slippage padrão para moedas não listadas (conservador)
DEFAULT_SLIPPAGE = 0.003  # 0.3%

# Configurações de moedas disponíveis
COINS = ['SOL/USDT', 'ETH/USDT', 'BTC/USDT', 'XRP/USDT', 'AVAX/USDT', 'DOGE/USDT']


def get_total_fee(
    coin: str, 
    custom_exchange_fee: Optional[float] = None,
    custom_slippage: Optional[Dict[str, float]] = None
) -> float:
    """
    Retorna a taxa total (exchange + slippage) para uma moeda.
    
    Args:
        coin: Par de trading (ex: "SOL/USDT")
        custom_exchange_fee: Taxa de exchange customizada (opcional)
        custom_slippage: Dict de slippage customizado por moeda (opcional)
        
    Returns:
        Taxa total em decimal (ex: 0.0015 = 0.15%)
    """
    exchange_fee = custom_exchange_fee if custom_exchange_fee is not None else EXCHANGE_FEE
    
    if custom_slippage and coin in custom_slippage:
        slippage = custom_slippage[coin]
    else:
        slippage = SLIPPAGE_BY_COIN.get(coin, DEFAULT_SLIPPAGE)
    
    return exchange_fee + slippage


def get_fee_breakdown(
    coin: str,
    custom_exchange_fee: Optional[float] = None,
    custom_slippage: Optional[Dict[str, float]] = None
) -> dict:
    """
    Retorna breakdown das taxas para uma moeda.
    
    Returns:
        Dict com exchange_fee, slippage, total_fee (todos em decimal)
    """
    exchange_fee = custom_exchange_fee if custom_exchange_fee is not None else EXCHANGE_FEE
    
    if custom_slippage and coin in custom_slippage:
        slippage = custom_slippage[coin]
    else:
        slippage = SLIPPAGE_BY_COIN.get(coin, DEFAULT_SLIPPAGE)
    
    total = exchange_fee + slippage
    
    return {
        "exchange_fee": exchange_fee,
        "slippage": slippage,
        "total_fee": total,
        "exchange_fee_pct": f"{exchange_fee * 100:.2f}%",
        "slippage_pct": f"{slippage * 100:.2f}%",
        "total_fee_pct": f"{total * 100:.2f}%"
    }


def get_all_fees() -> Dict[str, dict]:
    """Retorna breakdown de taxas para todas as moedas."""
    return {coin: get_fee_breakdown(coin) for coin in COINS}
