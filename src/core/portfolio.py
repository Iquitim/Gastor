"""
Portfolio management functions.
Handles trade sanitization, position sizing and recalculation.
"""

import streamlit as st
import pandas as pd


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
                         force_close: bool = False, last_price: float = None, last_timestamp = None,
                         use_compound: bool = False) -> list:
    """
    Ajusta os amounts dos trades.
    
    Args:
        trades: Lista de trades com amounts placeholders
        initial_balance: Saldo inicial da conta
        position_size_pct: Porcentagem do saldo por operação
        force_close: Se True, adiciona SELL no final se houver posição aberta
        last_price: Preço do último candle
        last_timestamp: Timestamp do último candle
        use_compound: Se True, usa saldo CORRENTE (juros compostos). 
                      Se False, usa saldo INICIAL fixo.
    
    Returns:
        Lista de trades com amounts ajustados
    """
    from .config import get_total_fee, COMMISSION
    
    if not trades:
        return []
        
    adjusted_trades = []
    
    # Estado para simulação de saldo corrente
    running_balance = initial_balance
    holdings = 0.0
    
    # Assume taxa padrão para estimativa (pode variar por moeda mas aqui simplificamos)
    # Idealmente pegaria da moeda do trade, mas assumiremos SOL/USDT ou a do primeiro trade
    fee_rate = COMMISSION 
    
    for t in trades:
        action = t.get('action', '').upper()
        price = float(t.get('price', 0))
        
        if action == 'BUY':
            if holdings == 0: # Só compra se não tiver posição (logica simplificada de portfolio unico)
                # Define base de cálculo do tamanho da posição
                base_capital = running_balance if use_compound else initial_balance
                
                # Calcula valor alvo do trade
                target_value = base_capital * (position_size_pct / 100.0)
                
                # PROTEÇÃO: Nunca investir mais do que o saldo disponível (sem alavancagem)
                # Se não estiver usando juros compostos (fixo), mas perdeu dinheiro, 
                # limita ao que sobrou na conta.
                position_value = min(target_value, running_balance)
                
                # Se saldo for insuficiente (<= 0), não opera
                if position_value <= 0:
                    position_value = 0
                
                # Ajusta amount
                amount = position_value / price if price > 0 else 0
                
                # Registra o custo (estimado para controle de fluxo)
                cost = amount * price
                fee = cost * fee_rate
                
                # Pequeno ajuste se a taxa faria o saldo ficar negativo (corner case)
                if (cost + fee) > running_balance:
                    # Reduz amount para cobrir a taxa
                    amount = running_balance / (price * (1 + fee_rate))
                    cost = amount * price
                    fee = cost * fee_rate
                
                running_balance -= (cost + fee)
                
                t['amount'] = amount
                holdings += amount
                if amount > 0:
                    adjusted_trades.append(t)
            
        elif action == 'SELL':
            if holdings > 0:
                amount = holdings # Vende tudo
                revenue = amount * price
                fee = revenue * fee_rate
                running_balance += (revenue - fee)
                
                t['amount'] = amount
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
        # Atualiza saldo final (opcional aqui, mas bom para debug)
        revenue = holdings * last_price
        fee = revenue * fee_rate
        running_balance += (revenue - fee)
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
                
                
def get_portfolio_at(trades: list, target_timestamp) -> dict:
    """
    Calcula o estado do portfólio em um momento específico (time-travel).
    Retorna dict com balance, holdings, avg_price.
    """
    from .config import get_total_fee
    
    # Filtra trades até o momento atual
    # Precisamos sanitizar TUDO primeiro para manter a lógica consistente
    clean_trades = sanitize_trades(trades)
    
    # Filtra por timestamp
    # Converte para timestamp do pandas para garantir comparação correta
    target_ts = pd.to_datetime(target_timestamp)
    relevant_trades = [t for t in clean_trades if pd.to_datetime(t['timestamp']) <= target_ts]
    
    # Estado inicial
    balance = st.session_state.get('initial_balance', 10000.0)
    holdings = 0.0
    avg_price = 0.0
    
    coin = st.session_state.get('sb_coin', 'SOL/USDT')
    fee_rate = get_total_fee(coin)
    
    for t in relevant_trades:
        action = t.get('action', '').upper()
        price = float(t.get('price', 0))
        amount = float(t.get('amount', 0))
        
        if action == 'BUY':
            cost = amount * price
            fee = cost * fee_rate
            
            total_holdings = holdings + amount
            if total_holdings > 0:
                curr_val = holdings * avg_price
                new_val = amount * price
                avg_price = (curr_val + new_val) / total_holdings
            
            balance -= (cost + fee)
            holdings = total_holdings
            
        elif action == 'SELL':
            revenue = amount * price
            fee = revenue * fee_rate
            balance += (revenue - fee)
            holdings -= amount
            
            if holdings <= 0.0001:
                holdings = 0.0
                avg_price = 0.0
                
    return {
        'balance': balance,
        'holdings': holdings,
        'avg_price': avg_price
    }
