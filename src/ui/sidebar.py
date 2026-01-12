"""
Sidebar UI component for the trading application.
"""

import os
import json
import streamlit as st

from src.core.data_loader import load_data, COINS, COMMISSION


def save_trades() -> str:
    """Salva trades em arquivo JSON."""
    filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'trades.json')
    with open(filepath, 'w') as f:
        trades_to_save = st.session_state.trades.copy()
        for t in trades_to_save:
            if 'timestamp' in t:
                t['timestamp'] = str(t['timestamp'])
        json.dump(trades_to_save, f, indent=2)
    return filepath


def render_sidebar():
    """Renderiza a sidebar completa."""
    
    with st.sidebar:
        # --- BRANDING ---
        # --- BRANDING ---
        # Carrega imagem dinamicamente
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'image', 'gastor.png')
        img_base64 = ""
        if os.path.exists(logo_path):
            import base64
            with open(logo_path, "rb") as image_file:
                img_base64 = base64.b64encode(image_file.read()).decode()
        
        logo_html = f'<img src="data:image/png;base64,{img_base64}" style="width: 100%; height: 100%; object-fit: contain;">' if img_base64 else ""

        st.markdown(f"""
        <div style="text-align: left; padding: 10px 0; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="width: 80px; height: 80px; display: flex; align-items: center; justify-content: center;">
                    {logo_html}
                </div>
                <div style="height: 75px; display: flex; flex-direction: column; justify-content: center;">
                     <h1 style="margin: 0; padding: 0; line-height: 1.2; font-size: 28px; font-weight: 800; background: linear-gradient(90deg, #f8fafc, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.5px;">Gastor</h1>
                     <p style="margin: 0; padding: 0; line-height: 1.0; font-size: 11px; color: #64748b; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;">Trading Analyzer Studio</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Settings") # Clean header
        
        # Configuração de Saldo Inicial
        if 'initial_balance' not in st.session_state:
            st.session_state.initial_balance = 10000.0

        def reset_account():
            """Reseta a conta com o novo saldo inicial."""
            new_bal = st.session_state.input_initial_balance
            st.session_state.initial_balance = new_bal
            st.session_state.balance = new_bal
            st.session_state.holdings = 0.0
            st.session_state.avg_price = 0.0
            st.session_state.trades = []

        st.number_input(
            "Saldo Inicial ($)", 
            value=st.session_state.initial_balance, 
            step=1000.0, 
            key='input_initial_balance',
            on_change=reset_account
        )
        
        if st.button("Resetar Conta"):
            reset_account()
            st.rerun()

        st.divider()
        
        st.markdown("### Dados de Mercado")
        
        if 'sb_coin' not in st.session_state:
            st.session_state.sb_coin = COINS[0]
            
        def update_coin():
            st.session_state.sb_coin = st.session_state.sb_coin_widget
            
        if 'sb_coin_widget' not in st.session_state:
            st.session_state.sb_coin_widget = st.session_state.sb_coin
            
        selected_coin = st.selectbox(
            "Moeda", 
            COINS, 
            index=COINS.index(st.session_state.sb_coin) if st.session_state.sb_coin in COINS else 0, 
            key='sb_coin_widget', 
            on_change=update_coin
        )
        days = st.slider("Dias de histórico", 30, 180, 90)
        
        if st.button("Carregar Dados", type="primary"):
            with st.spinner("Carregando..."):
                df = load_data(st.session_state.sb_coin_widget, days)
                st.session_state.df = df
                st.session_state.selected_index = len(df) - 1
                st.success(f"✅ {len(df)} candles carregados")
        
        st.divider()
        
        st.markdown("### Portfólio")
        current_price = 0
        if st.session_state.df is not None:
            idx = st.session_state.get('selected_index', 0)
            current_price = st.session_state.df['close'].iloc[idx]
            
        portfolio_value = st.session_state.balance + (st.session_state.holdings * current_price)
        pnl_total = ((portfolio_value - st.session_state.initial_balance) / st.session_state.initial_balance) * 100
        
        if abs(pnl_total) < 0.001:
            delta_val = None
        else:
            delta_val = f"{pnl_total:+.2f}%"
            
        st.metric("Saldo Disponível", f"${st.session_state.balance:,.2f}")
        st.metric("Posição (Moedas)", f"{st.session_state.holdings:.4f} {selected_coin.split('/')[0]}")
        st.metric("Valor Total", f"${portfolio_value:,.2f}", delta=delta_val)
        
        st.divider()

        if st.button("Salvar Trades", icon=":material/save:"):
            filepath = save_trades()
            st.success(f"Salvo em {filepath}")

        if st.button("Carregar Trades Salvos", icon=":material/file_upload:"):
            _load_trades_from_file(selected_coin)
    
    return selected_coin, days


def _load_trades_from_file(selected_coin: str):
    """Carrega trades de arquivo JSON."""
    filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'trades.json')
    
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                loaded_trades = json.load(f)
            
            if loaded_trades:
                st.session_state.trades = loaded_trades
                
                trade_coin = loaded_trades[0].get('coin', COINS[0])
                
                if st.session_state.sb_coin != trade_coin:
                    st.session_state.sb_coin = trade_coin
                    st.session_state.sb_coin_widget = trade_coin
                    st.toast(f"Trocando moeda para {trade_coin}...")
                    st.rerun()
                    
                if st.session_state.df is None:
                    with st.spinner(f"Carregando histórico de {trade_coin}..."):
                        try:
                            df = load_data(trade_coin, 90)
                            st.session_state.df = df
                            st.session_state.selected_index = len(df) - 1
                            st.success(f"Dados carregados!")
                        except Exception as e:
                            st.error(f"Erro ao baixar dados: {e}")
                            st.stop()

                # Recalcula Portfólio
                st.session_state.balance = st.session_state.initial_balance
                st.session_state.holdings = 0.0
                st.session_state.avg_price = 0.0
                
                for t in loaded_trades:
                    amt = float(t['amount'])
                    prc = float(t['price'])
                    if t['action'] == 'BUY':
                        cost = amt * prc
                        fee = cost * COMMISSION
                        st.session_state.balance -= (cost + fee)
                        
                        current_val = st.session_state.holdings * st.session_state.avg_price
                        new_val = amt * prc
                        if (st.session_state.holdings + amt) > 0:
                            st.session_state.avg_price = (current_val + new_val) / (st.session_state.holdings + amt)
                        st.session_state.holdings += amt
                        
                    elif t['action'] == 'SELL':
                        rev = amt * prc
                        fee = rev * COMMISSION
                        st.session_state.balance += (rev - fee)
                        st.session_state.holdings -= amt
                
                st.toast("Trades carregados e portfólio atualizado!")
                st.rerun()
            else:
                st.warning("Arquivo de trades está vazio.")
        except Exception as e:
            st.error(f"Erro ao carregar: {e}")
    else:
        st.error("Nenhum arquivo 'trades.json' encontrado.")
