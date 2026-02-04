
from typing import Dict, Optional

def evaluate_signal(triggers: Dict, has_position: bool, session_id: int) -> Optional[str]:
    """
    Avalia sinais baseado no estado ATUAL dos indicadores (Level Trigger).
    Isso garante que se o dashboard mostra "Ativo", o bot entra (Late Entry).
    """
    try:
        status = triggers.get("status")
        if status != "ready":
            print(f"[Signal {session_id}] ⏳ Triggers not ready: status={status}")
            return None
        
        buy_rules = triggers.get("buy_rules", [])
        sell_rules = triggers.get("sell_rules", [])
        
        # Log detalhado dos triggers
        buy_active = sum(1 for r in buy_rules if r["active"])
        sell_active = sum(1 for r in sell_rules if r["active"])
        print(f"[Signal {session_id}] 🎯 Buy: {buy_active}/{len(buy_rules)} active | Sell: {sell_active}/{len(sell_rules)} active | HasPos: {has_position}")
        
        # Lógica de Compra: TODOS os gatilhos devem estar ativos (AND)
        # Se não tiver regras, não compra
        should_buy = len(buy_rules) > 0 and all(r["active"] for r in buy_rules)
        
        # Lógica de Venda: QUALQUER gatilho ativo dispara venda (OR)
        # (Stop loss, Take profit, Reversal, etc)
        should_sell = len(sell_rules) > 0 and any(r["active"] for r in sell_rules)
        
        if should_buy and not has_position:
            print(f"[PaperEngine {session_id}] Signal detected: RSI/Trend Active -> BUY")
            return "BUY"
        
        elif should_sell and has_position:
            print(f"[PaperEngine {session_id}] Signal detected: Exit Condition -> SELL")
            return "SELL"
            
    except Exception as e:
        print(f"[PaperEngine {session_id}] Error evaluating signals: {e}")
        
    return None
