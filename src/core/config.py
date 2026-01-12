"""
Trading Configuration - Fees and Settings per Coin
===================================================

Este arquivo centraliza todas as configurações de taxas e custos
de operação para cada moeda suportada.

Slippage varia por moeda baseado em:
- Liquidez (volume médio)
- Spread típico bid/ask
- Volatilidade

Moedas mais líquidas (BTC, ETH) têm menor slippage.
Moedas menos líquidas (altcoins) têm maior slippage.
"""

# Taxa fixa da exchange (Binance Spot)
# Maker: 0.1% | Taker: 0.1% (sem desconto BNB)
EXCHANGE_FEE = 0.001  # 0.1%

# Slippage estimado por moeda (CONSERVADOR)
# Considera: latência do robô, spread bid/ask, volatilidade
# Valores realistas para trading automatizado: 0.1% a 0.3%
SLIPPAGE_BY_COIN = {
    # Alta liquidez - slippage menor (mas ainda conservador)
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


def get_total_fee(coin: str) -> float:
    """
    Retorna a taxa total (exchange + slippage) para uma moeda.
    
    Args:
        coin: Par de trading (ex: "SOL/USDT")
        
    Returns:
        Taxa total em decimal (ex: 0.0015 = 0.15%)
    """
    slippage = SLIPPAGE_BY_COIN.get(coin, DEFAULT_SLIPPAGE)
    return EXCHANGE_FEE + slippage


def get_fee_breakdown(coin: str) -> dict:
    """
    Retorna breakdown das taxas para uma moeda.
    
    Returns:
        Dict com exchange_fee, slippage, total_fee (todos em decimal)
    """
    slippage = SLIPPAGE_BY_COIN.get(coin, DEFAULT_SLIPPAGE)
    return {
        "exchange_fee": EXCHANGE_FEE,
        "slippage": slippage,
        "total_fee": EXCHANGE_FEE + slippage,
        "total_fee_pct": f"{(EXCHANGE_FEE + slippage) * 100:.2f}%"
    }


# Configurações de moedas disponíveis
COINS = ['SOL/USDT', 'ETH/USDT', 'BTC/USDT', 'XRP/USDT', 'AVAX/USDT', 'DOGE/USDT']

# Para compatibilidade com código legado
COMMISSION = EXCHANGE_FEE
SLIPPAGE = DEFAULT_SLIPPAGE
TOTAL_FEE = COMMISSION + SLIPPAGE
