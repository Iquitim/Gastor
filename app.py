"""
Gastor - Trading Analysis & ML Platform
========================================

Main application entry point.
All UI components are modularized in src/ui/ and business logic in src/core/.
"""

import streamlit as st

# UI Components
from src.ui.sidebar import render_sidebar
from src.ui.tab_trading import render_trading_tab
from src.ui.tab_ml_studio import render_ml_studio_tab
from src.ui.tab_strategies import render_strategies_tab
from src.ui.tab_results import render_results_tab
from src.ui.tab_optimizer import render_optimizer_tab
from src.ui.tab_glossary import render_glossary_tab


# ===================== APP CONFIG =====================
st.set_page_config(
    page_title="Gastor | Trading ML",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ===================== SESSION STATE INIT =====================
def init_session_state():
    """Inicializa o session state com valores padrão."""
    defaults = {
        'df': None,
        'oot_df': None,
        'full_df': None,
        'trades': [],
        'balance': 10000.0,
        'initial_balance': 10000.0,
        'holdings': 0.0,
        'avg_price': 0.0,
        'selected_index': 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ===================== MAIN =====================
def main():
    """Função principal da aplicação."""
    
    # Inicializa estado
    init_session_state()
    
    # CSS Fix for Title Alignment
    st.markdown("""
        <style>
               .block-container {
                    padding-top: 1.8rem;
                    padding-bottom: 0rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
        </style>
        """, unsafe_allow_html=True)

    # Header
    st.title("Trading Analyzer")
    st.markdown("Marque trades manualmente para criar dataset de treinamento")
    
    # Sidebar
    selected_coin, days = render_sidebar()
    
    # Main content
    if st.session_state.df is not None:
        df = st.session_state.df
        
        # Callbacks para sincronização de navegação
        def update_slider():
            st.session_state.selected_index = st.session_state.chart_slider
            st.session_state.chart_num = st.session_state.chart_slider

        def update_num():
            st.session_state.selected_index = st.session_state.chart_num
            st.session_state.chart_slider = st.session_state.chart_num

        # Garante que o índice está dentro dos limites
        if st.session_state.selected_index >= len(df):
            st.session_state.selected_index = len(df) - 1
            
        idx = st.session_state.selected_index
        current_price = df['close'].iloc[idx]
        current_time = df.index[idx]
        
        # ===================== TABS PRINCIPAIS =====================
        tab_trading, tab_results, tab_ml, tab_strategies, tab_optimizer, tab_glossary = st.tabs([
            ":material/trending_up: Trading", 
            ":material/bar_chart: Resultados",
            ":material/psychology: ML Studio",
            ":material/science: Laboratório de Estratégias",
            ":material/experiment: Otimizador",
            ":material/menu_book: Glossário"
        ])
        
        # TAB 1: TRADING
        with tab_trading:
            render_trading_tab(df, idx, current_price, current_time, selected_coin, update_slider, update_num)
        
        # TAB 2: RESULTADOS
        with tab_results:
            render_results_tab(df)
        
        # TAB 3: ML STUDIO
        with tab_ml:
            render_ml_studio_tab(df)
        
        # TAB 4: LABORATÓRIO DE ESTRATÉGIAS
        with tab_strategies:
            render_strategies_tab(df)

        # TAB 5: OTIMIZADOR
        with tab_optimizer:
            render_optimizer_tab(df)
        
        # TAB 6: GLOSSÁRIO
        with tab_glossary:
            render_glossary_tab()
    
    else:
        st.info("Carregue dados de mercado na sidebar para começar.")


if __name__ == "__main__":
    main()
