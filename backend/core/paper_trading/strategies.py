
import pandas as pd
from typing import List, Dict, Any, Optional
from core.database import SessionLocal
from core.models import Strategy
from core.indicators import (
    calc_rsi, calc_ema, calc_macd, calc_bollinger_bands,
    calc_stochastic, calc_donchian, calc_volume_ratio
)

def calculate_triggers(
    strategy_slug: str, 
    strategy_params: Dict, 
    candle_history: List[Dict], 
    has_position: bool
) -> Dict:
    """
    Calcula os gatilhos da estratégia com base no histórico de candles.
    Retorna estrutura compatível com o endpoint /triggers.
    """
    if len(candle_history) < 20:
         return {
            "status": "collecting",
            "message": f"Coletando histórico: {len(candle_history)}/50 candles",
            "current_price": candle_history[-1]["close"] if candle_history else 0,
            "buy_rules": [],
            "sell_rules": [],
            "has_position": has_position
        }
    
    # Criar DataFrame com histórico
    df = pd.DataFrame(candle_history)
    current_price = df['close'].iloc[-1]
    
    slug = strategy_slug
    params = dict(strategy_params or {})
    
    buy_rules = []
    sell_rules = []
    
    # Estratégias pré-definidas
    if slug == "rsi_reversal":
        rsi_period = int(params.get("rsi_period", 14))
        rsi_buy = float(params.get("rsi_buy", 30))
        rsi_sell = float(params.get("rsi_sell", 70))
        
        rsi = calc_rsi(df['close'], rsi_period)
        current_rsi = float(rsi.iloc[-1])
        
        buy_rules.append({
            "indicator": f"RSI({rsi_period})",
            "current": round(current_rsi, 2),
            "operator": "<",
            "threshold": rsi_buy,
            "active": bool(current_rsi < rsi_buy),
        })
        sell_rules.append({
            "indicator": f"RSI({rsi_period})",
            "current": round(current_rsi, 2),
            "operator": ">",
            "threshold": rsi_sell,
            "active": bool(current_rsi > rsi_sell),
        })
        
    elif slug == "golden_cross":
        fast = int(params.get("fast", 12))
        slow = int(params.get("slow", 26))
        
        ema_fast = calc_ema(df['close'], fast)
        ema_slow = calc_ema(df['close'], slow)
        
        current_fast = float(ema_fast.iloc[-1])
        current_slow = float(ema_slow.iloc[-1])
        
        buy_rules.append({
            "indicator": f"EMA({fast})",
            "current": round(current_fast, 4),
            "operator": ">",
            "threshold": f"EMA({slow}): {round(current_slow, 4)}",
            "active": bool(current_fast > current_slow),
        })
        sell_rules.append({
            "indicator": f"EMA({fast})",
            "current": round(current_fast, 4),
            "operator": "<",
            "threshold": f"EMA({slow}): {round(current_slow, 4)}",
            "active": bool(current_fast < current_slow),
        })
        
    elif slug == "bollinger_bounce":
        period = int(params.get("bb_period", 20))
        std = float(params.get("bb_std", 2.0))
        
        upper, middle, lower = calc_bollinger_bands(df['close'], period, std)
        
        buy_rules.append({
            "indicator": "Preço",
            "current": round(current_price, 4),
            "operator": "<=",
            "threshold": f"BB Lower: {round(float(lower.iloc[-1]), 4)}",
            "active": bool(current_price <= float(lower.iloc[-1])),
        })
        sell_rules.append({
            "indicator": "Preço",
            "current": round(current_price, 4),
            "operator": ">=",
            "threshold": f"BB Upper: {round(float(upper.iloc[-1]), 4)}",
            "active": bool(current_price >= float(upper.iloc[-1])),
        })
        
    elif slug == "macd_crossover":
        macd, signal = calc_macd(df['close'])
        current_macd = float(macd.iloc[-1])
        current_signal = float(signal.iloc[-1])
        
        buy_rules.append({
            "indicator": "MACD",
            "current": round(current_macd, 4),
            "operator": ">",
            "threshold": f"Signal: {round(current_signal, 4)}",
            "active": bool(current_macd > current_signal),
        })
        sell_rules.append({
            "indicator": "MACD",
            "current": round(current_macd, 4),
            "operator": "<",
            "threshold": f"Signal: {round(current_signal, 4)}",
            "active": bool(current_macd < current_signal),
        })
    
    elif slug == "ema_rsi_combo":
        fast = int(params.get("fast_ema", 9))
        slow = int(params.get("slow_ema", 21))
        rsi_min = int(params.get("rsi_filter", 50))
        
        ema_fast = calc_ema(df['close'], fast)
        ema_slow = calc_ema(df['close'], slow)
        rsi = calc_rsi(df['close'], 14)
        
        current_fast = float(ema_fast.iloc[-1])
        current_slow = float(ema_slow.iloc[-1])
        current_rsi = float(rsi.iloc[-1])
        buy_rules.append({
            "indicator": f"EMA({fast})",
            "current": round(current_fast, 4),
            "operator": ">",
            "threshold": f"EMA({slow}): {round(current_slow, 4)}",
            "active": bool(current_fast > current_slow),
        })
        buy_rules.append({
            "indicator": "RSI(14)",
            "current": round(current_rsi, 2),
            "operator": ">",
            "threshold": rsi_min,
            "active": bool(current_rsi > rsi_min),
        })
        sell_rules.append({
            "indicator": f"EMA({fast})",
            "current": round(current_fast, 4),
            "operator": "<",
            "threshold": f"EMA({slow}): {round(current_slow, 4)}",
            "active": bool(current_fast < current_slow),
        })
        
    elif slug == "trend_following":
        ema_period = int(params.get("ema_period", 20))
        vol_mult = float(params.get("volume_mult", 1.5))
        
        ema = calc_ema(df['close'], ema_period)
        vol_ratio = calc_volume_ratio(df['volume'], 20)
        
        current_ema = float(ema.iloc[-1])
        current_vol = float(vol_ratio.iloc[-1]) if not pd.isna(vol_ratio.iloc[-1]) else 0
        
        buy_rules.append({
            "indicator": "Preço",
            "current": round(current_price, 4),
            "operator": ">",
            "threshold": f"EMA({ema_period}): {round(current_ema, 4)}",
            "active": bool(current_price > current_ema),
        })
        buy_rules.append({
            "indicator": "Volume Ratio",
            "current": round(current_vol, 2),
            "operator": ">",
            "threshold": vol_mult,
            "active": bool(current_vol > vol_mult),
        })
        sell_rules.append({
            "indicator": "Preço",
            "current": round(current_price, 4),
            "operator": "<",
            "threshold": f"EMA({ema_period}): {round(current_ema, 4)}",
            "active": bool(current_price < current_ema),
        })
        
    elif slug == "macd_rsi_combo":
        rsi_confirm = int(params.get("rsi_confirm", 50))
        
        macd, signal = calc_macd(df['close'])
        rsi = calc_rsi(df['close'], 14)
        
        current_macd = float(macd.iloc[-1])
        current_signal = float(signal.iloc[-1])
        current_rsi = float(rsi.iloc[-1])
        
        buy_rules.append({
            "indicator": "MACD",
            "current": round(current_macd, 4),
            "operator": ">",
            "threshold": f"Signal: {round(current_signal, 4)}",
            "active": bool(current_macd > current_signal),
        })
        buy_rules.append({
            "indicator": "RSI(14)",
            "current": round(current_rsi, 2),
            "operator": ">",
            "threshold": rsi_confirm,
            "active": bool(current_rsi > rsi_confirm),
        })
        sell_rules.append({
            "indicator": "MACD",
            "current": round(current_macd, 4),
            "operator": "<",
            "threshold": f"Signal: {round(current_signal, 4)}",
            "active": bool(current_macd < current_signal),
        })
        
    elif slug == "stochastic_rsi":
        period = int(params.get("stoch_period", 14))
        buy_level = int(params.get("stoch_buy", 20))
        sell_level = int(params.get("stoch_sell", 80))
        
        k, d = calc_stochastic(df['close'], df['high'], df['low'], period)
        current_k = float(k.iloc[-1]) if not pd.isna(k.iloc[-1]) else 50
        
        buy_rules.append({
            "indicator": f"Stoch K({period})",
            "current": round(current_k, 2),
            "operator": "<",
            "threshold": buy_level,
            "active": bool(current_k < buy_level),
        })
        sell_rules.append({
            "indicator": f"Stoch K({period})",
            "current": round(current_k, 2),
            "operator": ">",
            "threshold": sell_level,
            "active": bool(current_k > sell_level),
        })
        
    elif slug == "donchian_breakout":
        period = int(params.get("period", 20))
        
        upper, lower = calc_donchian(df['high'], df['low'], period)
        prev_upper = float(upper.iloc[-2]) if len(upper) > 1 else current_price
        prev_lower = float(lower.iloc[-2]) if len(lower) > 1 else current_price
        
        buy_rules.append({
            "indicator": "Preço",
            "current": round(current_price, 4),
            "operator": ">",
            "threshold": f"Donchian Upper: {round(prev_upper, 4)}",
            "active": bool(current_price > prev_upper),
        })
        sell_rules.append({
            "indicator": "Preço",
            "current": round(current_price, 4),
            "operator": "<",
            "threshold": f"Donchian Lower: {round(prev_lower, 4)}",
            "active": bool(current_price < prev_lower),
        })
        
    elif slug == "volume_breakout":
        lookback = int(params.get("lookback", 20))
        vol_mult = float(params.get("volume_mult", 2.0))
        price_break = float(params.get("price_break_pct", 1.0))
        
        vol_ratio = calc_volume_ratio(df['volume'], lookback)
        current_vol = float(vol_ratio.iloc[-1]) if not pd.isna(vol_ratio.iloc[-1]) else 0
        price_jump_pct = ((df['close'].iloc[-1] / df['open'].iloc[-1]) - 1) * 100
        
        buy_rules.append({
            "indicator": "Volume Ratio",
            "current": round(current_vol, 2),
            "operator": ">",
            "threshold": vol_mult,
            "active": bool(current_vol > vol_mult),
        })
        buy_rules.append({
            "indicator": "Price Jump %",
            "current": round(price_jump_pct, 2),
            "operator": ">",
            "threshold": f"{price_break}%",
            "active": bool(price_jump_pct > price_break),
        })
        
        low_n = df['low'].rolling(window=lookback).min()
        prev_low = float(low_n.iloc[-2]) if len(low_n) > 1 else current_price
        sell_rules.append({
            "indicator": "Preço",
            "current": round(current_price, 4),
            "operator": "<",
            "threshold": f"Min Low({lookback}): {round(prev_low, 4)}",
            "active": bool(current_price < prev_low),
        })
        
    # Estratégias customizadas
    elif slug.startswith("custom_") or slug == "custom":
        custom_rules = None
        if slug.startswith("custom_"):
            custom_rules = _load_custom_rules(slug)
        elif "rules" in params:
            custom_rules = params["rules"]
        
        if custom_rules:
            buy_rules = _parse_custom_triggers(df, custom_rules.get("buy", []), "buy")
            sell_rules = _parse_custom_triggers(df, custom_rules.get("sell", []), "sell")
    
    # Log de diagnóstico
    buy_active = sum(1 for r in buy_rules if r.get("active"))
    sell_active = sum(1 for r in sell_rules if r.get("active"))
    print(f"[Triggers] 📈 {slug} @ ${current_price:.2f} | Buy: {buy_active}/{len(buy_rules)} | Sell: {sell_active}/{len(sell_rules)}")
    
    return {
        "status": "ready",
        "current_price": round(current_price, 4),
        "has_position": has_position,
        "buy_rules": buy_rules,
        "sell_rules": sell_rules,
    }

