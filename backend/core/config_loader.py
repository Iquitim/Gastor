"""
Config Loader - Abstraction for Secret Management
=================================================

Centraliza a leitura de configurações sensíveis.
Padrão "Pulo do Gato":
1. Tenta ler de Docker Secrets (/run/secrets/{key}) - Futuro Swarm/K8s
2. Tenta ler de Environment Variables (os.getenv) - Atual .env

Isso permite migrar a infraestrutura sem alterar o código da aplicação.
"""

import os
from pathlib import Path
from typing import Optional

class ConfigLoader:
    
    # Caminho padrão para secrets no Docker Swarm
    SECRETS_DIR = Path("/run/secrets")

    @classmethod
    def get_secret(cls, key: str, default: Optional[str] = None) -> str:
        """
        Recupera um segredo/configuração.
        
        Ordem de precedência:
        1. Arquivo em /run/secrets/{key} (Docker Secret)
        2. Variável de Ambiente
        3. Valor default
        """
        
        # 1. Tentar Docker Secret (Prioridade Máxima)
        secret_file = cls.SECRETS_DIR / key
        if secret_file.exists():
            try:
                return secret_file.read_text().strip()
            except Exception:
                pass # Falha ao ler arquivo, tentar env var
        
        # 2. Tentar Environment Variable (Padrão Atual)
        return os.getenv(key, default)
    
    @classmethod
    def get_bool(cls, key: str, default: bool = False) -> bool:
        """Helper para booleanos."""
        val = cls.get_secret(key, str(default)).lower()
        return val in ("true", "1", "yes", "on")

    @classmethod
    def get_int(cls, key: str, default: int = 0) -> int:
        """Helper para inteiros."""
        try:
            return int(cls.get_secret(key, str(default)))
        except ValueError:
            return default
