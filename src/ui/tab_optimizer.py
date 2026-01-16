"""
Strategy Optimizer Tab UI component.
Performs grid search simulation on selected strategies.
"""

import streamlit as st
import pandas as pd
import numpy as np
import itertools
from src.strategies import STRATEGIES
from src.core.portfolio import adjust_trade_amounts, recalculate_portfolio, apply_risk_management
from src.core.config import get_total_fee
import copy

def run_optimizer(df, strategies_to_test, param_steps=3, optimize_execution=False):
    """
    Executa otimização (Grid Search) nas estratégias selecionadas.
    Permite otimizar também modo de execução (Reinvestir, Sizing).
    """
    results = []
    
    # Obtém moeda ativa e taxas
    active_coin = "SOL/USDT"
    if 'trades' in st.session_state and len(st.session_state.trades) > 0:
         active_coin = st.session_state.trades[0].get('coin', 'SOL/USDT')
    fee_rate = get_total_fee(active_coin)
    
    # Define Grid de Execução
    if optimize_execution:
        # Testa variações de execução
        execution_grid = [
            {'use_compound': False, 'sizing': 'fixo'},
            {'use_compound': True, 'sizing': 'fixo'},
            {'use_compound': True, 'sizing': 'volatilidade_atr'},
            {'use_compound': True, 'sizing': 'agressivo_rsi'} 
        ]
    else:
        # Usa configuração atual do usuário (Single Item Grid)
        current_compound = st.session_state.get('use_compound_checkbox', False)
        # Tenta pegar do session state do strategies tab. Fallback para 'fixo'
        current_sizing = st.session_state.get('strat_sizing_method', 'fixo')
        
        execution_grid = [
            {'use_compound': current_compound, 'sizing': current_sizing}
        ]
        
    position_pct = st.session_state.get('strategy_position_size', 100.0) / 100.0
    
    for slug in strategies_to_test:
        strategy_class = STRATEGIES.get(slug)
        if not strategy_class: continue
        strategy = strategy_class()
        
        # Grid de Parâmetros da Estratégia
        param_grid = {}
        for p_name, p_config in strategy.parameters.items():
            min_val = p_config.get('min', 0)
            max_val = p_config.get('max', 100)
            is_int = isinstance(p_config.get('default', 0), int)
            p_values = np.linspace(min_val, max_val, param_steps)
            if is_int: p_values = np.unique(p_values.astype(int))
            param_grid[p_name] = p_values
            
        keys = param_grid.keys()
        values = param_grid.values()
        combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
        
        # Limita simulações pesadas (Otimização Execução multiplica por 4x)
        limit = 100 if optimize_execution else 200
        if len(combinations) > limit:
            import random
            combinations = random.sample(combinations, limit)
            
        for params in combinations:
            # Roda Estratégia Base
            try:
                base_trades = strategy.apply(df, **params)
            except:
                continue
            if not base_trades: continue
            
            # Loop de Execução
            for exec_cfg in execution_grid:
                use_compound = exec_cfg['use_compound']
                sizing_method = exec_cfg['sizing']
                
                # Copy trades & Apply Risk Management (adds size_factor)
                trades_for_sim = copy.deepcopy(base_trades)
                trades_for_sim = apply_risk_management(trades_for_sim, df, sizing_method)
                
                # Usa saldo inicial do usuário
                initial_balance = st.session_state.get('initial_balance', 10000.0)
                position_pct_val = st.session_state.get('strategy_position_size', 100)
                last_price = df['close'].iloc[-1]
                last_ts = df.index[-1]
                
                # Usa adjust_trade_amounts para calcular amounts EXATAMENTE como na aplicação real
                try:
                    adjusted_trades = adjust_trade_amounts(
                        trades_for_sim,
                        initial_balance,
                        position_pct_val,
                        force_close=True,  # Igual ao comportamento real
                        last_price=last_price,
                        last_timestamp=last_ts,
                        use_compound=use_compound
                    )
                except:
                    continue
                
                if not adjusted_trades:
                    continue
                
                # Usa calculate_portfolio_evolution para calcular métricas EXATAMENTE como na tab Results
                from src.ui.tab_results import calculate_portfolio_evolution, calculate_metrics, calculate_drawdown
                
                evolution_df = calculate_portfolio_evolution(adjusted_trades, df, initial_balance)
                
                if evolution_df.empty:
                    continue
                
                # Calcula métricas usando as mesmas funções que a aba Resultados
                metrics = calculate_metrics(adjusted_trades, evolution_df, initial_balance)
                dd_metrics = calculate_drawdown(evolution_df)
                
                # Extrai valores para display
                total_pnl_pct = metrics.get('total_pnl_pct', 0)
                win_rate = metrics.get('win_rate', 0)
                completed_trades = metrics.get('completed_trades', 0)
                max_dd = dd_metrics.get('max_drawdown_pct', 0)
                
                param_str = ", ".join([f"{k}={v}" for k,v in params.items()])
                
                # Traduz sizing method para display
                sizing_map = {'fixo': 'Fixo', 'conservador': 'Conserv.', 'volatilidade_atr': 'Volat.', 'agressivo_rsi': 'RSI'}
                sizing_disp = sizing_map.get(sizing_method, sizing_method)
                exec_str = f"{'Juros Comp.' if use_compound else 'Fixo'} + {sizing_disp}"
                
                results.append({
                    "Slug": slug,
                    "Estratégia": strategy.name,
                    "Params": param_str,
                    "Execução": exec_str,
                    "Total PnL %": round(total_pnl_pct, 2),
                    "Max DD %": round(max_dd, 2),
                    "Trades": completed_trades,
                    "Win Rate %": round(win_rate, 1),
                    "Result Raw": params,
                    "Exec Raw": exec_cfg 
                })
            
    return pd.DataFrame(results)

