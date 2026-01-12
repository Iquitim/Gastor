"""
Strategies Lab Tab UI component.
Contains strategy configuration, category selection, and strategy application.
"""

import streamlit as st

from src.core.portfolio import adjust_trade_amounts, recalculate_portfolio
from src.strategies import STRATEGIES


def render_strategies_tab(df):
    """Renderiza a tab do Laboratório de Estratégias."""
    
    # Usa o DF COMPLETO (sem corte OOT) para estratégias
    strategy_df = st.session_state.get('full_df', df)
    
    st.markdown("Use estratégias clássicas para gerar trades automaticamente e depois edite na tabela.")
    
    # Info sobre período usado
    strat_start = str(strategy_df.index[0])[:10]
    strat_end = str(strategy_df.index[-1])[:10]
    st.success(f"📊 **Período para estratégias:** {strat_start} a {strat_end} ({len(strategy_df)} candles) - *Sem corte OOT*")
    
    # Configuração global de position size
    st.info("⚙️ **Configuração de Investimento**")
    
    config_cols = st.columns([2, 1])
    
    with config_cols[0]:
        if 'strategy_position_size' not in st.session_state:
            st.session_state.strategy_position_size = 100
            
        position_size = st.slider(
            "💰 Tamanho da Posição (% do saldo por operação)",
            min_value=10,
            max_value=100,
            value=st.session_state.strategy_position_size,
            step=10,
            help="Quanto do seu saldo inicial usar em cada operação.",
            key="position_size_slider"
        )
        st.session_state.strategy_position_size = position_size
        
    with config_cols[1]:
        initial_bal = st.session_state.get('initial_balance', 10000.0)
        trade_value = initial_bal * position_size / 100
        st.metric("💵 Valor por Trade", f"${trade_value:,.0f}")
    
    force_close = st.checkbox(
        "📌 Forçar fechamento no fim do período",
        value=True,
        help="Se houver posição aberta no último candle, adiciona SELL automático",
        key="force_close_checkbox"
    )
    
    st.markdown("---")
    
    # Agrupa estratégias por categoria
    if STRATEGIES:
        CATEGORY_NAMES = {
            "trend": "📈 Tendência",
            "reversal": "🔄 Reversão",
            "momentum": "⚡ Momentum",
            "hybrid": "🔗 Híbridas",
            "breakout": "🚀 Breakout",
            "volume": "📊 Volume",
            "oscillator": "🎢 Osciladores",
            "volatility": "🌊 Volatilidade"
        }
        
        # Ordem fixa das categorias para consistência
        CATEGORY_ORDER = ["trend", "reversal", "momentum", "hybrid", "breakout", "volume", "oscillator", "volatility"]
        
        categories = {}
        for slug, cls in STRATEGIES.items():
            cat = cls.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((slug, cls))
        
        # Ordena categorias de forma consistente
        cat_list = [c for c in CATEGORY_ORDER if c in categories]
        cat_display = [CATEGORY_NAMES.get(c, c.title()) for c in cat_list]
        
        # Persiste seleção no session_state
        if 'selected_strategy_category' not in st.session_state:
            st.session_state.selected_strategy_category = 0
        
        # Garante que o índice está dentro dos limites
        current_idx = st.session_state.selected_strategy_category
        if current_idx >= len(cat_list):
            current_idx = 0
            st.session_state.selected_strategy_category = 0
        
        selected_cat_idx = st.selectbox(
            "🏷️ Categoria de Estratégias",
            range(len(cat_list)),
            index=current_idx,
            format_func=lambda x: f"{cat_display[x]} ({len(categories[cat_list[x]])} estratégias)",
            key="strategy_category_select"
        )
        
        # Atualiza session_state quando mudar
        if selected_cat_idx != st.session_state.selected_strategy_category:
            st.session_state.selected_strategy_category = selected_cat_idx
        
        selected_cat = cat_list[selected_cat_idx]
        
        cat_descriptions = {
            "trend": "Estratégias que seguem a direção do mercado.",
            "reversal": "Estratégias que buscam pontos de reversão.",
            "momentum": "Baseadas em força do movimento.",
            "hybrid": "Combinam múltiplos indicadores.",
            "breakout": "Detectam rompimentos de níveis.",
            "volume": "Analisam volume institucional.",
            "oscillator": "Detectam sobrecompra/sobrevenda."
        }
        st.caption(cat_descriptions.get(selected_cat, ""))
        
        strategy_list = categories[selected_cat]
        strat_tab_names = [f"{cls.icon} {cls.name}" for _, cls in strategy_list]
        strat_tabs = st.tabs(strat_tab_names)
        
        for strat_tab, (slug, strategy_class) in zip(strat_tabs, strategy_list):
            with strat_tab:
                strategy = strategy_class()
                
                st.markdown(strategy.explanation)
                st.info(f"💡 **Ideal para:** {strategy.ideal_for}")
                
                st.markdown("---")
                st.markdown("**⚙️ Parâmetros**")
                
                params = {}
                param_cols = st.columns(len(strategy.parameters)) if strategy.parameters else [st]
                
                for col, (param_name, param_config) in zip(param_cols, strategy.parameters.items()):
                    with col:
                        params[param_name] = st.slider(
                            param_config.get("label", param_name),
                            min_value=param_config.get("min", 0),
                            max_value=param_config.get("max", 100),
                            value=param_config.get("default", 50),
                            help=param_config.get("help", ""),
                            key=f"param_{slug}_{param_name}"
                        )
                
                if st.button(f"🚀 Aplicar {strategy.name}", use_container_width=True, key=f"btn_{slug}"):
                    raw_trades = strategy.apply(strategy_df, **params)
                    
                    initial_balance = st.session_state.get('initial_balance', 10000.0)
                    position_pct = st.session_state.get('strategy_position_size', 100)
                    
                    last_price = strategy_df['close'].iloc[-1]
                    last_timestamp = strategy_df.index[-1]
                    
                    adjusted_trades = adjust_trade_amounts(
                        raw_trades, 
                        initial_balance, 
                        position_pct,
                        force_close=force_close,
                        last_price=last_price,
                        last_timestamp=last_timestamp
                    )
                    
                    current = st.session_state.trades
                    combined = current + adjusted_trades
                    recalculate_portfolio(combined)
                    
                    st.success(f"✅ Adicionados {len(adjusted_trades)} trades de {strategy.name}!")
                    st.rerun()
    else:
        st.warning("Nenhuma estratégia disponível.")
    
    st.divider()
    
    # Mostra resumo de trades atual (referência)
    if st.session_state.trades:
        st.caption(f"📊 **Trades atuais:** {len(st.session_state.trades)} operações registradas")
    else:
        st.caption("Nenhum trade registrado ainda.")
