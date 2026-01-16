# Testes de Estresse - Gastor

Este diretório contém testes de estresse para validar estratégias de trading em múltiplos períodos e condições de mercado.

## Estrutura

```
tests/
├── __init__.py
├── stress/
│   ├── __init__.py
│   └── test_rsi_reversal.py    # Stress test da estratégia RSI Reversal
└── README.md
```

## Como Executar

### Stress Test RSI Reversal

```bash
# Da raiz do projeto
cd /home/silvano/Documentos/projetos/Gastor
source venv/bin/activate

# Rodar o teste
python tests/stress/test_rsi_reversal.py
```

### O que o teste faz

1. Carrega dados históricos de SOL/USDT em múltiplos períodos (90, 120, 180, 365 dias)
2. Aplica a estratégia RSI Reversal com parâmetros otimizados (rsi_buy=20, rsi_sell=60)
3. Calcula métricas de performance (PnL, Win Rate, Max Drawdown)
4. Avalia se a estratégia passaria no FTMO Challenge em cada período
5. Gera relatório de recomendação

### Critérios FTMO

- ✅ Meta de Lucro: +10% mínimo
- ✅ Max Drawdown: < 10%
- ✅ Max Daily Loss: < 5%
- ✅ Dias de Trading: mínimo 4 dias

## Adicionar Novos Testes

Crie um arquivo `test_<nome_estrategia>.py` no diretório `stress/` seguindo o padrão de `test_rsi_reversal.py`.