def _parse_custom_triggers(df, groups: List, side: str) -> List[Dict]:
    """Parse regras customizadas e retorna valores atuais."""
    triggers = []
    
    for group in groups:
        rules = group.get("rules", [])
        for rule in rules:
            ind_name = rule.get("indicator", "close")
            period = int(rule.get("period", 14))
            operator = rule.get("operator", "<")
            value = rule.get("value", 0)
            value_type = rule.get("valueType", "constant")
            
            # Calcular indicador atual
            current_val = 0.0
            display_name = ind_name
            
            if ind_name == "rsi":
                rsi = calc_rsi(df['close'], period)
                current_val = float(rsi.iloc[-1])
                display_name = f"RSI({period})"
            elif ind_name == "ema":
                ema = calc_ema(df['close'], period)
                current_val = float(ema.iloc[-1])
                display_name = f"EMA({period})"
            elif ind_name == "sma":
                sma = df['close'].rolling(window=period).mean()
                current_val = float(sma.iloc[-1])
                display_name = f"SMA({period})"
            elif ind_name == "close":
                current_val = float(df['close'].iloc[-1])
                display_name = "Preço"
            elif ind_name == "volume":
                current_val = float(df['volume'].iloc[-1])
                display_name = "Volume"
            
            # Threshold
            if value_type == "constant":
                threshold = float(value)
                threshold_display = threshold
            else:
                # Indicador como threshold
                rhs_name = str(value)
                rhs_period = int(rule.get("valuePeriod", 14))
                if rhs_name == "ema":
                    rhs_val = float(calc_ema(df['close'], rhs_period).iloc[-1])
                    threshold_display = f"EMA({rhs_period}): {round(rhs_val, 4)}"
                    threshold = rhs_val
                else:
                    threshold = 0
                    threshold_display = rhs_name
            
            # Verificar se está ativo
            active = False
            if isinstance(threshold, (int, float)):
                if operator == "<": active = bool(current_val < threshold)
                elif operator == ">": active = bool(current_val > threshold)
                elif operator == "<=": active = bool(current_val <= threshold)
                elif operator == ">=": active = bool(current_val >= threshold)
            
            triggers.append({
                "indicator": display_name,
                "current": round(current_val, 4) if current_val < 1000 else round(current_val, 2),
                "operator": operator,
                "threshold": threshold_display,
                "active": active,
            })
    
    return triggers

def _load_custom_rules(slug: str) -> Optional[Dict]:
    """Carrega regras de estratégia customizada do banco."""
    try:
        strat_id = int(slug.split("_")[1])
        with SessionLocal() as db:
            strategy = db.query(Strategy).filter(
                Strategy.id == strat_id
            ).first()
            if strategy:
                return strategy.rules
    except Exception as e:
        print(f"[PaperStrategy] Error loading custom rules: {e}")
    return None
