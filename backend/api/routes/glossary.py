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
            "short_description": "Média móvel com peso exponencial"
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
    
    return {
        "error": f"Termo '{slug}' não encontrado",
        "available": ["rsi", "ema", "candlestick"]
    }


@router.get("/search/{query}")
async def search_glossary(query: str) -> List[Dict[str, Any]]:
    """
    Busca termos no glossário por nome ou descrição.
    """
    # TODO: Implementar busca full-text
    return []
