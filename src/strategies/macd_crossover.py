"""
MACD Crossover Strategy - Momentum baseado em cruzamento MACD/Signal.

Uma das estratégias mais clássicas e comprovadas do mercado.
"""

import pandas as pd
from typing import List, Dict
from .base import BaseStrategy


class MACDCrossoverStrategy(BaseStrategy):
    """
    Estratégia de Momentum usando MACD (Moving Average Convergence Divergence).
    
    Compra quando a linha MACD cruza a linha Signal para cima.
    Vende quando a linha MACD cruza a linha Signal para baixo.
    """
    
    name = "MACD Crossover"
    slug = "macd_crossover"
    category = "momentum"
    icon = "📈"
    
    description = "Compra/vende no cruzamento das linhas MACD e Signal"
    
    explanation = """
### 📈 Estratégia MACD Crossover
**Conceito:** "Surfando o Momentum"

O **MACD** (Moving Average Convergence Divergence) é um dos indicadores mais populares e confiáveis. Ele mostra a relação entre duas médias móveis.

#### 📊 Componentes:
- **Linha MACD:** Diferença entre EMA12 e EMA26
- **Linha Signal:** EMA9 do MACD (mais suave)
- **Histograma:** Diferença entre MACD e Signal

#### 🎯 Sinais:
- 🟢 **Compra:** Quando MACD cruza Signal **para cima** (momentum bullish)
- 🔴 **Venda:** Quando MACD cruza Signal **para baixo** (momentum bearish)

#### ✅ Vantagens:
- Captura mudanças de momentum antes de movimentos grandes
- Funciona bem em timeframes de 1h a 4h
- Menos sinais falsos que RSI puro

#### ⚠️ Desvantagens:
- Indicador "atrasado" (lagging) - entrada não é no topo/fundo exato
- Gera whipsaws em mercados laterais muito estreitos

#### 💡 Dica:
Use o histograma como confirmação: barras crescentes confirmam força do movimento.
"""
    
    ideal_for = "Mercados com momentum claro, timeframes de 1h a 4h"
    
    parameters = {
        "require_positive_histogram": {
            "default": 0,
            "min": 0,
            "max": 1,
            "label": "Exigir Histograma Positivo (0=Não, 1=Sim)",
            "help": "Se ativo, só compra quando histograma também for positivo"
        }
    }
    
    def apply(self, df: pd.DataFrame, **params) -> List[Dict]:
        """Aplica estratégia de MACD Crossover."""
        
        p = self.validate_params(**params)
        require_hist = p["require_positive_histogram"] == 1
        
        trades = []
        in_position = False
        
        # Verifica se MACD existe
        if 'macd' not in df.columns or 'macd_signal' not in df.columns:
            return []
        
        # Calcula histograma se não existir
        if 'macd_hist' not in df.columns:
            df = df.copy()
            df['macd_hist'] = df['macd'] - df['macd_signal']
        
        for i in range(1, len(df)):
            macd = df['macd'].iloc[i]
            signal = df['macd_signal'].iloc[i]
            prev_macd = df['macd'].iloc[i-1]
            prev_signal = df['macd_signal'].iloc[i-1]
            hist = df['macd_hist'].iloc[i]
            price = df['close'].iloc[i]
            ts = df.index[i]
            
            # Skip NaN
            if pd.isna(macd) or pd.isna(signal) or pd.isna(prev_macd) or pd.isna(prev_signal):
                continue
            
            # Buy: MACD cruza Signal para cima
            crossover_up = prev_macd <= prev_signal and macd > signal
            
            if crossover_up and not in_position:
                # Filtro opcional de histograma
                if require_hist and hist <= 0:
                    continue
                    
                trades.append({
                    "action": "BUY",
                    "price": price,
                    "amount": 1.0,
                    "coin": "Fixed",
                    "timestamp": ts,
                    "reason": f"MACD Crossover ↑ (MACD={macd:.2f} > Signal={signal:.2f})"
                })
                in_position = True
            
            # Sell: MACD cruza Signal para baixo
            crossover_down = prev_macd >= prev_signal and macd < signal
            
            if crossover_down and in_position:
                trades.append({
                    "action": "SELL",
                    "price": price,
                    "amount": 1.0,
                    "coin": "Fixed",
                    "timestamp": ts,
                    "reason": f"MACD Crossover ↓ (MACD={macd:.2f} < Signal={signal:.2f})"
                })
                in_position = False
        
        return trades
