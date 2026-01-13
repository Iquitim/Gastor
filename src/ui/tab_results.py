"""
Results Dashboard Tab UI component.
Shows comprehensive trading performance metrics and visualizations.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st

from src.core.config import get_total_fee


def calculate_portfolio_evolution(trades: list, df: pd.DataFrame, initial_balance: float) -> pd.DataFrame:
    """
    Calcula a evolução do patrimônio ao longo do tempo.
    
    Returns:
        DataFrame com colunas: timestamp, balance, holdings_value, total_value, pnl_pct
    """
    if not trades:
        return pd.DataFrame()
    
    # Ordena trades por timestamp
    sorted_trades = sorted(trades, key=lambda x: x['timestamp'])
    
    # Cria série temporal do patrimônio
    evolution = []
    balance = initial_balance
    holdings = 0.0
    
    # Usa moeda do session_state para taxa consistente com sidebar
    coin = st.session_state.get('sb_coin', 'SOL/USDT')
    fee_rate = get_total_fee(coin)
    
    # Adiciona ponto inicial
    first_ts = sorted_trades[0]['timestamp']
    evolution.append({
        'timestamp': first_ts,
        'balance': initial_balance,
        'holdings': 0,
        'holdings_value': 0,
        'total_value': initial_balance,
        'pnl_pct': 0,
        'event': 'START'
    })
    
    # Processa cada trade
    for trade in sorted_trades:
        action = trade.get('action', '').upper()
        price = float(trade.get('price', 0))
        amount = float(trade.get('amount', 0))
        timestamp = trade['timestamp']
        
        if action == 'BUY':
            cost = amount * price
            fee = cost * fee_rate
            balance -= (cost + fee)
            holdings += amount
            
        elif action == 'SELL':
            revenue = amount * price
            fee = revenue * fee_rate
            balance += (revenue - fee)
            holdings -= amount
        
        holdings_value = holdings * price
        total_value = balance + holdings_value
        pnl_pct = ((total_value - initial_balance) / initial_balance) * 100
        
        evolution.append({
            'timestamp': timestamp,
            'balance': balance,
            'holdings': holdings,
            'holdings_value': holdings_value,
            'total_value': total_value,
            'pnl_pct': pnl_pct,
            'event': action
        })
    
    return pd.DataFrame(evolution)


def calculate_drawdown(evolution_df: pd.DataFrame) -> dict:
    """
    Calcula métricas de drawdown e max daily loss.
    
    Returns:
        Dict com max_drawdown_pct, max_drawdown_date, current_drawdown, max_daily_loss
    """
    if evolution_df.empty:
        return {
            'max_drawdown_pct': 0, 
            'max_drawdown_date': None, 
            'current_drawdown_pct': 0,
            'max_daily_loss_pct': 0,
            'max_daily_loss_date': None
        }
    
    values = evolution_df['total_value'].values
    timestamps = evolution_df['timestamp'].values
    
    # Calcula drawdown
    peak = values[0]
    max_dd = 0
    max_dd_idx = 0
    
    drawdowns = []
    for i, val in enumerate(values):
        if val > peak:
            peak = val
        dd = (peak - val) / peak * 100
        drawdowns.append(dd)
        if dd > max_dd:
            max_dd = dd
            max_dd_idx = i
    
    evolution_df['drawdown_pct'] = drawdowns
    
    # Calcula Max Daily Loss (perda máxima em um único dia)
    max_daily_loss = 0
    max_daily_loss_date = None
    
    # Agrupa por dia
    daily_values = {}
    for i, ts in enumerate(timestamps):
        day = str(ts)[:10]  # Pega apenas a data YYYY-MM-DD
        if day not in daily_values:
            daily_values[day] = {'start': values[i], 'end': values[i], 'min': values[i]}
        daily_values[day]['end'] = values[i]
        daily_values[day]['min'] = min(daily_values[day]['min'], values[i])
    
    # Calcula perda de cada dia (do início do dia até o mínimo do dia)
    initial_balance = values[0]
    for day, data in daily_values.items():
        daily_loss = (data['start'] - data['min']) / initial_balance * 100
        if daily_loss > max_daily_loss:
            max_daily_loss = daily_loss
            max_daily_loss_date = day
    
    return {
        'max_drawdown_pct': max_dd,
        'max_drawdown_date': evolution_df.iloc[max_dd_idx]['timestamp'] if max_dd_idx < len(evolution_df) else None,
        'current_drawdown_pct': drawdowns[-1] if drawdowns else 0,
        'drawdown_series': drawdowns,
        'max_daily_loss_pct': max_daily_loss,
        'max_daily_loss_date': max_daily_loss_date
    }


def calculate_metrics(trades: list, evolution_df: pd.DataFrame, initial_balance: float) -> dict:
    """Calcula todas as métricas de performance."""
    
    if not trades or evolution_df.empty:
        return {
            'total_trades': 0,
            'buy_trades': 0,
            'sell_trades': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'avg_trade_pnl': 0,
            'best_trade': 0,
            'worst_trade': 0,
            'final_value': initial_balance,
            'total_pnl': 0,
            'total_pnl_pct': 0,
        }
    
    # Contagem de trades
    buys = [t for t in trades if t.get('action', '').upper() == 'BUY']
    sells = [t for t in trades if t.get('action', '').upper() == 'SELL']
    
    # Calcula P&L por trade (simplificado)
    trade_pnls = []
    for i in range(min(len(buys), len(sells))):
        buy_price = float(buys[i].get('price', 0))
        sell_price = float(sells[i].get('price', 0))
        amount = float(buys[i].get('amount', 0))
        pnl = (sell_price - buy_price) * amount
        trade_pnls.append(pnl)
    
    wins = [p for p in trade_pnls if p > 0]
    losses = [p for p in trade_pnls if p < 0]
    
    final_value = evolution_df.iloc[-1]['total_value'] if not evolution_df.empty else initial_balance
    total_pnl = final_value - initial_balance
    
    return {
        'total_trades': len(trades),
        'buy_trades': len(buys),
        'sell_trades': len(sells),
        'completed_trades': min(len(buys), len(sells)),
        'win_rate': (len(wins) / len(trade_pnls) * 100) if trade_pnls else 0,
        'profit_factor': (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else 0,
        'avg_trade_pnl': np.mean(trade_pnls) if trade_pnls else 0,
        'best_trade': max(trade_pnls) if trade_pnls else 0,
        'worst_trade': min(trade_pnls) if trade_pnls else 0,
        'final_value': final_value,
        'total_pnl': total_pnl,
        'total_pnl_pct': (total_pnl / initial_balance * 100) if initial_balance > 0 else 0,
    }


def render_results_tab(df):
    """Renderiza a tab de Resultados."""
    
    st.markdown("### :material/analytics: Dashboard de Performance")
    
    trades = st.session_state.get('trades', [])
    initial_balance = st.session_state.get('initial_balance', 10000.0)
    
    if not trades:
        st.info("Nenhum trade registrado. Execute estratégias ou marque trades manualmente para ver os resultados.")
        return
    
    # Calcula evolução do patrimônio (para gráfico)
    evolution_df = calculate_portfolio_evolution(trades, df, initial_balance)
    
    # Calcula drawdown
    dd_metrics = calculate_drawdown(evolution_df)
    
    # ==== CÁLCULO CORRETO DO PATRIMÔNIO FINAL ====
    # Usa o ÚLTIMO preço do período (não o slider de navegação)
    current_balance = st.session_state.get('balance', initial_balance)
    current_holdings = st.session_state.get('holdings', 0.0)
    
    # CORREÇÃO: Usa o último preço do DataFrame, não o do slider
    # O slider é para navegação visual, não para cálculo de resultados
    last_price = df['close'].iloc[-1] if len(df) > 0 else 0
    
    # Patrimônio Final = Saldo + (Holdings * Último Preço do Período)
    final_value = current_balance + (current_holdings * last_price)
    total_pnl = final_value - initial_balance
    total_pnl_pct = (total_pnl / initial_balance * 100) if initial_balance > 0 else 0
    
    # Calcula métricas de trades (para estatísticas)
    metrics = calculate_metrics(trades, evolution_df, initial_balance)
    # Sobrescreve com valores reais calculados
    metrics['final_value'] = final_value
    metrics['total_pnl'] = total_pnl
    metrics['total_pnl_pct'] = total_pnl_pct
    
    # ==================== BIG NUMBERS ====================
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Patrimônio: positivo = verde/seta cima, negativo = vermelho/seta baixo
        st.metric(
            ":material/attach_money: Patrimônio Final",
            f"${metrics['final_value']:,.2f}",
            delta=f"{metrics['total_pnl_pct']:+.2f}%"
            # delta_color padrão: positivo=verde, negativo=vermelho
        )
    
    with col2:
        # Lucro: positivo = verde, negativo = vermelho
        st.metric(
            ":material/trending_up: Lucro/Prejuízo",
            f"${metrics['total_pnl']:+,.2f}",
            delta=f"{metrics['total_pnl']:+,.2f}"
        )
    
    with col3:
        st.metric(
            ":material/check_circle: Taxa de Acerto",
            f"{metrics['win_rate']:.1f}%",
            delta=f"{metrics['completed_trades']} trades completos",
            delta_color="off"  # Neutro
        )
    
    with col4:
        # Max Drawdown: sempre negativo, sem delta
        st.metric(
            ":material/trending_down: Max Drawdown",
            f"-{dd_metrics['max_drawdown_pct']:.2f}%",
            delta=str(dd_metrics['max_drawdown_date'])[:10] if dd_metrics['max_drawdown_date'] else "N/A",
            delta_color="off"  # Neutro (é só data)
        )
    
    # Segunda linha de métricas
    st.markdown("---")
    
    col5, col6, col7, col8, col9 = st.columns(5)
    
    with col5:
        st.metric(":material/paid: Valor Investido", f"${initial_balance:,.2f}")
    
    with col6:
        st.metric(":material/swap_horiz: Total de Operações", f"{metrics['total_trades']}")
    
    with col7:
        pf_display = f"{metrics['profit_factor']:.2f}" if metrics['profit_factor'] > 0 else "N/A"
        st.metric(":material/account_balance: Profit Factor", pf_display)
    
    with col8:
        # Drawdown atual: mostrar como negativo para ficar vermelho
        dd_value = -dd_metrics['current_drawdown_pct']  # Negativo para mostrar vermelho
        st.metric(
            ":material/waterfall_chart: Drawdown Atual", 
            f"-{dd_metrics['current_drawdown_pct']:.2f}%",
            delta=f"{dd_value:.2f}%"  # Negativo = vermelho com seta para baixo
        )
    
    with col9:
        # Max Daily Loss
        daily_loss_value = -dd_metrics['max_daily_loss_pct']
        st.metric(
            ":material/calendar_today: Max Loss Diária",
            f"-{dd_metrics['max_daily_loss_pct']:.2f}%",
            delta=dd_metrics['max_daily_loss_date'] if dd_metrics['max_daily_loss_date'] else "N/A",
            delta_color="off"
        )
    
    # ==================== GRÁFICOS ====================
    st.markdown("---")
    st.markdown("### :material/show_chart: Evolução do Patrimônio")
    
    if not evolution_df.empty:
        # Gráfico de evolução
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3],
            subplot_titles=('Patrimônio Total', 'Drawdown (%)')
        )
        
        # Patrimônio
        fig.add_trace(
            go.Scatter(
                x=evolution_df['timestamp'],
                y=evolution_df['total_value'],
                mode='lines+markers',
                name='Patrimônio',
                line=dict(color='#00d4aa', width=2),
                marker=dict(size=4),
                fill='tozeroy',
                fillcolor='rgba(0, 212, 170, 0.1)'
            ),
            row=1, col=1
        )
        
        # Linha de referência (investimento inicial)
        fig.add_hline(
            y=initial_balance,
            line_dash="dash",
            line_color="yellow",
            annotation_text=f"Investido: ${initial_balance:,.0f}",
            row=1, col=1
        )
        
        # Drawdown
        if 'drawdown_pct' in evolution_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=evolution_df['timestamp'],
                    y=[-d for d in evolution_df['drawdown_pct']],
                    mode='lines',
                    name='Drawdown',
                    line=dict(color='#ff6b6b', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(255, 107, 107, 0.3)'
                ),
                row=2, col=1
            )
        
        fig.update_layout(
            height=500,
            showlegend=True,
            template='plotly_dark'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ==================== DETALHES DOS TRADES ====================
    st.markdown("---")
    st.markdown("### :material/list: Detalhes das Operações")
    
    detail_cols = st.columns(2)
    
    with detail_cols[0]:
        st.markdown("**:material/thumb_up: Melhores Trades**")
        if metrics['best_trade'] > 0:
            st.success(f"Melhor: +${metrics['best_trade']:,.2f}")
        else:
            st.info("Nenhum trade lucrativo ainda")
        
        st.markdown("**:material/functions: Média por Trade**")
        avg_color = "success" if metrics['avg_trade_pnl'] >= 0 else "error"
        if metrics['avg_trade_pnl'] >= 0:
            st.success(f"${metrics['avg_trade_pnl']:+,.2f}")
        else:
            st.error(f"${metrics['avg_trade_pnl']:+,.2f}")
    
    with detail_cols[1]:
        st.markdown("**:material/thumb_down: Piores Trades**")
        if metrics['worst_trade'] < 0:
            st.error(f"Pior: ${metrics['worst_trade']:,.2f}")
        else:
            st.info("Nenhuma perda registrada")
        
        st.markdown("**:material/compare_arrows: Compras vs Vendas**")
        st.info(f":material/shopping_cart: {metrics['buy_trades']} compras | :material/sell: {metrics['sell_trades']} vendas")
    
    # ==================== COMPARATIVO FTMO ====================
    st.markdown("---")
    st.markdown("### :material/emoji_events: Comparativo com FTMO Challenge")
    st.caption("Compare sua performance com os requisitos do FTMO Challenge para contas de $10k-$200k")
    
    # Regras do FTMO Challenge
    FTMO_RULES = {
        'profit_target': 10.0,        # Meta de lucro: 10%
        'max_drawdown': 10.0,         # Max Drawdown: 10%
        'max_daily_loss': 5.0,        # Max Loss Diária: 5%
        'min_trading_days': 4,        # Mínimo 4 dias de trading
        'verification_target': 5.0,   # Meta da verificação: 5%
    }
    
    # Calcula métricas do usuário para comparação
    user_profit_pct = metrics['total_pnl_pct']
    user_max_dd = dd_metrics['max_drawdown_pct']
    user_max_daily_loss = dd_metrics['max_daily_loss_pct']
    
    # Calcula dias de trading únicos
    if not evolution_df.empty:
        trading_days = len(evolution_df['timestamp'].dt.date.unique()) if hasattr(evolution_df['timestamp'].dt, 'date') else len(set([str(t)[:10] for t in evolution_df['timestamp']]))
    else:
        trading_days = 0
    
    # Análise de aprovação
    passed_profit = user_profit_pct >= FTMO_RULES['profit_target']
    passed_drawdown = user_max_dd <= FTMO_RULES['max_drawdown']
    passed_daily_loss = user_max_daily_loss <= FTMO_RULES['max_daily_loss']
    passed_days = trading_days >= FTMO_RULES['min_trading_days']
    
    # Status geral - TODAS as condições precisam passar
    all_passed = passed_profit and passed_drawdown and passed_daily_loss and passed_days
    
    # Exibição em colunas
    ftmo_cols = st.columns(5)
    
    with ftmo_cols[0]:
        status = "✅" if passed_profit else "❌"
        st.metric(
            f"{status} Meta de Lucro",
            f"{user_profit_pct:+.2f}%",
            delta=f"Meta: +{FTMO_RULES['profit_target']:.0f}%",
            delta_color="off"
        )
    
    with ftmo_cols[1]:
        status = "✅" if passed_drawdown else "❌"
        st.metric(
            f"{status} Max Drawdown",
            f"-{user_max_dd:.2f}%",
            delta=f"Limite: -{FTMO_RULES['max_drawdown']:.0f}%",
            delta_color="off"
        )
    
    with ftmo_cols[2]:
        status = "✅" if passed_daily_loss else "❌"
        st.metric(
            f"{status} Max Loss Diária",
            f"-{user_max_daily_loss:.2f}%",
            delta=f"Limite: -{FTMO_RULES['max_daily_loss']:.0f}%",
            delta_color="off"
        )
    
    with ftmo_cols[3]:
        status = "✅" if passed_days else "❌"
        st.metric(
            f"{status} Dias de Trading",
            f"{trading_days} dias",
            delta=f"Mínimo: {FTMO_RULES['min_trading_days']} dias",
            delta_color="off"
        )
    
    with ftmo_cols[4]:
        if all_passed:
            st.success("### :material/celebration: APROVADO!")
            st.caption("Você passaria no FTMO!")
        else:
            st.error("### :material/cancel: Reprovado")
            st.caption("Ajuste sua estratégia.")
    
    # Gráfico de Radar comparativo
    st.markdown("#### :material/radar: Radar de Performance vs FTMO")
    
    # Normaliza valores para o radar (0-100%)
    # Lucro: 100% = atingiu a meta, 0% = 0 lucro, pode passar de 100%
    radar_profit = min(max(user_profit_pct / FTMO_RULES['profit_target'] * 100, 0), 150)
    
    # Drawdown: 100% = 0 drawdown (perfeito), 0% = atingiu limite
    radar_drawdown = max(100 - (user_max_dd / FTMO_RULES['max_drawdown'] * 100), 0)
    
    # Daily Loss: 100% = 0 perda diária (perfeito), 0% = atingiu limite
    radar_daily_loss = max(100 - (user_max_daily_loss / FTMO_RULES['max_daily_loss'] * 100), 0)
    
    # Win Rate: 100% = 100% win rate
    radar_winrate = metrics['win_rate']
    
    # Profit Factor: Normalizado (1.0 = 50%, 2.0 = 100%)
    radar_pf = min(metrics['profit_factor'] / 2.0 * 100, 100) if metrics['profit_factor'] > 0 else 0
    
    # Dias de trading: 100% = atingiu mínimo
    radar_days = min(trading_days / FTMO_RULES['min_trading_days'] * 100, 100)
    
    # Cria gráfico de radar
    categories = ['Lucro', 'Controle DD', 'Loss Diária', 'Win Rate', 'Profit Factor', 'Dias Trading']
    
    fig_radar = go.Figure()
    
    # Sua performance
    fig_radar.add_trace(go.Scatterpolar(
        r=[radar_profit, radar_drawdown, radar_daily_loss, radar_winrate, radar_pf, radar_days],
        theta=categories,
        fill='toself',
        name='Sua Performance',
        line_color='#00d4aa',
        fillcolor='rgba(0, 212, 170, 0.3)'
    ))
    
    # Meta FTMO (100% em tudo)
    fig_radar.add_trace(go.Scatterpolar(
        r=[100, 100, 100, 60, 50, 100],  # Metas: lucro 100%, dd 100%, daily 100%, WR 60%, PF 1.0=50%, dias 100%
        theta=categories,
        fill='toself',
        name='Meta FTMO',
        line_color='#ffd700',
        fillcolor='rgba(255, 215, 0, 0.1)'
    ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 120],
                tickfont=dict(size=10)
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        showlegend=True,
        template='plotly_dark',
        height=400,
        margin=dict(l=80, r=80, t=40, b=40)
    )
    
    st.plotly_chart(fig_radar, use_container_width=True)
    
    # Explicação das regras
    with st.expander(":material/info: Regras do FTMO Challenge"):
        st.markdown("""
        **FTMO Challenge** é um processo de avaliação para identificar traders qualificados:
        
        | Regra | Valor | Descrição |
        |-------|-------|-----------|
        | 🎯 Meta de Lucro | **+10%** | Atingir 10% de lucro sobre o capital inicial |
        | 📉 Max Drawdown | **-10%** | O patrimônio não pode cair mais que 10% do inicial |
        | 📊 Max Loss Diária | **-5%** | Perda máxima permitida em um único dia |
        | 📅 Mín. Dias Trading | **4 dias** | Mínimo de dias com pelo menos 1 operação |
        | ⏱️ Tempo Limite | **Ilimitado** | Sem prazo para completar o challenge |
        
        *Referência: [FTMO.com](https://ftmo.com)*
        """)

