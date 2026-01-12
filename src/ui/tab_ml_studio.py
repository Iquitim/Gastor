"""
ML Studio Tab UI component.
Contains model training, feature analysis, and backtesting.
"""

import os
import streamlit as st
import plotly.express as px

from src.core.ml import TradeModel, FeatureExtractor
from src.core.data_loader import COMMISSION


def render_ml_studio_tab(df):
    """Renderiza a tab do ML Studio."""
    
    st.markdown("O modelo aprenderá com os trades marcados na aba Trading.")
    
    # Abas internas para organização
    ml_tab_train, ml_tab_analysis, ml_tab_backtest = st.tabs([
        "⚙️ Treino & Modelo", 
        "🔍 Análise de Features", 
        "🔮 Backtest & Validação"
    ])

    # --- ABA 1: CONFIGURAÇÃO E TREINO ---
    with ml_tab_train:
        t_col1, t_col2 = st.columns([1, 2])
        
        with t_col1:
            st.subheader("Configuração")
            model_name = st.selectbox("Algoritmo", list(TradeModel.SUPPORTED_MODELS.keys()), index=0, key='ml_model_select')
            
            st.markdown("**Seleção de Features**")
            all_features = [
                'rsi', 'macd', 'macd_hist', 'bb_width', 'bb_pband', 
                'dist_ema9', 'dist_ema21', 'dist_ema50', 
                'volatility', 'hour', 'day_of_week', 'period'
            ]
            default_feats = ['rsi', 'bb_pband', 'dist_ema9', 'hour', 'volatility']
            selected_features = st.multiselect(
                "Features Ativas", all_features, default=default_feats, key='ml_features_select'
            )
            
            st.caption(f"Usando {len(selected_features)} variáveis preditivas.")

        with t_col2:
            st.subheader("Treinamento")
            st.info("O modelo aprenderá com os trades marcados na aba Trading.")
            
            if st.button("🚀 Iniciar Treinamento", type="primary", use_container_width=True):
                MIN_TRADES = 10
                if len(st.session_state.trades) < MIN_TRADES:
                    st.error(f"⚠️ Dados insuficientes! Marque pelo menos {MIN_TRADES} trades.")
                else:
                    with st.spinner(f"Treinando {model_name}..."):
                        try:
                            model = TradeModel(model_name)
                            
                            metrics = model.train(st.session_state.df, st.session_state.trades, feature_cols=selected_features)
                            if "error" in metrics:
                                st.error(metrics["error"])
                            else:
                                st.session_state.model = model
                                st.session_state.training_metrics = metrics
                                # Salva no diretório raiz do projeto
                                model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'model_latest.joblib')
                                model.save(model_path)
                                st.toast("Modelo Treinado e Salvo!", icon="✅")
                        except Exception as e:
                            st.error(f"Erro no treino: {e}")

            if 'training_metrics' in st.session_state:
                metrics = st.session_state.training_metrics
                st.markdown("#### 🎯 Performance (Treino)")
                m1, m2, m3 = st.columns(3)
                m1.metric("Acurácia", f"{metrics.get('accuracy', 0):.2f}")
                m2.metric("Precision", f"{metrics.get('precision', 0):.2f}")
                m3.metric("Recall", f"{metrics.get('recall', 0):.2f}")
    
    # --- ABA 2: ANÁLISE ---
    with ml_tab_analysis:
        st.subheader("🔍 Correlação de Features")
        st.caption("Entenda quais variáveis estão mais relacionadas entre si.")
        
        if st.button("Gerar Heatmap"):
            with st.spinner("Calculando correlações..."):
                features_df = FeatureExtractor.extract_features(st.session_state.df)
                
                all_feat_list = ['rsi', 'macd', 'macd_hist', 'bb_width', 'bb_pband', 
                                 'dist_ema9', 'dist_ema21', 'dist_ema50', 
                                 'volatility', 'hour', 'day_of_week', 'period']
                cols_to_plot = [c for c in features_df.columns if c in all_feat_list]
                if not cols_to_plot: 
                    cols_to_plot = features_df.columns
                
                corr = features_df[cols_to_plot].corr()
                
                fig_corr = px.imshow(
                    corr, text_auto=".1f", aspect="auto", 
                    color_continuous_scale='RdBu_r', 
                    title="Heatmap de Correlação"
                )
                st.plotly_chart(fig_corr, use_container_width=True)
            
    # --- ABA 3: BACKTEST ---
    with ml_tab_backtest:
        st.subheader("🔮 Validação Out-of-Time")
        st.markdown("Simule o modelo em dados passados e futuros (OOT).")
        
        b_col1, b_col2 = st.columns([1, 2])
        with b_col1:
            stop_loss_pct = st.number_input("Stop Loss (%)", 0.0, 20.0, 2.0, step=0.5, help="Vende se cair X% da entrada")
            
        with b_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Executar Backtest", type="primary", use_container_width=True):
                if 'model' not in st.session_state:
                    model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'model_latest.joblib')
                    if os.path.exists(model_path):
                        model = TradeModel()
                        model.load(model_path)
                        st.session_state.model = model
                        st.session_state.training_metrics = model.metrics
                    else:
                        st.error("Nenhum modelo treinado disponível.")
                        
                if 'model' in st.session_state:
                    with st.spinner("Simulando trades..."):
                        model = st.session_state.model
                        df_bt = st.session_state.df
                        preds = model.predict(df_bt)
                        st.session_state.predictions = preds
                        
                        balance = 1000.0
                        holdings = 0.0
                        entry_price = 0.0
                        trades_count = 0
                        wins = 0
                        in_position = False
                        
                        for i in range(len(preds)):
                            price = df_bt['close'].iloc[i]
                            signal = preds.iloc[i]
                            
                            if in_position and stop_loss_pct > 0:
                                pnl_unrealized = (price - entry_price) / entry_price
                                if pnl_unrealized < -(stop_loss_pct/100):
                                    revenue = holdings * price
                                    fee = revenue * COMMISSION
                                    balance += (revenue - fee)
                                    holdings = 0.0
                                    in_position = False
                                    trades_count += 1
                                    continue
                            
                            if signal == 1 and not in_position:
                                amount = (balance * 0.99) / price
                                cost = amount * price
                                fee = cost * COMMISSION
                                balance -= (cost + fee)
                                holdings = amount
                                entry_price = price
                                in_position = True
                                trades_count += 1
                                
                            elif signal == -1 and in_position:
                                revenue = holdings * price
                                fee = revenue * COMMISSION
                                balance += (revenue - fee)
                                if price > entry_price:
                                    wins += 1
                                holdings = 0.0
                                in_position = False
                                trades_count += 1
                        
                        final_val = balance + (holdings * df_bt['close'].iloc[-1])
                        pnl_pct = ((final_val - 1000.0) / 1000.0) * 100
                        win_rate = (wins / max(1, (trades_count/2))) * 100
                        
                        st.session_state.backtest_results = {
                            "pnl_pct": pnl_pct, "pnl_abs": final_val - 1000.0,
                            "trades": int(trades_count/2), "win_rate": win_rate
                        }
                        st.success("Backtest Finalizado!")

        if "backtest_results" in st.session_state:
            res = st.session_state.backtest_results
            st.markdown("---")
            b1, b2, b3 = st.columns(3)
            b1.metric("Resultado Final", f"{res['pnl_pct']:+.2f}%", f"${res['pnl_abs']:+.2f}")
            b2.metric("Total Trades", f"{res['trades']}")
            b3.metric("Taxa de Acerto", f"{res['win_rate']:.0f}%")
