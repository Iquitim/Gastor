"""
Config Tab - Configuração de taxas de trading.
Permite visualizar e modificar taxas de exchange e slippage por moeda.
"""

import streamlit as st
from src.core.config import (
    EXCHANGE_FEE, 
    SLIPPAGE_BY_COIN, 
    DEFAULT_SLIPPAGE, 
    COINS
)


def render_config_tab():
    """Renderiza a aba de Configurações."""
    
    st.header("⚙️ Configurações de Taxas")
    st.markdown("""
    Configure as taxas de trading aplicadas em cada operação. 
    Taxas mais realistas geram backtests mais confiáveis! 📊
    """)
    
    # Inicializa session state se não existir
    if 'custom_exchange_fee' not in st.session_state:
        st.session_state.custom_exchange_fee = EXCHANGE_FEE
    if 'custom_slippage' not in st.session_state:
        st.session_state.custom_slippage = SLIPPAGE_BY_COIN.copy()
    
    # =========================================================================
    # TABELA DE TAXAS ATUAIS
    # =========================================================================
    st.subheader("📋 Taxas Atuais por Moeda")
    
    # Monta dados da tabela
    exchange_fee = st.session_state.custom_exchange_fee
    custom_slippage = st.session_state.custom_slippage
    
    table_data = []
    for coin in COINS:
        slippage = custom_slippage.get(coin, DEFAULT_SLIPPAGE)
        total = exchange_fee + slippage
        table_data.append({
            "Moeda": coin,
            "Exchange": f"{exchange_fee * 100:.2f}%",
            "Slippage": f"{slippage * 100:.2f}%",
            "Total": f"{total * 100:.2f}%"
        })
    
    # Exibe tabela
    st.table(table_data)
    
    st.divider()
    
    # =========================================================================
    # EDITORES DE TAXAS
    # =========================================================================
    st.subheader("✏️ Modificar Taxas")
    
    col1, col2 = st.columns(2)
    
    # --- Taxa de Exchange (Global) ---
    with col1:
        st.markdown("#### 🏦 Taxa de Exchange (Global)")
        st.caption("Aplicada a todas as moedas")
        
        new_exchange_fee = st.number_input(
            "Taxa de Exchange (%)",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.custom_exchange_fee * 100,
            step=0.01,
            format="%.2f",
            help="Taxa cobrada pela corretora por operação (ex: 0.10% na Binance)",
            key="input_exchange_fee"
        )
    
    # --- Slippage por Moeda ---
    with col2:
        st.markdown("#### 💨 Slippage por Moeda")
        st.caption("Depende da liquidez de cada ativo")
        
        selected_coin = st.selectbox(
            "Selecione a moeda",
            options=COINS,
            key="config_coin_select"
        )
        
        current_slippage = custom_slippage.get(selected_coin, DEFAULT_SLIPPAGE)
        
        new_slippage = st.number_input(
            f"Slippage para {selected_coin} (%)",
            min_value=0.0,
            max_value=2.0,
            value=current_slippage * 100,
            step=0.01,
            format="%.2f",
            help="Diferença entre preço esperado e executado",
            key="input_slippage"
        )
    
    st.markdown("")
    
    # =========================================================================
    # BOTÕES DE AÇÃO
    # =========================================================================
    col_apply, col_reset, col_spacer = st.columns([1, 1, 3])
    
    with col_apply:
        if st.button("✅ Aplicar Alterações", type="primary", use_container_width=True):
            # Atualiza taxa de exchange
            st.session_state.custom_exchange_fee = new_exchange_fee / 100
            
            # Atualiza slippage da moeda selecionada
            st.session_state.custom_slippage[selected_coin] = new_slippage / 100
            
            st.success(f"Taxas atualizadas! Exchange: {new_exchange_fee:.2f}% | {selected_coin} Slippage: {new_slippage:.2f}%")
            st.rerun()
    
    with col_reset:
        if st.button("🔄 Restaurar Padrões", use_container_width=True):
            st.session_state.custom_exchange_fee = EXCHANGE_FEE
            st.session_state.custom_slippage = SLIPPAGE_BY_COIN.copy()
            st.success("Taxas restauradas para os valores padrão!")
            st.rerun()
    
    st.divider()
    
    # =========================================================================
    # INFORMAÇÕES EDUCATIVAS
    # =========================================================================
    with st.expander("💡 **Entenda as Taxas**", expanded=False):
        st.markdown("""
        ### 🏦 Taxa de Exchange (Exchange Fee)
        
        É a comissão cobrada pela corretora (ex: Binance) em cada operação.
        
        - **Maker**: Ordem que adiciona liquidez ao book (geralmente menor)
        - **Taker**: Ordem que consome liquidez do book (geralmente maior)
        
        | Exchange | Taxa Padrão |
        |----------|-------------|
        | Binance | 0.10% |
        | Coinbase | 0.50% |
        | Kraken | 0.26% |
        
        ---
        
        ### 💨 Slippage (Deslizamento)
        
        Diferença entre o preço que você espera e o preço realmente executado.
        
        **Causas:**
        - Baixa liquidez do ativo
        - Alta volatilidade
        - Ordens muito grandes
        - Latência na execução
        
        **Recomendação:** Moedas mais líquidas (BTC, ETH) têm slippage menor.
        Altcoins com menor volume têm slippage maior.
        
        ---
        
        ### 📊 Taxa Total
        
        ```
        Taxa Total = Exchange Fee + Slippage
        ```
        
        Esta taxa é aplicada **duas vezes** em cada trade completo:
        1. Na **compra** (entrada)
        2. Na **venda** (saída)
        
        **Exemplo:** Se taxa total = 0.25%, um trade completo custa ~0.50% do valor.
        """)
    
    # Aviso importante
    st.info("""
    ⚠️ **Nota:** As taxas customizadas persistem apenas durante esta sessão. 
    Ao recarregar a página, os valores padrão serão restaurados.
    """)
