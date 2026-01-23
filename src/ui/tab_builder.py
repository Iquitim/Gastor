"""
Strategy Builder Tab UI component - Versão 2 com Grupos.
Permite criar estratégias personalizadas com grupos de regras combinados por AND/OR.
"""

import streamlit as st
from typing import Dict, List, Optional

from src.strategies.custom_strategy import (
    AVAILABLE_INDICATORS,
    AVAILABLE_OPERATORS,
    INDICATOR_CATEGORIES,
    CustomStrategy,
    get_indicators_by_category,
    create_empty_rule,
    create_empty_strategy_config,
    create_empty_group,
    migrate_old_config,
    format_rule,
    format_group,
)
from src.core.strategy_storage import (
    save_strategy,
    load_strategy,
    list_strategies,
    delete_strategy,
    strategy_exists,
)
from src.core.portfolio import adjust_trade_amounts, recalculate_portfolio


# =============================================================================
# SISTEMA DE AÇÕES PENDENTES (resolve delay do Streamlit)
# =============================================================================

def _process_pending_actions():
    """Processa ações pendentes ANTES de renderizar."""
    if 'builder_pending_action' not in st.session_state:
        return
    
    action = st.session_state.builder_pending_action
    del st.session_state.builder_pending_action
    
    if 'builder_config' not in st.session_state:
        return
    
    config = st.session_state.builder_config
    action_type = action.get('type')
    section = action.get('section')  # 'buy' ou 'sell'
    group_idx = action.get('group_idx')
    rule_idx = action.get('rule_idx')
    
    groups_key = f"{section}_groups" if section else None
    
    if action_type == 'add_rule' and groups_key:
        if group_idx < len(config.get(groups_key, [])):
            config[groups_key][group_idx]['rules'].append(create_empty_rule())
    
    elif action_type == 'remove_rule' and groups_key:
        if group_idx < len(config.get(groups_key, [])):
            rules = config[groups_key][group_idx].get('rules', [])
            if rule_idx < len(rules):
                rules.pop(rule_idx)
    
    elif action_type == 'add_group' and groups_key:
        config.setdefault(groups_key, []).append(create_empty_group())
    
    elif action_type == 'remove_group' and groups_key:
        groups = config.get(groups_key, [])
        if group_idx < len(groups):
            groups.pop(group_idx)
        # Garantir pelo menos 1 grupo
        if not config.get(groups_key):
            config[groups_key] = [create_empty_group()]
    
    st.session_state.builder_config = config


def _schedule_action(action_type: str, section: str = None, group_idx: int = None, rule_idx: int = None):
    """Agenda uma ação para ser processada no próximo render."""
    st.session_state.builder_pending_action = {
        'type': action_type,
        'section': section,
        'group_idx': group_idx,
        'rule_idx': rule_idx
    }
    st.rerun()


# =============================================================================
# COMPONENTES DE REGRA
# =============================================================================

