
import pandas as pd
from typing import List, Dict, Any, Optional
from core.database import SessionLocal
from core.models import Strategy
from core.database import SessionLocal
from core.models import Strategy
# Indicators are now calculated by the Strategy classes
from core.strategies.factory import get_strategy_class

def calculate_triggers(
    strategy_slug: str, 
    strategy_params: Dict, 
    candle_history: List[Dict], 
    has_position: bool
) -> Dict:
    print(f"DEBUG: calculate_triggers called for {strategy_slug}")
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
    
    # Instantiate Strategy
    # from core.strategies.factory import get_strategy_class (Moved to top)
    
    # Handle custom strategy slug mapping
    target_slug = slug
    if slug.startswith("custom_"):
        target_slug = "custom"
        # Load rules from DB if not in params
        if "rules" not in params:
            rules = _load_custom_rules(slug)
            if rules:
                params["rules"] = rules

    strategy_cls = get_strategy_class(target_slug)
    
    if not strategy_cls:
        return {
            "status": "error",
            "message": f"Strategy {slug} not found",
            "buy_rules": [],
            "sell_rules": []
        }

    strategy = strategy_cls(params)
    # Generate signals and indicators
    df = strategy.generate_signals(df)
    
    # Extract last row
    last_row = df.iloc[-1]
    
    buy_rules = []
    sell_rules = []
    
    # Common helper to format rules
    def format_rule(indicator, current, op, threshold, active):
        return {
            "indicator": indicator,
            "current": round(current, 4) if isinstance(current, (int, float)) else str(current),
            "operator": op,
            "threshold": threshold,
            "active": bool(active)
        }

    if slug == "rsi_reversal":
        rsi_period = int(strategy.get_param("rsi_period", 14))
        rsi_buy = float(strategy.get_param("rsi_buy", 30))
        rsi_sell = float(strategy.get_param("rsi_sell", 70))
        
        current_rsi = float(last_row.get('rsi', 0))
        
        buy_rules.append(format_rule(f"RSI({rsi_period})", current_rsi, "<", rsi_buy, current_rsi < rsi_buy))
        sell_rules.append(format_rule(f"RSI({rsi_period})", current_rsi, ">", rsi_sell, current_rsi > rsi_sell))

    elif slug == "golden_cross":
        fast = int(strategy.get_param("fast", 9))
        slow = int(strategy.get_param("slow", 21))
        
        curr_fast = float(last_row.get('ema_fast', 0))
        curr_slow = float(last_row.get('ema_slow', 0))
        
        buy_rules.append(format_rule(f"EMA({fast})", curr_fast, ">", f"EMA({slow}): {curr_fast:.4f}", curr_fast > curr_slow))
        sell_rules.append(format_rule(f"EMA({fast})", curr_fast, "<", f"EMA({slow}): {curr_slow:.4f}", curr_fast < curr_slow))

    elif slug == "macd_crossover":
        curr_macd = float(last_row.get('macd', 0))
        curr_sig = float(last_row.get('macd_signal', 0))
        
        buy_rules.append(format_rule("MACD", curr_macd, ">", f"Signal: {curr_sig:.4f}", curr_macd > curr_sig))
        sell_rules.append(format_rule("MACD", curr_macd, "<", f"Signal: {curr_sig:.4f}", curr_macd < curr_sig))

    elif slug == "bollinger_bounce":
        curr_price = float(last_row['close'])
        lower = float(last_row.get('bb_lower', 0))
        upper = float(last_row.get('bb_upper', 0))
        
        buy_rules.append(format_rule("Price", curr_price, "<=", f"Low Band: {lower:.4f}", curr_price <= lower))
        sell_rules.append(format_rule("Price", curr_price, ">=", f"Up Band: {upper:.4f}", curr_price >= upper))

    elif slug == "trend_following":
         curr_price = float(last_row['close'])
         curr_ema = float(last_row.get('ema', 0))
         curr_vol = float(last_row.get('vol_ratio', 0))
         vol_mult = float(strategy.get_param("volume_mult", 1.5))
         
         buy_rules.append(format_rule("Price", curr_price, ">", f"EMA: {curr_ema:.4f}", curr_price > curr_ema))
         buy_rules.append(format_rule("Vol Ratio", curr_vol, ">", vol_mult, curr_vol > vol_mult))
         sell_rules.append(format_rule("Price", curr_price, "<", f"EMA: {curr_ema:.4f}", curr_price < curr_ema))

    elif slug == "stochastic_rsi":
         curr_k = float(last_row.get('stoch_k', 50))
         buy_level = int(strategy.get_param("stoch_buy", 20))
         sell_level = int(strategy.get_param("stoch_sell", 80))
         
         buy_rules.append(format_rule("Stoch K", curr_k, "<", buy_level, curr_k < buy_level))
         sell_rules.append(format_rule("Stoch K", curr_k, ">", sell_level, curr_k > sell_level))
    
    elif slug == "donchian_breakout":
         curr_price = float(last_row['close'])
         # Strategy implementation has donchian_upper/lower
         # Breakout logic uses shift(1)
         # We can try to reconstruct logic or trust the signals
         # But for UI "Current Status" we usually show current vs threshold
         
         # Note: Strategy logic: close > upper.shift(1).
         # For visualization, maybe show previous upper?
         prev_upper = float(df['donchian_upper'].iloc[-2]) if len(df) > 1 else 0
         prev_lower = float(df['donchian_lower'].iloc[-2]) if len(df) > 1 else 0
         
         buy_rules.append(format_rule("Price", curr_price, ">", f"Prev High: {prev_upper:.4f}", curr_price > prev_upper))
         sell_rules.append(format_rule("Price", curr_price, "<", f"Prev Low: {prev_lower:.4f}", curr_price < prev_lower))

    elif slug == "ema_rsi_combo":
        curr_fast = float(last_row.get('ema_fast', 0))
        curr_slow = float(last_row.get('ema_slow', 0))
        curr_rsi = float(last_row.get('rsi', 0))
        rsi_min = int(strategy.get_param("rsi_filter", 50))
        
        buy_rules.append(format_rule("Fast EMA", curr_fast, ">", f"Slow: {curr_slow:.4f}", curr_fast > curr_slow))
        buy_rules.append(format_rule("RSI", curr_rsi, ">", rsi_min, curr_rsi > rsi_min))
        sell_rules.append(format_rule("Fast EMA", curr_fast, "<", f"Slow: {curr_slow:.4f}", curr_fast < curr_slow))
    
    elif slug == "macd_rsi_combo":
        curr_macd = float(last_row.get('macd', 0))
        curr_sig = float(last_row.get('macd_signal', 0))
        curr_rsi = float(last_row.get('rsi', 0))
        rsi_confirm = int(strategy.get_param("rsi_confirm", 50))
        
        buy_rules.append(format_rule("MACD", curr_macd, ">", f"Signal: {curr_sig:.4f}", curr_macd > curr_sig))
        buy_rules.append(format_rule("RSI", curr_rsi, ">", rsi_confirm, curr_rsi > rsi_confirm))
        sell_rules.append(format_rule("MACD", curr_macd, "<", f"Signal: {curr_sig:.4f}", curr_macd < curr_sig))
    
    elif slug == "volume_breakout":
        # Strategy logic: buy if volume spike AND price jump
        # Columns: vol_spike, price_jump. values are boolean.
        # But we want numeric values for UI.
        # Strategy implementation for VolumeBreakout DOES NOT export 'vol_ratio' to DF currently?
        # Let's check VolumeBreakout implementation.
        # If it doesn't, we can't show it easily without modifying the strategy.
        # For now, let's just show the booleans or skip detailed rules for VB.
        pass
    
    # Generic Signal Fallback (if specific UI logic above fails or is missing)
    if not buy_rules and not sell_rules:
         buy_rules.append(format_rule("Strategy Signal", "Active" if last_row.get('buy_signal') else "Inactive", "==", "Active", last_row.get('buy_signal')))
         sell_rules.append(format_rule("Strategy Signal", "Active" if last_row.get('sell_signal') else "Inactive", "==", "Active", last_row.get('sell_signal')))
    
    # Estratégias customizadas (Generic Handler based on params/rules)
    if target_slug == "custom":
        custom_rules = params.get("rules")
        if custom_rules:
            # Helper to parse triggers using the DF columns
            def parse_triggers_from_df(last_row, rules):
                triggers = []
                for group in rules:
                    for rule in group.get("rules", []):
                        ind_name = rule.get("indicator", "close")
                        period = int(rule.get("period", 0))
                        
                        # Construct key matching Custom strategy _get_indicator_series
                        # Strategies use format: "{name}_{period}"
                        if ind_name == "close": 
                            current_val = float(last_row['close'])
                            display_name = "Price"
                        elif ind_name == "volume":
                            current_val = float(last_row['volume'])
                            display_name = "Volume"
                        else:
                            key = f"{ind_name}_{period}"
                            current_val = float(last_row.get(key, 0))
                            display_name = f"{ind_name.upper()}({period})"
                        
                        # Threshold
                        value_type = rule.get("valueType", "constant")
                        if value_type == "constant":
                            threshold = float(rule.get("value", 0))
                            threshold_display = threshold
                        else:
                            rhs_name = str(rule.get("value"))
                            rhs_period = int(rule.get("valuePeriod", 0))
                            if rhs_name == "close":
                                threshold = float(last_row['close'])
                            else:
                                rhs_key = f"{rhs_name}_{rhs_period}"
                                threshold = float(last_row.get(rhs_key, 0))
                            threshold_display = f"{rhs_name.upper()}({rhs_period}): {threshold:.4f}"

                        op = rule.get("operator", "<")
                        active = False
                        if op == "<": active = current_val < threshold
                        elif op == ">": active = current_val > threshold
                        elif op == "<=": active = current_val <= threshold
                        elif op == ">=": active = current_val >= threshold
                        elif op == "==": active = current_val == threshold
                        
                        triggers.append(format_rule(display_name, current_val, op, threshold_display, active))
                return triggers

            buy_rules = parse_triggers_from_df(last_row, custom_rules.get("buy", []))
            sell_rules = parse_triggers_from_df(last_row, custom_rules.get("sell", []))

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

# Removed _parse_custom_triggers as it is no longer needed


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