def apply_strategy_callback(slug, params, exec_cfg, df):
    """Callback para aplicar a estratégia sem conflito de state."""
    # 1. Atualiza Settings Globais (Isso é seguro dentro de callback)
    st.session_state.use_compound_checkbox = exec_cfg['use_compound']
    st.session_state.strat_sizing_method = exec_cfg['sizing'] 
    
    # 2. Executa Lógica
    strategy_cls = STRATEGIES.get(slug)
    if strategy_cls:
        strategy = strategy_cls()
        raw_trades = strategy.apply(df, **params)
        
        # Aplica Sizing
        sizing_method = exec_cfg['sizing']
        raw_trades = apply_risk_management(raw_trades, df, sizing_method)
        
        # Aplica Portfolio Engine
        updated_compound = exec_cfg['use_compound']
        final_bal = st.session_state.get('initial_balance', 10000.0)
        pos_pct = st.session_state.get('strategy_position_size', 100)
        
        last_price = df['close'].iloc[-1]
        last_ts = df.index[-1]
        
        if 'force_close_checkbox' not in st.session_state: st.session_state.force_close_checkbox = True
        force_c = st.session_state.force_close_checkbox
        
        adj_trades = adjust_trade_amounts(
            raw_trades, final_bal, pos_pct, force_c, last_price, last_ts, updated_compound
        )
        
        recalculate_portfolio(adj_trades)
        
        # Feedback (será visto no próximo rerun)
        st.session_state['toast_msg'] = f"Estratégia {strategy.name} aplicada com sucesso!"