def render_rule_compact(rule: Dict, rule_key: str) -> Optional[Dict]:
    """
    Renderiza uma regra em formato compacto com preview.
    
    Returns:
        Regra atualizada ou None se removida
    """
    # Preview da regra em linguagem natural
    preview = format_rule(rule)
    
    # Persistir estado de expansão no session_state
    expander_state_key = f"{rule_key}_expanded"
    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False
    
    # Usar expanded=True quando está sendo editado (mantém aberto após interação)
    is_expanded = st.session_state.get(expander_state_key, False)
    
    with st.expander(f"📊 {preview}", expanded=is_expanded):
        # Marcar como aberto quando estiver dentro (usuário clicou para expandir)
        st.session_state[expander_state_key] = True
        
        # Linha 1: Indicador + Período + Operador
        cols1 = st.columns([3, 1, 2])
        
        indicator_options = list(AVAILABLE_INDICATORS.keys())
        indicator_labels = [AVAILABLE_INDICATORS[k]["label"] for k in indicator_options]
        
        with cols1[0]:
            current_idx = indicator_options.index(rule.get("indicator", "rsi")) if rule.get("indicator") in indicator_options else 0
            selected_label = st.selectbox(
                "Indicador",
                indicator_labels,
                index=current_idx,
                key=f"{rule_key}_ind",
                label_visibility="collapsed"
            )
            rule["indicator"] = indicator_options[indicator_labels.index(selected_label)]
        
        with cols1[1]:
            ind_config = AVAILABLE_INDICATORS.get(rule["indicator"], {})
            if ind_config.get("params"):
                param = ind_config["params"][0]
                current_period = rule.get("params", {}).get(param["name"], param["default"])
                new_period = st.number_input(
                    "Período",
                    min_value=param["min"],
                    max_value=param["max"],
                    value=int(current_period),
                    key=f"{rule_key}_period",
                    label_visibility="collapsed"
                )
                rule["params"] = {param["name"]: new_period}
        
        with cols1[2]:
            op_options = list(AVAILABLE_OPERATORS.keys())
            op_labels = [AVAILABLE_OPERATORS[k]["label"] for k in op_options]
            current_op = op_options.index(rule.get("operator", "<")) if rule.get("operator") in op_options else 0
            selected_op = st.selectbox(
                "Operador",
                op_labels,
                index=current_op,
                key=f"{rule_key}_op",
                label_visibility="collapsed"
            )
            rule["operator"] = op_options[op_labels.index(selected_op)]
        
        # Linha 2: Tipo + Valor/Indicador + Período
        cols2 = st.columns([2, 3, 1])
        
        with cols2[0]:
            value_type = st.selectbox(
                "Comparar com",
                ["constant", "indicator"],
                index=0 if rule.get("value_type", "constant") == "constant" else 1,
                format_func=lambda x: "📊 Valor" if x == "constant" else "📈 Indicador",
                key=f"{rule_key}_vtype",
                label_visibility="collapsed"
            )
            rule["value_type"] = value_type
        
        with cols2[1]:
            if value_type == "constant":
                current_val = rule.get("value", 0)
                if not isinstance(current_val, (int, float)):
                    current_val = 0
                rule["value"] = st.number_input(
                    "Valor",
                    value=float(current_val),
                    step=0.1,
                    key=f"{rule_key}_val",
                    label_visibility="collapsed"
                )
            else:
                current_val_ind = "sma"
                current_val_params = {}
                if isinstance(rule.get("value"), dict):
                    current_val_ind = rule["value"].get("indicator", "sma")
                    current_val_params = rule["value"].get("params", {})
                
                val_idx = indicator_options.index(current_val_ind) if current_val_ind in indicator_options else 0
                selected_val = st.selectbox(
                    "Indicador",
                    indicator_labels,
                    index=val_idx,
                    key=f"{rule_key}_val_ind",
                    label_visibility="collapsed"
                )
                selected_val_key = indicator_options[indicator_labels.index(selected_val)]
                rule["value"] = {"indicator": selected_val_key, "params": current_val_params}
        
        with cols2[2]:
            if value_type == "indicator":
                val_ind_config = AVAILABLE_INDICATORS.get(rule["value"]["indicator"], {})
                if val_ind_config.get("params"):
                    val_param = val_ind_config["params"][0]
                    current_val_period = rule["value"].get("params", {}).get(val_param["name"], val_param["default"])
                    new_val_period = st.number_input(
                        "Período",
                        min_value=val_param["min"],
                        max_value=val_param["max"],
                        value=int(current_val_period),
                        key=f"{rule_key}_val_period",
                        label_visibility="collapsed"
                    )
                    rule["value"]["params"] = {val_param["name"]: new_val_period}
        
        # Botão remover
        if st.button("🗑️ Remover regra", key=f"{rule_key}_del", use_container_width=True):
            # Limpar estado de expansão da regra removida
            if expander_state_key in st.session_state:
                del st.session_state[expander_state_key]
            return None
    
    return rule


# =============================================================================
# COMPONENTE DE GRUPO
# =============================================================================

