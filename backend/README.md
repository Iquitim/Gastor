# Backend Gastor

API REST desenvolvida em FastAPI para controlar a lógica de trade, backtests e otimização.

## Estrutura

- `api/routes`: Endpoints da API (Market Data, Strategies, Optimization).
- `core/`: Lógica de negócio (Backtest Engine, Indicators, Data Loader).
- `strategies/`: Implementação das estratégias.

## Setup de Desenvolvimento

Requer Python 3.9+.

```bash
# 1. Criar ambiente virtual
python -m venv venv

# 2. Ativar ambiente
# Linux/Mac:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 3. Instalar dependências
# 3. Instalar dependências (Recomendado via UV)
# Instale o uv: curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install -r requirements.txt

# Ou via pip clássico:
pip install -r requirements.txt

# 4. Iniciar servidor
uvicorn main:app --reload
```

A API estará disponível em `http://localhost:8000`.
Documentação automática (Swagger UI) em `http://localhost:8000/docs`.