def render_optimizer_tab(df):
    """Renderiza a tab do Otimizador."""
    
    # Garante uso do DF completo (sem OOT) para otimização, igual ao Lab de Estratégias
    df = st.session_state.get('full_df', df)
    
    # Check toast
    if 'toast_msg' in st.session_state:
        st.toast(st.session_state['toast_msg'])
        del st.session_state['toast_msg']

    st.markdown("### :material/experiment: Otimizador de Estratégias")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.container(border=True):
            st.markdown("##### ⚙️ Configuração")
            
            all_slugs = list(STRATEGIES.keys())
            # Pre-seleção
            default_sel = list(STRATEGIES.keys())[:2] if len(STRATEGIES) >= 2 else list(STRATEGIES.keys())
            
            selected_slugs_options = st.multiselect(
                "Estratégias",
                options=all_slugs,
                format_func=lambda x: STRATEGIES[x].name if x in STRATEGIES else x,
                default=default_sel
            )
            
            steps = st.slider("Grid Steps (min-max)", 2, 5, 3, help="Quantos valores testar por parâmetro.")
            
            optimize_exec = st.checkbox(
                "Otimizar Execução (Reinvestir/Sizing)", 
                value=False,
                help="Se marcado, testa combinções de Juros Compostos e Sizing Dinâmico (ATR/RSI) para cada estratégia."
            )
            
            if st.button("Iniciar Otimização 🚀", type="primary", use_container_width=True):
                if not selected_slugs_options:
                    st.error("Selecione uma estratégia.")
                else:
                    with st.spinner("Otimizando... pode demorar se 'Otimizar Execução' estiver marcado..."):
                        results_df = run_optimizer(df, selected_slugs_options, steps, optimize_exec)
                        st.session_state.opt_results = results_df
                        st.success("Concluído!")

    with col2:
        if 'opt_results' in st.session_state and isinstance(st.session_state.opt_results, pd.DataFrame) and not st.session_state.opt_results.empty:
            res = st.session_state.opt_results
            
            st.markdown("#### 🏆 Top Resultados")
            sort_metric = st.selectbox("Ordenar por", ["Total PnL %", "Win Rate %", "Max DD %"], index=0, label_visibility="collapsed")
            ascending = True if sort_metric == "Max DD %" else False
            
            res_sorted = res.sort_values(by=sort_metric, ascending=ascending).reset_index(drop=True)
            
            best = res_sorted.iloc[0]
            
            # --- DASHBOARD RESUMO ---
            st.markdown(f"### 🌟 Campeã: {best['Estratégia']}")
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Lucro Total", f"{best['Total PnL %']}%", border=True)
            m2.metric("Win Rate", f"{best['Win Rate %']}%", border=True)
            m3.metric("Max Drawdown", f"{best['Max DD %']}%", delta_color="inverse", border=True)
            m4.metric("Total Trades", f"{best['Trades']}", border=True)
            
            # Detalhes
            with st.expander("📝 Detalhes da Configuração Campeã", expanded=True):
                st.markdown(f"**Parâmetros:** `{best['Params']}`")
                st.markdown(f"**Modo de Execução:** `{best['Execução']}`")
                if 'Exec Raw' in best:
                     exec_info = best['Exec Raw']
                     st.caption(f"Settings Reais: Reinvest={exec_info['use_compound']}, Sizing={exec_info['sizing']}")
            
            # Tabela Geral Simplificada
            st.markdown("##### Outros Resultados")
            st.dataframe(
                res_sorted[["Estratégia", "Total PnL %", "Execução", "Win Rate %", "Max DD %", "Trades", "Params"]],
                use_container_width=True,
                height=250,
                column_config={
                    "Total PnL %": st.column_config.NumberColumn(format="%.2f%%"),
                    "Max DD %": st.column_config.ProgressColumn(format="%.2f%%", min_value=0.0, max_value=max(0.5, res_sorted["Max DD %"].max() / 100)),
                }
            )
            
            st.divider()
            
            st.button(
                "Aplicar Campeã no Gráfico 📉", 
                type="primary", 
                use_container_width=True,
                on_click=apply_strategy_callback,
                args=(best['Slug'], best['Result Raw'], best['Exec Raw'], df)
            )

        else:
            st.info("Execute a otimização para ver os resultados.")
