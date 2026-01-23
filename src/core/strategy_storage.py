"""
Strategy Storage - Sistema de persistência para estratégias customizadas.

Salva e carrega estratégias como arquivos JSON.
"""

import os
import json
from typing import Dict, List, Optional
from pathlib import Path


# Diretório para salvar estratégias (relativo à raiz do projeto)
STRATEGIES_DIR = Path(__file__).parent.parent.parent / "saved_strategies"


def ensure_dir_exists():
    """Garante que o diretório de estratégias existe."""
    STRATEGIES_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(name: str) -> str:
    """Converte nome para um filename seguro."""
    # Remove caracteres especiais e espaços
    safe = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in name)
    return safe.lower()[:50]  # Limita tamanho


def save_strategy(name: str, config: Dict) -> str:
    """
    Salva uma estratégia customizada como JSON.
    
    Args:
        name: Nome da estratégia
        config: Configuração completa da estratégia
    
    Returns:
        Caminho do arquivo salvo
    """
    ensure_dir_exists()
    
    # Garante que o nome está na config
    config["name"] = name
    
    filename = sanitize_filename(name) + ".json"
    filepath = STRATEGIES_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False, default=str)
    
    return str(filepath)


def load_strategy(name: str) -> Optional[Dict]:
    """
    Carrega uma estratégia pelo nome.
    
    Args:
        name: Nome da estratégia (ou nome do arquivo sem .json)
    
    Returns:
        Configuração da estratégia ou None se não encontrada
    """
    ensure_dir_exists()
    
    # Tenta primeiro pelo nome sanitizado
    filename = sanitize_filename(name) + ".json"
    filepath = STRATEGIES_DIR / filename
    
    if not filepath.exists():
        # Tenta encontrar pelo nome exato
        for f in STRATEGIES_DIR.glob("*.json"):
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    config = json.load(file)
                    if config.get("name") == name:
                        return config
            except (json.JSONDecodeError, KeyError):
                continue
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_strategies() -> List[Dict]:
    """
    Lista todas as estratégias salvas.
    
    Returns:
        Lista com informações básicas das estratégias
        [{"name": "...", "filename": "...", "rules_count": N}, ...]
    """
    ensure_dir_exists()
    
    strategies = []
    for filepath in STRATEGIES_DIR.glob("*.json"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
                strategies.append({
                    "name": config.get("name", filepath.stem),
                    "filename": filepath.name,
                    "buy_rules_count": len(config.get("buy_rules", [])),
                    "sell_rules_count": len(config.get("sell_rules", [])),
                    "buy_logic": config.get("buy_logic", "AND"),
                    "sell_logic": config.get("sell_logic", "AND"),
                })
        except (json.JSONDecodeError, KeyError):
            continue
    
    return sorted(strategies, key=lambda x: x["name"].lower())


def delete_strategy(name: str) -> bool:
    """
    Remove uma estratégia salva.
    
    Args:
        name: Nome da estratégia
    
    Returns:
        True se removida, False se não encontrada
    """
    ensure_dir_exists()
    
    filename = sanitize_filename(name) + ".json"
    filepath = STRATEGIES_DIR / filename
    
    if filepath.exists():
        filepath.unlink()
        return True
    
    # Tenta encontrar pelo nome exato
    for f in STRATEGIES_DIR.glob("*.json"):
        try:
            with open(f, 'r', encoding='utf-8') as file:
                config = json.load(file)
                if config.get("name") == name:
                    f.unlink()
                    return True
        except (json.JSONDecodeError, KeyError):
            continue
    
    return False


def strategy_exists(name: str) -> bool:
    """Verifica se uma estratégia com esse nome já existe."""
    filename = sanitize_filename(name) + ".json"
    filepath = STRATEGIES_DIR / filename
    return filepath.exists()
