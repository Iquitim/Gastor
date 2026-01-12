"""
Portfolio management functions.
Handles trade sanitization, position sizing and recalculation.
"""

import streamlit as st


def sanitize_trades(trades: list) -> list:
    """
    Remove trades inválidos (ex: Venda sem saldo) e ordena por data.
    Garante coerência do portfólio.
    
    Modo STRICT: Só permite compra se não houver posição aberta
    (isso impede sobreposição de estratégias)
    """
    if not trades:
        return []
    
    # Ordena por timestamp
    sorted_trades = sorted(trades, key=lambda x: x['timestamp'])
    
    valid_trades = []
    holdings = 0.0
    
    for t in sorted_trades:
        action = t.get('action', '').upper()
        amount = float(t.get('amount', 1.0))
        
        if action == 'BUY':
            # STRICT MODE: Só permite compra se não houver posição aberta
            if holdings < 0.0001:  # Basicamente zero
                valid_trades.append(t)
                holdings += amount
            # else: Ignora compra se já estiver posicionado
            
        elif action == 'SELL':
            # Só permite venda se tiver saldo suficiente
            if holdings >= (amount - 0.0001):
                valid_trades.append(t)
                holdings -= amount
            # else: Remove venda inválida
                
    return valid_trades


def adjust_trade_amounts(trades: list, initial_balance: float, position_size_pct: float = 100.0, 
                         force_close: bool = False, last_price: float = None, last_timestamp = None) -> list:
    """
    Ajusta os amounts dos trades para usar porcentagem do SALDO INICIAL.
    
    O valor por operação é FIXO baseado no saldo inicial, não no saldo flutuante.
    Isso permite múltiplas operações com tamanho consistente.
    
    Args:
        trades: Lista de trades com amounts placeholders
        initial_balance: Saldo inicial da conta
        position_size_pct: Porcentagem do SALDO INICIAL por operação (padrão 100%)
        force_close: Se True, adiciona SELL no final se houver posição aberta
        last_price: Preço do último candle (para force_close)
        last_timestamp: Timestamp do último candle (para force_close)
    
    Returns:
        Lista de trades com amounts ajustados
    """
    if not trades:
        return []
        
    adjusted_trades = []
    holdings = 0.0
    position_value = initial_balance * (position_size_pct / 100.0)
    
    for t in trades:
        action = t.get('action', '').upper()
        price = float(t.get('price', 0))
        
        if action == 'BUY':
            amount = position_value / price if price > 0 else 0
            t['amount'] = amount
            holdings += amount
            adjusted_trades.append(t)
            
        elif action == 'SELL':
            if holdings > 0:
                t['amount'] = holdings
                holdings = 0
                adjusted_trades.append(t)
    
    # Force close: se ainda tem posição aberta e force_close está ativo
    if force_close and holdings > 0 and last_price and last_timestamp:
        close_trade = {
            'action': 'SELL',
            'price': last_price,
            'amount': holdings,
            'timestamp': last_timestamp,
            'reason': '📌 Fechamento Forçado (fim do período)',
            'coin': 'AUTO'
        }
        adjusted_trades.append(close_trade)
        holdings = 0
    
    return adjusted_trades


def recalculate_portfolio(trades: list) -> None:
    """Recalcula o portfólio baseado na lista de trades (com sanitização)."""
    from .config import get_total_fee, COMMISSION
    
    clean_trades = sanitize_trades(trades)
    
    # Reseta portfólio
    st.session_state.trades = clean_trades
    st.session_state.balance = st.session_state.get('initial_balance', 10000.0)
    st.session_state.holdings = 0.0
    st.session_state.avg_price = 0.0
    
    # Pega moeda selecionada para usar taxa correta
    coin = st.session_state.get('sb_coin', 'SOL/USDT')
    fee_rate = get_total_fee(coin)
    
    # Recalcula posição
    for t in clean_trades:
        action = t.get('action', '').upper()
        price = float(t.get('price', 0))
        amount = float(t.get('amount', 1.0))
        
        if action == 'BUY':
            cost = amount * price
            fee = cost * fee_rate
            
            # Calcula novo preço médio
            total_holdings = st.session_state.holdings + amount
            if total_holdings > 0:
                curr_val = st.session_state.holdings * st.session_state.avg_price
                new_val = amount * price
                st.session_state.avg_price = (curr_val + new_val) / total_holdings
            
            st.session_state.balance -= (cost + fee)
            st.session_state.holdings = total_holdings
                
        elif action == 'SELL':
            revenue = amount * price
            fee = revenue * fee_rate
            st.session_state.balance += (revenue - fee)
            st.session_state.holdings -= amount
            
            if st.session_state.holdings <= 0.0001:
                st.session_state.holdings = 0.0
                st.session_state.avg_price = 0.0
