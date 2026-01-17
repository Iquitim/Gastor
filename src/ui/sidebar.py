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
        
        # Data source selector
        from src.core.data_fetchers import AVAILABLE_DATA_SOURCES
        
        source_options = list(AVAILABLE_DATA_SOURCES.keys())
        source_labels = [f"{AVAILABLE_DATA_SOURCES[k]['icon']} {AVAILABLE_DATA_SOURCES[k]['name']}" for k in source_options]
        
        if 'data_source' not in st.session_state:
            st.session_state.data_source = "auto"
        
        selected_source_idx = source_options.index(st.session_state.data_source) if st.session_state.data_source in source_options else 0
        
        selected_source = st.selectbox(
            "Fonte de Dados",
            options=source_options,
            format_func=lambda x: f"{AVAILABLE_DATA_SOURCES[x]['icon']} {AVAILABLE_DATA_SOURCES[x]['name']}",
            index=selected_source_idx,
            key='data_source_widget',
            help="Escolha a fonte de dados. 'Automático' tenta todas até uma funcionar."
        )
        st.session_state.data_source = selected_source
        
        # Show source description
        st.caption(f"ℹ️ {AVAILABLE_DATA_SOURCES[selected_source]['description']}")
        
        if st.button("Carregar Dados", type="primary"):
            # Reset flags before loading
            st.session_state.using_simulated_data = False
            st.session_state.data_source_used = None
            st.session_state.data_source_error = None
            
            with st.spinner(f"Carregando de {AVAILABLE_DATA_SOURCES[selected_source]['name']}..."):
                df = load_data(st.session_state.sb_coin_widget, days, selected_source)
                st.session_state.df = df
                st.session_state.selected_index = len(df) - 1
                
                # Show result
                source_used = st.session_state.get('data_source_used', 'unknown')
                error = st.session_state.get('data_source_error')
                
                if st.session_state.get('using_simulated_data', False):
                    st.warning(f"⚠️ Usando dados SIMULADOS! API indisponível.")
                    if error:
                        st.error(f"❌ {error}")
                elif source_used and source_used in AVAILABLE_DATA_SOURCES:
                    src_info = AVAILABLE_DATA_SOURCES[source_used]
                    st.success(f"✅ {len(df)} candles via {src_info['icon']} {src_info['name']}")
                else:
                    st.success(f"✅ {len(df)} candles carregados")
        
        # Show persistent warnings/info
        if st.session_state.get('using_simulated_data', False):
            st.error("🔴 DADOS SIMULADOS - Não são dados reais de mercado!")
        elif st.session_state.get('data_source_used'):
            source_used = st.session_state.data_source_used
            if source_used in AVAILABLE_DATA_SOURCES:
                src_info = AVAILABLE_DATA_SOURCES[source_used]
                st.info(f"📡 Fonte: {src_info['icon']} {src_info['name']}")
        
        st.divider()
        
        st.markdown("### Portfólio")
        current_price = 0
        if st.session_state.df is not None:
            # CORREÇÃO: Usa o último preço do período para cálculos de patrimônio
            # O slider é apenas para navegação visual, não afeta o resultado real
            current_price = st.session_state.df['close'].iloc[-1]
            
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