def render_group(group: Dict, group_key: str, group_idx: int, color: str, section: str) -> Optional[Dict]:
    """
    Renderiza um grupo de regras.
    
    Args:
        section: 'buy' ou 'sell' para identificar a seção
    
    Returns:
        Grupo atualizado ou None se removido
    """
    logic = group.get("logic", "AND")
    rules = group.get("rules", [])
    
    # Header do grupo com cor
    border_color = "#10b981" if color == "green" else "#ef4444"
    
    st.markdown(f"""
        <div style="
            border-left: 4px solid {border_color};
            padding-left: 12px;
            margin-bottom: 10px;
        ">
            <span style="color: {border_color}; font-weight: bold;">
                GRUPO {group_idx + 1}
            </span>
        </div>
    """, unsafe_allow_html=True)
    
    # Controles do grupo
    ctrl_cols = st.columns([3, 1, 1])
    
    with ctrl_cols[0]:
        new_logic = st.radio(
            f"Lógica do Grupo {group_idx + 1}",
            ["AND", "OR"],
            index=0 if logic == "AND" else 1,
            horizontal=True,
            key=f"{group_key}_logic",
            label_visibility="collapsed"
        )
        group["logic"] = new_logic
    
    with ctrl_cols[2]:
        if st.button("🗑️", key=f"{group_key}_del_group", help="Remover grupo"):
            _schedule_action('remove_group', section=section, group_idx=group_idx)
            return None
    
    # Regras do grupo
    updated_rules = []
    
    for i, rule in enumerate(rules):
        # Mostrar AND/OR entre regras - com destaque visual grande
        if i > 0:
            logic_color = "#f59e0b" if new_logic == "OR" else "#3b82f6"
            st.markdown(f"""
                <center>
                    <span style='
                        background: {logic_color};
                        color: white;
                        padding: 6px 24px;
                        border-radius: 20px;
                        font-weight: bold;
                        font-size: 16px;
                        letter-spacing: 2px;
                        display: inline-block;
                        margin: 8px 0;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
                    '>
                        {new_logic}
                    </span>
                </center>
            """, unsafe_allow_html=True)
        
        rule_key = f"{group_key}_rule_{i}"
        
        # Renderizar regra com botão de remover que usa schedule_action
        updated_rule = render_rule_compact(rule.copy(), rule_key)
        
        if updated_rule is not None:
            updated_rules.append(updated_rule)
        else:
            # Usuário clicou em remover - agendar ação
            _schedule_action('remove_rule', section=section, group_idx=group_idx, rule_idx=i)
    
    group["rules"] = updated_rules
    
    # Botão adicionar regra - usa schedule_action para ação imediata
    if st.button(f"➕ Regra", key=f"{group_key}_add_rule", use_container_width=True):
        _schedule_action('add_rule', section=section, group_idx=group_idx)
    
    return group


# =============================================================================
# COMPONENTE DE SEÇÃO (COMPRA/VENDA)
# =============================================================================

