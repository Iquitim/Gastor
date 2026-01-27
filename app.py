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
from src.ui.tab_builder import render_builder_tab
from src.ui.tab_config import render_config_tab


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
        tab_trading, tab_results, tab_ml, tab_strategies, tab_optimizer, tab_builder, tab_glossary, tab_config = st.tabs([
            ":material/trending_up: Trading", 
            ":material/bar_chart: Resultados",
            ":material/psychology: ML Studio",
            ":material/science: Laboratório de Estratégias",
            ":material/experiment: Otimizador",
            ":material/build: Construtor",
            ":material/menu_book: Glossário",
            ":material/settings: Configurações"
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
        
        # TAB 6: CONSTRUTOR
        with tab_builder:
            render_builder_tab(df)
        
        # TAB 7: GLOSSÁRIO
        with tab_glossary:
            render_glossary_tab()
        
        # TAB 8: CONFIGURAÇÕES
        with tab_config:
            render_config_tab()
    
    else:
        # ========================================
        # PÁGINA DE BOAS-VINDAS - Design Profissional
        # ========================================
        
        # Hero section minimalista
        st.markdown("""
        <div style="text-align: center; padding: 40px 0 20px 0;">
            <h2 style="color: #ffffff; margin-bottom: 12px; font-weight: 500;">Bem-vindo ao Gastor</h2>
            <p style="color: #9ca3af; font-size: 16px; letter-spacing: 1px;">
                Plataforma de análise de trading com <span style="color: #10b981;">Machine Learning Human-in-the-Loop</span>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Call to action
        st.markdown("""
        <div style="
            background: linear-gradient(90deg, #065f46, #047857);
            padding: 16px 24px;
            border-radius: 8px;
            margin: 20px 0;
        ">
            <p style="margin: 0; color: white; font-size: 15px;">
                <strong>Para começar:</strong> Configure sua moeda e período na barra lateral e clique em <strong>Carregar Dados</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Features em 3 colunas - Design minimalista
        st.markdown("#### Funcionalidades")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="border-left: 3px solid #10b981; padding-left: 16px;">
                <h5 style="color: #f1f5f9; margin: 0 0 8px 0;">Trading Analyzer</h5>
                <p style="color: #94a3b8; font-size: 14px; margin: 0;">
                    Marque trades no gráfico interativo para criar seu dataset de treinamento.
                </p>
                <ul style="color: #64748b; font-size: 13px; margin-top: 12px; padding-left: 16px;">
                    <li>Marcação visual BUY/SELL</li>
                    <li>Candlesticks interativo</li>
                    <li>Indicadores técnicos</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="border-left: 3px solid #3b82f6; padding-left: 16px;">
                <h5 style="color: #f1f5f9; margin: 0 0 8px 0;">Machine Learning</h5>
                <p style="color: #94a3b8; font-size: 14px; margin: 0;">
                    O sistema aprende seus padrões de trading e prevê sinais futuros.
                </p>
                <ul style="color: #64748b; font-size: 13px; margin-top: 12px; padding-left: 16px;">
                    <li>Validação Out-of-Time</li>
                    <li>XGBoost, LightGBM</li>
                    <li>Feature importance</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="border-left: 3px solid #8b5cf6; padding-left: 16px;">
                <h5 style="color: #f1f5f9; margin: 0 0 8px 0;">Laboratório</h5>
                <p style="color: #94a3b8; font-size: 14px; margin: 0;">
                    Teste estratégias pré-definidas ou construa as suas próprias.
                </p>
                <ul style="color: #64748b; font-size: 13px; margin-top: 12px; padding-left: 16px;">
                    <li>Estratégias clássicas</li>
                    <li>Construtor de regras</li>
                    <li>Backtest automático</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Guia rápido - Design minimalista
        st.markdown("#### Guia Rápido")
        
        cols = st.columns(4)
        steps = [
            ("01", "Configurar", "Escolha moeda e período na sidebar"),
            ("02", "Carregar", "Busque os dados de mercado"),
            ("03", "Explorar", "Use as abas para análise e ML"),
            ("04", "Iterar", "Refine suas estratégias")
        ]
        
        for i, (num, title, desc) in enumerate(steps):
            with cols[i]:
                st.markdown(f"""
                <div style="
                    background: #0f172a;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid #1e293b;
                    min-height: 100px;
                ">
                    <span style="color: #10b981; font-size: 24px; font-weight: 300;">{num}</span>
                    <h5 style="color: #f1f5f9; margin: 8px 0 4px 0; font-size: 14px;">{title}</h5>
                    <p style="color: #64748b; font-size: 12px; margin: 0;">{desc}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Abas disponíveis - Design limpo
        with st.expander("Abas Disponíveis", expanded=False):
            st.markdown("""
            | Aba | Descrição |
            |-----|-----------|
            | Trading | Gráfico interativo para marcar trades |
            | Resultados | Análise de performance e métricas |
            | ML Studio | Treinamento de modelos |
            | Laboratório | Estratégias pré-definidas |
            | Otimizador | Otimização de parâmetros |
            | Construtor | Crie suas próprias estratégias |
            | Glossário | Dicionário de indicadores |
            | Configurações | Taxas de trading por moeda |
            """)
        
        # Footer minimalista
        st.markdown("""
        <div style="text-align: center; color: #475569; font-size: 12px; margin-top: 40px;">
            <p>Use a validação Out-of-Time (OOT) para testar em dados nunca vistos</p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
