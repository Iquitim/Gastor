"""
EMA + RSI Combo Strategy - Estratégia híbrida que combina tendência e momentum.

Filtra sinais falsos exigindo confirmação de tendência E momentum.
"""

import pandas as pd
from typing import List, Dict
from .base import BaseStrategy


class EMARSIComboStrategy(BaseStrategy):
    """
    Estratégia híbrida que combina EMA (tendência) com RSI (momentum).
    
    Só compra quando:
    - Preço está acima da EMA (tendência de alta)
    - RSI não está sobrecomprado (ainda tem espaço para subir)
    
    Só vende quando:
    - Preço cruza abaixo da EMA OU RSI atinge sobrecompra
    """
    
    name = "EMA + RSI Combo"
    slug = "ema_rsi_combo"
    category = "hybrid"
    icon = "🎯"
    
    description = "Combina tendência (EMA) com momentum (RSI) para sinais mais precisos"
    
    explanation = """
### 🎯 EMA + RSI Combo
**Conceito:** "Duas Confirmações são Melhores que Uma"

Esta estratégia **combina dois indicadores** para filtrar sinais falsos:
- **EMA:** Define a DIREÇÃO (tendência)
- **RSI:** Define o TIMING (momentum)

#### 📊 Lógica:
Só entramos quando **ambas as condições** são verdadeiras:

1. **Tendência favorável:** Preço > EMA (estamos em uptrend)
2. **Momentum favorável:** RSI < 70 (ainda não está sobrecomprado)

#### 🎯 Sinais:
- 🟢 **Compra quando:**
  - Preço cruza EMA para cima **E**
  - RSI está abaixo do limiar de sobrecompra

- 🔴 **Venda quando:**
  - Preço cruza EMA para baixo **OU**
  - RSI atinge zona de sobrecompra (take profit)

#### ✅ Vantagens:
- **Menos sinais falsos** que usar EMA ou RSI isolados
- Entradas mais precisas com melhor timing
- Combina o melhor de dois mundos

#### ⚠️ Desvantagens:
- Pode perder algumas oportunidades por ser conservadora
- Requer dois indicadores alinhados (menos frequente)

#### 💡 Dica Pro:
Esta estratégia é excelente para **Day Trading** em timeframe de 1h. Os filtros reduzem drasticamente os trades perdedores.
"""
    
    ideal_for = "Day trading, timeframe 1h-4h, traders conservadores"
    
    parameters = {
        "ema_period": {
            "default": 21,
            "min": 9,
            "max": 100,
            "label": "Período EMA",
            "help": "Período da EMA para definir tendência"
        },
        "rsi_overbought": {
            "default": 70,
            "min": 60,
            "max": 85,
            "label": "RSI Sobrecompra",
            "help": "Acima deste valor, não compra e considera venda"
        },
        "rsi_oversold": {
            "default": 30,
            "min": 15,
            "max": 40,
            "label": "RSI Sobrevenda",
            "help": "Usado para identificar oportunidades em tendência de alta"
        }
    }
    
    def apply(self, df: pd.DataFrame, **params) -> List[Dict]:
        """Aplica estratégia EMA + RSI Combo."""
        
        p = self.validate_params(**params)
        ema_period = p["ema_period"]
        rsi_overbought = p["rsi_overbought"]
        rsi_oversold = p["rsi_oversold"]
        
        trades = []
        in_position = False
        entry_price = 0
        
        # Prepara dados
        df = df.copy()
        
        # Tenta usar EMA existente ou calcula
        ema_col = f'ema{ema_period}'
        if ema_col not in df.columns:
            # Tenta usar outra EMA próxima
            available = [c for c in df.columns if c.startswith('ema')]
            if available:
                ema_col = available[0]  # Usa a primeira disponível
            else:
                df[ema_col] = df['close'].ewm(span=ema_period, adjust=False).mean()
        
        if 'rsi' not in df.columns:
            return []
        
        for i in range(1, len(df)):
            price = df['close'].iloc[i]
            ema = df[ema_col].iloc[i]
            rsi = df['rsi'].iloc[i]
            prev_price = df['close'].iloc[i-1]
            prev_ema = df[ema_col].iloc[i-1]
            ts = df.index[i]
            
            # Skip NaN
            if pd.isna(ema) or pd.isna(rsi) or pd.isna(prev_ema):
                continue
            
            # === CONDIÇÕES DE COMPRA ===
            # 1. Preço cruzou EMA para cima (ou está acima e RSI saiu de sobrevenda)
            # 2. RSI não está sobrecomprado
            
            ema_crossover_up = prev_price <= prev_ema and price > ema
            rsi_recovery = rsi > rsi_oversold and df['rsi'].iloc[i-1] <= rsi_oversold
            
            if not in_position:
                # Entrada principal: Cruzamento de EMA + RSI não sobrecomprado
                if ema_crossover_up and rsi < rsi_overbought:
                    trades.append({
                        "action": "BUY",
                        "price": price,
                        "amount": 1.0,
                        "coin": "Fixed",
                        "timestamp": ts,
                        "reason": f"EMA+RSI Entry (Price > {ema_col.upper()}, RSI={rsi:.0f})"
                    })
                    in_position = True
                    entry_price = price
                
                # Entrada secundária: Em tendência de alta + RSI saindo de sobrevenda
                elif price > ema and rsi_recovery:
                    trades.append({
                        "action": "BUY",
                        "price": price,
                        "amount": 1.0,
                        "coin": "Fixed",
                        "timestamp": ts,
                        "reason": f"RSI Recovery in Uptrend (RSI={rsi:.0f})"
                    })
                    in_position = True
                    entry_price = price
            
            # === CONDIÇÕES DE VENDA ===
            if in_position:
                # Saída 1: Preço cruzou EMA para baixo (tendência reverteu)
                ema_crossover_down = prev_price >= prev_ema and price < ema
                
                # Saída 2: RSI atingiu sobrecompra (take profit)
                rsi_overbought_exit = rsi >= rsi_overbought
                
                if ema_crossover_down:
                    trades.append({
                        "action": "SELL",
                        "price": price,
                        "amount": 1.0,
                        "coin": "Fixed",
                        "timestamp": ts,
                        "reason": f"Trend Reversal (Price < {ema_col.upper()})"
                    })
                    in_position = False
                    
                elif rsi_overbought_exit:
                    trades.append({
                        "action": "SELL",
                        "price": price,
                        "amount": 1.0,
                        "coin": "Fixed",
                        "timestamp": ts,
                        "reason": f"Take Profit (RSI={rsi:.0f} ≥ {rsi_overbought})"
                    })
                    in_position = False
        
        return trades