def render_section(section_key: str, groups: List[Dict], groups_logic: str, 
                   color: str, emoji: str, title: str) -> tuple:
    """
    Renderiza uma seção completa (compra ou venda) com múltiplos grupos.
    
    Returns:
        (grupos atualizados, lógica entre grupos)
    """
    # Header
    st.markdown(f"### {emoji} {title}")
    
    # Renderiza grupos
    updated_groups = []
    new_groups_logic = groups_logic
    
    for i, group in enumerate(groups):
        # Mostrar lógica entre grupos com badge visual destacado
        if i > 0:
            # Badge visual grande entre grupos
            logic_color = "#f59e0b" if new_groups_logic == "OR" else "#3b82f6"
            st.markdown(f"""
                <center>
                    <span style='
                        background: linear-gradient(135deg, {logic_color}, {logic_color}dd);
                        color: white;
                        padding: 8px 32px;
                        border-radius: 25px;
                        font-weight: bold;
                        font-size: 18px;
                        letter-spacing: 3px;
                        display: inline-block;
                        margin: 12px 0;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                        border: 2px solid white;
                    '>
                        {new_groups_logic}
                    </span>
                </center>
            """, unsafe_allow_html=True)
            
            # Seletor para trocar a lógica
            logic_cols = st.columns([1, 2, 1])
            with logic_cols[1]:
                new_groups_logic = st.radio(
                    f"Lógica entre grupos",
                    ["AND", "OR"],  # Ordem consistente: AND primeiro
                    index=0 if groups_logic == "AND" else 1,
                    horizontal=True,
                    key=f"{section_key}_logic_before_{i}",
                    label_visibility="collapsed"
                )
                # Descrição
                if new_groups_logic == "OR":
                    st.caption("☝️ *Pelo menos um grupo deve ser satisfeito*")
                else:
                    st.caption("☝️ *Todos os grupos devem ser satisfeitos*")
        
        with st.container(border=True):
            group_key = f"{section_key}_group_{i}"
            updated_group = render_group(group.copy(), group_key, i, color, section=section_key)
            
            if updated_group is not None:
                updated_groups.append(updated_group)
    
    # Garantir pelo menos 1 grupo
    if not updated_groups:
        updated_groups = [create_empty_group()]
    
    # Área de adicionar grupo com seletor de lógica
    st.write("")
    add_cols = st.columns([1, 2, 1])
    
    with add_cols[1]:
        # Seletor de como o novo grupo será conectado
        if len(updated_groups) >= 1:
            st.markdown("<center><small style='color: gray;'>Próximo grupo será conectado com:</small></center>", unsafe_allow_html=True)
            next_logic = st.radio(
                "Lógica para próximo grupo",
                ["AND", "OR"],  # Ordem consistente: AND primeiro
                index=0 if new_groups_logic == "AND" else 1,
                horizontal=True,
                key=f"{section_key}_next_logic",
                label_visibility="collapsed"
            )
            new_groups_logic = next_logic
        
        if st.button(f"➕ Adicionar Grupo", key=f"{section_key}_add_group", use_container_width=True, type="secondary"):
            _schedule_action('add_group', section=section_key)
    
    return updated_groups, new_groups_logic


# =============================================================================
# PRINCIPAL
# =============================================================================

