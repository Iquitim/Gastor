"""
Glossary Routes
===============

Endpoints for trading glossary and educational content.
"""

from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional

router = APIRouter()


# Glossário será migrado de tab_glossary.py
GLOSSARY_CATEGORIES = [
    "conceitos_basicos",
    "medias_moveis",
    "osciladores",
    "volatilidade",
    "termos_gerais"
]


@router.get("/")
async def list_glossary(
    category: Optional[str] = Query(None, description="Filtrar por categoria")
) -> Dict[str, Any]:
    """
    Lista todos os termos do glossário.
    
    Opcionalmente filtra por categoria.
    """
    # TODO: Migrar GLOSSARY de tab_glossary.py
    
    sample_terms = [
        {
            "slug": "candlestick",
            "name": "Candlestick",
            "category": "conceitos_basicos",
            "short_description": "Representação visual de preço em um período"
        },
        {
            "slug": "rsi",
            "name": "RSI (Relative Strength Index)",
            "category": "osciladores",
            "short_description": "Oscilador que mede força do movimento"
        },
        {
            "slug": "ema",
            "name": "EMA (Exponential Moving Average)",
            "category": "medias_moveis",
            "short_description": "Média móvel com peso exponencial (período baseado em CANDLES)"
        },
        {
            "slug": "golden_cross",
            "name": "Golden Cross",
            "category": "medias_moveis",
            "short_description": "Cruzamento de EMAs indicando reversão de alta (EMA 12/26 padrão)"
        }
    ]
    
    if category:
        sample_terms = [t for t in sample_terms if t["category"] == category]
    
    return {
        "categories": GLOSSARY_CATEGORIES,
        "total": len(sample_terms),
        "terms": sample_terms
    }


@router.get("/{slug}")
async def get_term(slug: str) -> Dict[str, Any]:
    """
    Retorna detalhes completos de um termo do glossário.
    
    Inclui fórmula, explicação detalhada e analogias.
    """
    # TODO: Buscar do glossário real
    
    if slug == "rsi":
        return {
            "slug": "rsi",
            "name": "RSI (Relative Strength Index)",
            "category": "osciladores",
            "short_description": "Oscilador que mede força do movimento",
            "full_explanation": "O RSI é um indicador de momentum que mede a velocidade e magnitude das mudanças de preço...",
            "formula": "RSI = 100 - (100 / (1 + RS))",
            "formula_legend": {
                "RS": "Média de ganhos / Média de perdas",
                "100": "Normalização para escala 0-100"
            },
            "analogy": "Imagine um corredor: quanto mais ele corre sem descansar (RSI > 70), mais cansado fica e precisa parar. Quanto mais descansa (RSI < 30), mais energia tem para correr.",
            "usage": [
                "RSI < 30: Zona de sobrevenda (possível reversão para alta)",
                "RSI > 70: Zona de sobrecompra (possível reversão para baixa)"
            ]
        }
    
    if slug == "ema":
        return {
            "slug": "ema",
            "name": "EMA (Exponential Moving Average)",
            "category": "medias_moveis",
            "short_description": "Média móvel com peso exponencial nos preços mais recentes",
            "full_explanation": """A EMA (Média Móvel Exponencial) dá mais peso aos preços recentes, reagindo mais rápido a mudanças do que a SMA.

**IMPORTANTE: O período da EMA é baseado em CANDLES, não em dias!**

- Se timeframe = 1m → EMA(12) usa os últimos 12 minutos
- Se timeframe = 1h → EMA(12) usa as últimas 12 horas  
- Se timeframe = 1d → EMA(12) usa os últimos 12 dias

O multiplicador de peso é calculado como: 2 / (período + 1)

Quanto menor o período, mais sensível a mudanças de preço.""",
            "formula": "EMA = (Preço × k) + (EMA_anterior × (1 - k))",
            "formula_legend": {
                "Preço": "Preço de fechamento do candle atual",
                "k": "Multiplicador = 2 / (período + 1)",
                "EMA_anterior": "Valor da EMA no candle anterior"
            },
            "analogy": "A EMA é como uma memória que valoriza mais o que aconteceu recentemente. Quanto maior o período, mais 'esquecida' ela fica de mudanças rápidas.",
            "usage": [
                "EMA curta (9-12): Mais sensível, bom para entradas rápidas",
                "EMA longa (21-26): Mais suave, boa para identificar tendência",
                "Preço acima da EMA: Tendência de alta",
                "Preço abaixo da EMA: Tendência de baixa"
            ],
            "recommended_periods": {
                "1m": "EMA 5/13 ou 12/26 (menos ruído)",
                "15m": "EMA 9/21",
                "1h": "EMA 12/26",
                "4h": "EMA 12/26 ou 20/50",
                "1d": "EMA 50/200 (institucional)"
            }
        }
    
    if slug == "golden_cross":
        return {
            "slug": "golden_cross",
            "name": "Golden Cross",
            "category": "medias_moveis",
            "short_description": "Cruzamento de médias móveis indicando reversão de alta",
            "full_explanation": """O Golden Cross ocorre quando uma média móvel de curto prazo cruza ACIMA de uma média móvel de longo prazo.

**No Gastor, usamos EMA 12/26 como padrão** (baseado no padrão MACD).

**PERÍODOS SÃO BASEADOS EM CANDLES:**
- Timeframe 1m + EMA 12 = usa os últimos 12 minutos
- Timeframe 1h + EMA 12 = usa as últimas 12 horas
- Timeframe 1d + EMA 12 = usa os últimos 12 dias

O oposto (Death Cross) ocorre quando a EMA rápida cruza ABAIXO da lenta.""",
            "formula": "Golden Cross: EMA_rápida > EMA_lenta (após cruzamento)",
            "formula_legend": {
                "EMA_rápida": "Média móvel de curto prazo (ex: 12 candles)",
                "EMA_lenta": "Média móvel de longo prazo (ex: 26 candles)"
            },
            "analogy": "É como dois carros em uma corrida: quando o carro mais rápido (EMA curta) ultrapassa o mais lento (EMA longa), indica que o momentum está acelerando.",
            "usage": [
                "EMA rápida > EMA lenta: Sinal de COMPRA",
                "EMA rápida < EMA lenta: Sinal de VENDA (Death Cross)",
                "Combine com volume para confirmar a força do sinal"
            ],
            "gastor_defaults": {
                "fast": 12,
                "slow": 26,
                "explanation": "Baseado no padrão MACD, oferece bom equilíbrio entre sensibilidade e estabilidade"
            }
        }
    
    return {
        "error": f"Termo '{slug}' não encontrado",
        "available": ["rsi", "ema", "golden_cross", "candlestick"]
    }


@router.get("/search/{query}")
async def search_glossary(query: str) -> List[Dict[str, Any]]:
    """
    Busca termos no glossário por nome ou descrição.
    """
    # TODO: Implementar busca full-text
    return []
