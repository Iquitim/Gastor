"""
Trading Tab UI component.
Contains the main chart, buy/sell controls, and trade history.
"""

import hashlib
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.core.charting import create_chart
from src.core.portfolio import recalculate_portfolio
from src.core.data_loader import COMMISSION


def register_trade(action: str, price: float, amount: float, timestamp, coin: str):
    """Registra um trade e atualiza portfólio."""
    
    if action == 'BUY':
        cost = amount * price
        fee = cost * COMMISSION
        if st.session_state.balance < (cost + fee):
            st.error("Saldo insuficiente!")
            return None
            
    elif action == 'SELL':
        if st.session_state.holdings < amount:
            st.error("Moedas insuficientes!")
            return None
    
    trade = {
        'action': action,
        'price': price,
        'amount': amount,
        'timestamp': timestamp,
        'coin': coin,
        'reason': 'Manual'
    }
    
    st.session_state.trades.append(trade)
    recalculate_portfolio(st.session_state.trades)
    
    return trade


def render_trading_tab(df, idx: int, current_price: float, current_time, selected_coin: str, update_slider, update_num):
    """Renderiza a tab de Trading."""
    
    # --- MINI STATUS BAR (Barra de contexto no topo) ---
    status_cols = st.columns([2, 2, 2, 2])
    with status_cols[0]:
        st.metric("💰 Preço Atual", f"${current_price:.4f}")
    with status_cols[1]:
        st.metric("📅 Candle", str(current_time)[:16])
    with status_cols[2]:
        if st.session_state.holdings > 0:
            pnl_pct = ((current_price - st.session_state.avg_price) / st.session_state.avg_price) * 100
            st.metric("📈 Posição", f"{st.session_state.holdings:.4f}", delta=f"{pnl_pct:+.1f}%")
        else:
            st.metric("📈 Posição", "Sem posição")
    with status_cols[3]:
        st.metric("💵 Saldo", f"${st.session_state.balance:,.2f}")
    
    # Info do período com destaque visual
    start_date = str(df.index[0])[:10]
    end_date = str(df.index[-1])[:10]
    st.info(f"📊 **Dados:** {start_date} a {end_date} ({len(df)} candles) • *+30 dias OOT para validação ML*")
    
    st.divider()
    
    # --- CONTROLES DE NAVEGAÇÃO ---
    nav_col1, nav_col2, nav_col3 = st.columns([4, 1, 1])
    
    with nav_col1:
        st.slider(
            "🕐 Navegue no Tempo",
            0, len(df) - 1,
            value=idx,
            key='chart_slider',
            on_change=update_slider
        )
    
    with nav_col2:
        st.number_input(
            "Índice",
            0, len(df) - 1,
            value=idx,
            key='chart_num',
            on_change=update_num
        )
        
    with nav_col3:
        zoom = st.select_slider(
            "Zoom",
            options=[50, 100, 200, 400, 800, len(df)],
            value=200,
            key='zoom_slider'
        )
    
    # --- GRÁFICO (HERO - Elemento Principal) ---
    fig = create_chart(df, st.session_state.trades, focus_idx=idx, zoom_level=zoom)
    
    # Adiciona Previsões do Modelo (se houver)
    if 'predictions' in st.session_state:
        preds = st.session_state.predictions
        buy_signals = preds[preds == 1]
        sell_signals = preds[preds == -1]
        
        if len(buy_signals) > 0:
            fig.add_trace(go.Scatter(
                x=buy_signals.index, y=df.loc[buy_signals.index]['low'] * 0.99,
                mode='markers', marker=dict(symbol='triangle-up', size=10, color='purple'),
                name='ML Buy'
            ), row=1, col=1)
        
        if len(sell_signals) > 0:
            fig.add_trace(go.Scatter(
                x=sell_signals.index, y=df.loc[sell_signals.index]['high'] * 1.01,
                mode='markers', marker=dict(symbol='triangle-down', size=10, color='purple'),
                name='ML Sell'
            ), row=1, col=1)

    # Adiciona linha vertical na posição selecionada
    fig.add_vline(x=df.index[idx], line_dash="dash", line_color="yellow")
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # --- CONTROLES DE COMPRA/VENDA (Abaixo do gráfico) ---
    trade_col1, trade_col2, trade_col3 = st.columns(3)
    
    with trade_col1:
        st.markdown("#### 🟢 Comprar")
        buy_mode = st.radio("Modo", ["Valor ($)", "% Saldo"], horizontal=True, key="buy_mode_radio", label_visibility="collapsed")
        
        if buy_mode == "Valor ($)":
            buy_value = st.number_input("Valor (US$)", min_value=0.0, max_value=float(st.session_state.balance), value=100.0, key='buy_val')
        else:
            buy_pct = st.slider("% do Saldo", 10, 100, 50, step=10, key='buy_pct')
            total_budget = st.session_state.balance * (buy_pct / 100)
            buy_value = total_budget / (1 + COMMISSION)
            st.caption(f"≈ ${buy_value:.0f}")

        if st.button("EXECUTAR COMPRA", type="primary", use_container_width=True):
            if buy_value > 0:
                amount_to_buy = buy_value / current_price 
                trade = register_trade('BUY', current_price, amount_to_buy, current_time, selected_coin)
                if trade:
                    st.success(f"✅ Compra: {amount_to_buy:.4f}")
                    st.rerun()
    
    with trade_col2:
        st.markdown("#### 🔴 Vender")
        sell_mode = st.radio("Modo", ["Qtd Moeda", "% Posição"], horizontal=True, key="sell_mode_radio", label_visibility="collapsed")
        
        if sell_mode == "Qtd Moeda":
            sell_amount = st.number_input("Quantidade", min_value=0.0, max_value=float(st.session_state.holdings), value=float(st.session_state.holdings), key='sell_qty')
        else:
            sell_pct = st.slider("% da Posição", 10, 100, 100, step=10, key='sell_pct')
            sell_amount = st.session_state.holdings * (sell_pct / 100)
            st.caption(f"≈ {sell_amount:.4f} moedas")
    
        if st.button("EXECUTAR VENDA", type="secondary", use_container_width=True):
            if sell_amount > 0:
                trade = register_trade('SELL', current_price, sell_amount, current_time, selected_coin)
                if trade:
                    st.success(f"✅ Venda: {sell_amount:.4f}")
                    st.rerun()
    
    with trade_col3:
        st.markdown("#### ℹ️ Status")
        if st.session_state.holdings > 0:
            avg_price = st.session_state.avg_price
            unrealized_pct = ((current_price - avg_price) / avg_price) * 100
            st.metric("Preço Médio", f"${avg_price:.4f}")
            st.metric("P&L Não Realizado", f"{unrealized_pct:+.2f}%")
        else:
            st.info("Sem posição aberta")
    
    st.divider()
    
    # --- TABELA DE TRADES (Integrada na tab Trading) ---
    st.subheader("📋 Histórico de Operações")
    
    if st.session_state.trades:
        trades_df = pd.DataFrame(st.session_state.trades)
        edit_df = trades_df[['action', 'price', 'amount', 'timestamp', 'reason']].copy()
        edit_df['timestamp'] = pd.to_datetime(edit_df['timestamp'])
        edit_df['total_value'] = edit_df['price'] * edit_df['amount']
        edit_df = edit_df[['action', 'price', 'amount', 'total_value', 'timestamp', 'reason']]
        
        edited_df = st.data_editor(
            edit_df,
            num_rows="dynamic",
            use_container_width=True,
            key="trade_editor",
            column_config={
                "action": st.column_config.SelectboxColumn("🎯 Ação", options=["BUY", "SELL"], required=True),
                "price": st.column_config.NumberColumn("💵 Preço Unit.", format="$%.2f"),
                "amount": st.column_config.NumberColumn("📦 Qtd. Moedas", format="%.4f"),
                "total_value": st.column_config.NumberColumn("💰 Valor Total", format="$%.2f", disabled=True),
                "timestamp": st.column_config.DatetimeColumn("📅 Data/Hora", format="YYYY-MM-DD HH:mm"),
                "reason": st.column_config.TextColumn("📝 Motivo/Label")
            },
            height=300
        )
        
        if st.button("🗑️ Limpar Tabela (Reset)", use_container_width=True):
            recalculate_portfolio([])
            st.rerun()
         
        # Reconstrói lista de trades a partir do editor
        updated_trades = []
        for _, row in edited_df.iterrows():
            trade = {
                "action": row['action'],
                "price": float(row['price']),
                "amount": float(row['amount']),
                "coin": "Fixed",
                "timestamp": row['timestamp'],
                "reason": row['reason'] if pd.notna(row['reason']) else ""
            }
            updated_trades.append(trade)
        
        def get_hash(obj): 
            return hashlib.md5(str(obj).encode()).hexdigest()
        
        if get_hash(updated_trades) != get_hash(st.session_state.trades):
            st.session_state.trades = updated_trades
            recalculate_portfolio(updated_trades)
            st.rerun()
            
    else:
        st.info("Nenhum trade registrado. Use os botões acima ou o Laboratório de Estratégias.")