def render_builder_tab(df):
    """Renderiza a tab do Construtor de Estratégias v2."""
    
    # Processar ações pendentes ANTES de renderizar (resolve delay do Streamlit)
    _process_pending_actions()
    
    st.markdown("Crie estratégias combinando grupos de regras com lógica AND/OR.")
    
    # Inicializa estado
    if 'builder_config' not in st.session_state:
        st.session_state.builder_config = create_empty_strategy_config()
    
    # Migra se formato antigo
    config = migrate_old_config(st.session_state.builder_config)
    
    # === NOME ===
    st.markdown("---")
    name_cols = st.columns([3, 1])
    
    with name_cols[0]:
        config["name"] = st.text_input(
            "📝 Nome da Estratégia",
            value=config.get("name", ""),
            placeholder="Ex: Z-Score Robusto",
            key="builder_name"
        )
    
    with name_cols[1]:
        st.write("")
        if st.button("🔄 Limpar", use_container_width=True, type="secondary"):
            st.session_state.builder_config = create_empty_strategy_config()
            st.rerun()
    
    st.markdown("---")
    
    # === REGRAS DE COMPRA ===
    buy_groups, buy_groups_logic = render_section(
        "buy",
        config.get("buy_groups", [create_empty_group()]),
        config.get("buy_groups_logic", "OR"),
        "green",
        "🟢",
        "Regras de COMPRA"
    )
    config["buy_groups"] = buy_groups
    config["buy_groups_logic"] = buy_groups_logic
    
    st.markdown("---")
    
    # === REGRAS DE VENDA ===
    sell_groups, sell_groups_logic = render_section(
        "sell",
        config.get("sell_groups", [create_empty_group()]),
        config.get("sell_groups_logic", "OR"),
        "red",
        "🔴",
        "Regras de VENDA"
    )
    config["sell_groups"] = sell_groups
    config["sell_groups_logic"] = sell_groups_logic
    
    # Atualiza estado
    st.session_state.builder_config = config
    
    st.markdown("---")
    
    # === AÇÕES ===
    action_cols = st.columns(3)
    
    with action_cols[0]:
        if st.button("💾 Salvar", use_container_width=True, type="secondary"):
            if not config.get("name"):
                st.error("Digite um nome!")
            else:
                try:
                    save_strategy(config["name"], config)
                    st.success(f"✅ Salva: {config['name']}")
                except Exception as e:
                    st.error(f"Erro: {e}")
    
    with action_cols[1]:
        if st.button("🧪 Testar", use_container_width=True, type="secondary"):
            try:
                strategy = CustomStrategy(config)
                strategy_df = st.session_state.get('full_df', df)
                trades = strategy.apply(strategy_df)
                st.info(f"🔎 Geraria **{len(trades)} trades**")
            except Exception as e:
                st.error(f"Erro: {e}")
    
    with action_cols[2]:
        if st.button("🚀 Aplicar", use_container_width=True, type="primary"):
            try:
                strategy = CustomStrategy(config)
                strategy_df = st.session_state.get('full_df', df)
                coin = st.session_state.get('selected_coin', 'SOL/USDT')
                
                raw_trades = strategy.apply(strategy_df, coin=coin)
                
                if not raw_trades:
                    st.warning("Nenhum trade gerado.")
                else:
                    initial_balance = st.session_state.get('initial_balance', 10000.0)
                    position_pct = st.session_state.get('strategy_position_size', 100)
                    
                    adjusted_trades = adjust_trade_amounts(
                        raw_trades, 
                        initial_balance, 
                        position_pct,
                        force_close=True,
                        last_price=strategy_df['close'].iloc[-1],
                        last_timestamp=strategy_df.index[-1],
                        use_compound=False
                    )
                    
                    recalculate_portfolio(adjusted_trades)
                    st.success(f"✅ {len(adjusted_trades)} trades aplicados!")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")
    
    # === ESTRATÉGIAS SALVAS ===
    st.markdown("---")
    st.markdown("### 📂 Estratégias Salvas")
    
    saved = list_strategies()
    
    if not saved:
        st.info("Nenhuma estratégia salva.")
    else:
        for strat in saved:
            with st.container(border=True):
                cols = st.columns([3, 1, 1, 1])
                
                with cols[0]:
                    st.markdown(f"**{strat['name']}**")
                    st.caption(f"🟢 {strat['buy_rules_count']} | 🔴 {strat['sell_rules_count']}")
                
                with cols[1]:
                    if st.button("📥", key=f"load_{strat['filename']}", help="Carregar"):
                        loaded = load_strategy(strat['name'])
                        if loaded:
                            st.session_state.builder_config = migrate_old_config(loaded)
                            st.rerun()
                
                with cols[2]:
                    if st.button("🚀", key=f"apply_{strat['filename']}", help="Aplicar"):
                        loaded = load_strategy(strat['name'])
                        if loaded:
                            try:
                                strategy = CustomStrategy(loaded)
                                strategy_df = st.session_state.get('full_df', df)
                                
                                raw_trades = strategy.apply(strategy_df)
                                if raw_trades:
                                    adjusted_trades = adjust_trade_amounts(
                                        raw_trades, 
                                        st.session_state.get('initial_balance', 10000.0),
                                        st.session_state.get('strategy_position_size', 100),
                                        force_close=True,
                                        last_price=strategy_df['close'].iloc[-1],
                                        last_timestamp=strategy_df.index[-1],
                                        use_compound=False
                                    )
                                    recalculate_portfolio(adjusted_trades)
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Erro: {e}")
                
                with cols[3]:
                    if st.button("🗑️", key=f"del_{strat['filename']}", help="Excluir"):
                        delete_strategy(strat['name'])
                        st.rerun()
    
    # === REFERÊNCIA ===
    with st.expander("📖 Indicadores Disponíveis"):
        indicators_by_cat = get_indicators_by_category()
        for cat_label, indicators in indicators_by_cat.items():
            st.markdown(f"**{cat_label}**")
            st.caption(" • ".join([ind['label'] for ind in indicators]))
