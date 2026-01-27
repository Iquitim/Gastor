"""
Glossary Tab - Explicações didáticas de termos e indicadores de trading.
Escrito para iniciantes que nunca ouviram falar desses conceitos.
"""

import streamlit as st


def render_glossary_tab():
    """Renderiza a aba de Glossário com explicações de indicadores."""
    
    st.header("📖 Glossário de Trading")
    st.markdown("""
    Bem-vindo ao glossário! Aqui explicamos cada termo e indicador de forma simples, 
    como se você nunca tivesse ouvido falar deles antes. 🎓
    """)
    
    # Filtro por categoria
    categories = ["Todos", "📊 Médias Móveis", "📈 Osciladores", "📉 Volatilidade", "🔗 Sinais de Trading", "💰 Termos Gerais", "💸 Taxas e Custos"]
    selected_cat = st.selectbox("Filtrar por categoria", categories)
    
    st.divider()
    
    # =========================================================================
    # CONCEITOS BÁSICOS
    # =========================================================================
    if selected_cat in ["Todos", "💰 Termos Gerais"]:
        st.subheader("🔰 Conceitos Básicos (Leia Primeiro!)")
        st.markdown("*Se você é iniciante, comece por aqui!*")
        
        with st.expander("**O que é um Candle (Vela)?**", expanded=False):
            st.markdown("""
            ### 🕯️ Candle = Uma "foto" do preço em um período
            
            Imagine que você tira uma foto do preço de uma moeda a cada 1 hora. 
            Cada foto mostra 4 informações:
            
            | Termo | O que significa | Exemplo |
            |-------|-----------------|---------|
            | **Open** (Abertura) | Preço no início do período | 100 dólares |
            | **High** (Máxima) | Maior preço atingido | 105 dólares |
            | **Low** (Mínima) | Menor preço atingido | 98 dólares |
            | **Close** (Fechamento) | Preço no final do período | 103 dólares |
            
            🟢 **Candle Verde:** Fechou mais alto do que abriu (preço subiu)  
            🔴 **Candle Vermelho:** Fechou mais baixo do que abriu (preço caiu)
            
            **No Gastor:** Cada candle representa o timeframe selecionado (15min, 1h, 4h ou 1 dia).
            """)
            
        with st.expander("**O que é Timeframe?**", expanded=False):
            st.markdown("""
            ### ⏱️ Timeframe = O "zoom" do seu gráfico
            
            É o período que cada candle representa:
            
            | Timeframe | Cada candle representa | Candles em 1 dia |
            |-----------|------------------------|------------------|
            | 15 minutos | 15 minutos de negociação | 96 candles |
            | 1 hora | 1 hora de negociação | 24 candles |
            | 4 horas | 4 horas de negociação | 6 candles |
            | 1 dia | 1 dia inteiro | 1 candle |
            
            📐 **Analogia:** É como zoom em um mapa. 
            - Timeframe grande (1d) = visão geral do país
            - Timeframe pequeno (15m) = visão detalhada de uma rua
            
            **Dica:** Iniciantes geralmente começam com 1h ou 4h.
            """)
    
    # =========================================================================
    # MÉDIAS MÓVEIS
    # =========================================================================
    if selected_cat in ["Todos", "📊 Médias Móveis"]:
        st.subheader("📊 Médias Móveis")
        st.markdown("*Indicadores que suavizam o preço para ver a tendência geral*")
        
        with st.expander("**SMA - Média Móvel Simples** (Simple Moving Average)", expanded=False):
            st.markdown("""
            ### 📏 SMA = A média dos últimos N preços
            
            **Explicação simples:**  
            Imagine que você quer saber a temperatura média dos últimos 7 dias. 
            Você soma as 7 temperaturas e divide por 7. Pronto, isso é uma SMA!
            
            **Com preços funciona igual:**  
            SMA(20) = Soma dos últimos 20 preços de fechamento ÷ 20
            
            ---
            
            **Fórmula:**
            """)
            st.latex(r"SMA(n) = \frac{P_1 + P_2 + ... + P_n}{n}")
            st.markdown("""
            **Onde:**
            - **P** = Preço de fechamento de cada candle
            - **n** = Número de períodos (ex: 20 candles)
            - **P_1, P_2...** = Preço do 1º candle, 2º candle, etc.
            
            ---
            
            **Exemplo prático:**  
            Últimos 5 preços de fechamento: 100, 102, 98, 105, 103  
            SMA(5) = (100 + 102 + 98 + 105 + 103) ÷ 5 = **101,60**
            
            ---
            
            **Para que serve?**
            - 📈 Se o preço está **acima** da SMA → tendência de ALTA
            - 📉 Se o preço está **abaixo** da SMA → tendência de BAIXA
            - A SMA "suaviza" o gráfico, removendo ruídos
            
            **SMAs comuns:**
            - SMA(20) = Curto prazo
            - SMA(50) = Médio prazo
            - SMA(200) = Longo prazo (muito usada!)
            """)
            
        with st.expander("**EMA - Média Móvel Exponencial** (Exponential Moving Average)", expanded=False):
            st.markdown("""
            ### ⚡ EMA = SMA mais rápida, que dá mais peso aos preços recentes
            
            **Explicação simples:**  
            A SMA trata todos os preços igualmente. Mas e se você quisesse 
            que os preços mais recentes "valessem mais"? Isso é a EMA!
            
            **Analogia:**  
            Imagine notas de uma prova. A SMA seria a média simples. 
            A EMA seria como se as últimas provas valessem mais que as primeiras.
            
            ---
            
            **Fórmula (simplificada):**
            """)
            st.latex(r"EMA_{hoje} = P_{hoje} \times k + EMA_{ontem} \times (1-k)")
            st.markdown("""
            **Onde:**
            - **P_hoje** = Preço de fechamento de hoje
            - **EMA_ontem** = Valor da EMA calculado ontem
            - **k** = Fator de peso (quanto maior, mais peso para preços recentes)
            """)
            st.latex(r"k = \frac{2}{n+1}")
            st.markdown("""
            **Onde:**
            - **n** = Número de períodos (ex: 9, 21, 50)
            
            **Por que usar EMA em vez de SMA?**
            - EMA reage mais rápido às mudanças de preço
            - Ideal para mercados voláteis como criptomoedas
            - Gera sinais mais cedo (mas também mais falsos alarmes)
            
            **EMAs usadas no Gastor:**
            - EMA(9) = Curto prazo (mais rápida)
            - EMA(21) = Médio prazo
            - EMA(50) = Longo prazo (mais lenta)
            """)
            
        with st.expander("**Golden Cross / Death Cross** (Cruzamento de Médias)", expanded=False):
            st.markdown("""
            ### ✨ Golden Cross = Sinal de COMPRA | 💀 Death Cross = Sinal de VENDA
            
            **O que é?**  
            É quando duas médias móveis se cruzam. Uma é rápida (curto prazo) 
            e outra é lenta (longo prazo).
            
            ---
            
            🟢 **Golden Cross (Cruz Dourada):**  
            A média rápida cruza a média lenta **de baixo para cima**  
            → Os preços recentes estão subindo mais que a tendência geral  
            → **Sinal de COMPRA**
            
            🔴 **Death Cross (Cruz da Morte):**  
            A média rápida cruza a média lenta **de cima para baixo**  
            → Os preços recentes estão caindo mais que a tendência geral  
            → **Sinal de VENDA**
            
            ---
            
            **Exemplo clássico:**
            - Média rápida: EMA(9) ou EMA(50)
            - Média lenta: EMA(21) ou EMA(200)
            
            **No Gastor:** A estratégia "Golden Cross" usa exatamente esse conceito!
            """)
    
    # =========================================================================
    # OSCILADORES
    # =========================================================================
    if selected_cat in ["Todos", "📈 Osciladores"]:
        st.subheader("📈 Osciladores")
        st.markdown("*Indicadores que variam entre valores fixos, mostrando força do movimento*")
        
        with st.expander("**RSI - Índice de Força Relativa** (Relative Strength Index)", expanded=False):
            st.markdown("""
            ### 📊 RSI = Termômetro de "cansaço" do preço (0 a 100)
            
            **Explicação simples:**  
            O RSI mede se o preço subiu "demais" ou caiu "demais" recentemente.
            É como um termômetro que vai de 0 a 100.
            
            ---
            
            **Como interpretar:**
            
            | RSI | Significado | Ação |
            |-----|-------------|------|
            | > 70 | **Sobrecomprado** - Subiu muito, pode cair | ⚠️ Cuidado para comprar |
            | 30-70 | Zona neutra | 🔍 Observar |
            | < 30 | **Sobrevendido** - Caiu muito, pode subir | 🟢 Possível oportunidade |
            
            ---
            
            **Fórmula:**
            """)
            st.latex(r"RSI = 100 - \frac{100}{1 + RS}")
            st.markdown("""
            **Onde:**
            - **RSI** = Resultado final (de 0 a 100)
            - **RS** = Força Relativa (Relative Strength)
            """)
            st.latex(r"RS = \frac{\text{Media dos dias que SUBIRAM}}{\text{Media dos dias que CAIRAM}}")
            st.markdown("""
            **Onde:**
            - **Média dos dias que subiram** = Soma dos ganhos ÷ 14 (períodos)
            - **Média dos dias que caíram** = Soma das perdas ÷ 14
            
            **Analogia do dia a dia:**  
            Imagine uma pessoa correndo. Se ela correu muito rápido (RSI alto), 
            provavelmente vai precisar descansar (preço pode cair). 
            Se ela está parada há muito tempo (RSI baixo), pode começar a correr (preço pode subir).
            
            ---
            
            **No Gastor:**  
            A estratégia **RSI Reversal** (campeã!) compra quando RSI < 20 e vende quando RSI > 60.
            
            **Período padrão:** 14 candles
            """)
            
        with st.expander("**MACD** (Moving Average Convergence Divergence)", expanded=False):
            st.markdown("""
            ### 📉 MACD = Mostra quando uma tendência está ganhando ou perdendo força
            
            **Explicação simples:**  
            O MACD compara duas EMAs (lembra delas?) e mostra se estão 
            se aproximando (**convergindo**) ou se afastando (**divergindo**).
            
            ---
            
            **O MACD tem 3 partes:**
            
            1. **Linha MACD** = EMA rápida (12) - EMA lenta (26)
            2. **Linha de Sinal** = EMA(9) da linha MACD
            3. **Histograma** = Diferença entre MACD e Sinal (as barrinhas)
            
            ---
            
            **Fórmulas:**
            """)
            st.latex(r"\text{MACD} = EMA(12) - EMA(26)")
            st.latex(r"\text{Sinal} = EMA(9) \text{ do MACD}")
            st.latex(r"\text{Histograma} = MACD - Sinal")
            st.markdown("""
            ---
            
            **Como usar:**
            
            🟢 **MACD cruza Sinal para CIMA** → Sinal de COMPRA  
            🔴 **MACD cruza Sinal para BAIXO** → Sinal de VENDA
            
            📊 **Histograma crescendo** → Tendência ganhando força  
            📉 **Histograma diminuindo** → Tendência perdendo força
            
            ---
            
            **No Gastor:** Estratégias "MACD Crossover" e "MACD+RSI Combo" usam este indicador.
            """)
            
        with st.expander("**Stochastic RSI** (RSI Estocástico)", expanded=False):
            st.markdown("""
            ### ⚡ Stochastic RSI = RSI turbinado, ainda mais sensível
            
            **Explicação simples:**  
            É um "RSI do RSI". Torna o indicador mais rápido e sensível 
            às mudanças de preço.
            
            ---
            
            **Fórmula:**
            """)
            st.latex(r"StochRSI = \frac{RSI_{atual} - RSI_{min}}{RSI_{max} - RSI_{min}}")
            st.markdown("""
            (Calculado sobre os últimos N períodos)
            
            ---
            
            **Como interpretar (varia de 0 a 1):**
            
            | Valor | Significado |
            |-------|-------------|
            | > 0.8 | Muito sobrecomprado |
            | < 0.2 | Muito sobrevendido |
            
            **Quando usar:** Ideal para quem faz operações rápidas (scalping).
            """)
    
    # =========================================================================
    # VOLATILIDADE
    # =========================================================================
    if selected_cat in ["Todos", "📉 Volatilidade"]:
        st.subheader("📉 Indicadores de Volatilidade")
        st.markdown("*Medem quanto o preço está se movendo (não a direção, mas a intensidade)*")
        
        with st.expander("**Bollinger Bands** (Bandas de Bollinger)", expanded=False):
            st.markdown("""
            ### 📐 Bandas de Bollinger = Faixa que mostra se o preço está "esticado"
            
            **Explicação simples:**  
            Imagine uma linha do meio (a média do preço) com duas linhas ao redor 
            (uma acima, uma abaixo). Essas linhas se afastam quando o preço está 
            muito volátil e se aproximam quando está calmo.
            
            ---
            
            **As 3 linhas:**
            
            | Linha | O que é | Como calcular |
            |-------|---------|---------------|
            | **Banda Superior** | Limite de "caro" | Média + 2× desvio |
            | **Banda Média** | A média (SMA de 20 períodos) | Soma ÷ 20 |
            | **Banda Inferior** | Limite de "barato" | Média - 2× desvio |
            
            ---
            
            **Fórmulas:**
            """)
            st.latex(r"\text{Banda Media} = SMA(20) = \frac{\sum P}{20}")
            st.latex(r"\text{Banda Superior} = SMA(20) + 2 \times \sigma")
            st.latex(r"\text{Banda Inferior} = SMA(20) - 2 \times \sigma")
            st.markdown("""
            **Onde:**
            - **SMA(20)** = Média simples dos últimos 20 preços de fechamento
            - **σ (sigma)** = Desvio padrão (mede o quanto os preços variam da média)
            - **2 ×** = Multiplicador (quanto maior, mais largas as bandas)
            - **Σ P** = Soma de todos os preços
            
            ---
            
            **Como usar:**
            
            | Situação | O que significa |
            |----------|-----------------|
            | Preço toca banda **superior** | Pode estar "caro", possível queda |
            | Preço toca banda **inferior** | Pode estar "barato", possível alta |
            | Bandas muito **apertadas** | "Squeeze" - explosão de movimento vem aí! |
            | Bandas muito **abertas** | Alta volatilidade |
            
            ---
            
            **No Gastor:** A estratégia "Bollinger Bounce" compra quando toca a banda inferior.
            """)
            
        with st.expander("**ATR - Amplitude Média Verdadeira** (Average True Range)", expanded=False):
            st.markdown("""
            ### 📏 ATR = Mede o "tamanho médio" dos movimentos de preço
            
            **Explicação simples:**  
            O ATR não diz se o preço vai subir ou cair. Ele diz o **quanto** 
            o preço costuma se mover. Útil para saber o tamanho do stop loss.
            
            ---
            
            **Conceito de True Range (Amplitude Verdadeira):**
            
            O True Range considera 3 coisas e pega a maior:
            1. Máxima de hoje - Mínima de hoje
            2. |Máxima de hoje - Fechamento de ontem|
            3. |Mínima de hoje - Fechamento de ontem|
            
            **Fórmula:**
            """)
            st.latex(r"TR = \max(H_{hoje}-L_{hoje}, |H_{hoje}-C_{ontem}|, |L_{hoje}-C_{ontem}|)")
            st.latex(r"ATR(14) = \text{Media do TR dos ultimos 14 periodos}")
            st.markdown("""
            **Onde:**
            - **TR** = True Range (Amplitude Verdadeira)
            - **H** = High (preço máximo do candle)
            - **L** = Low (preço mínimo do candle)
            - **C** = Close (preço de fechamento)
            - **max()** = Pega o maior valor entre os 3
            - **| |** = Valor absoluto (sempre positivo)
            - **14** = Número de períodos na média
            
            ---
            
            **Para que serve no Gastor?**
            
            O ATR é usado no **sizing dinâmico por volatilidade**:
            - ATR alto (muito volátil) → Posição MENOR (menos risco)
            - ATR baixo (pouco volátil) → Posição MAIOR
            
            **Período padrão:** 14 candles
            """)
            
        with st.expander("**Donchian Channel** (Canal de Donchian)", expanded=False):
            st.markdown("""
            ### 📊 Donchian = Canal formado pelos extremos de preço
            
            **Explicação simples:**  
            Desenha um canal usando o maior HIGH e o menor LOW dos últimos N períodos.
            Quando o preço rompe esse canal, é um sinal de breakout.
            
            ---
            
            **Fórmulas (bem simples!):**
            """)
            st.latex(r"\text{Linha Superior} = \text{Maior HIGH dos ultimos 20 periodos}")
            st.latex(r"\text{Linha Inferior} = \text{Menor LOW dos ultimos 20 periodos}")
            st.markdown("""
            ---
            
            **Como usar:**
            
            🟢 Preço rompe a linha **superior** → Breakout de ALTA → Sinal de COMPRA  
            🔴 Preço rompe a linha **inferior** → Breakout de BAIXA → Sinal de VENDA
            
            ---
            
            **No Gastor:** A estratégia "Donchian Breakout" usa exatamente isso!
            """)
    
    # =========================================================================
    # SINAIS
    # =========================================================================
    if selected_cat in ["Todos", "🔗 Sinais de Trading"]:
        st.subheader("🔗 Sinais de Trading")
        st.markdown("*Termos usados para descrever oportunidades de compra/venda*")
        
        with st.expander("**Oversold / Overbought** (Sobrevendido / Sobrecomprado)", expanded=False):
            st.markdown("""
            ### 🔴 Sobrecomprado e 🟢 Sobrevendido
            
            São condições extremas identificadas por osciladores como RSI:
            
            ---
            
            📈 **OVERBOUGHT (Sobrecomprado):**
            - O ativo foi comprado por muita gente, muito rápido
            - Preço pode ter subido "demais"
            - **RSI > 70** indica isso
            - ⚠️ Possível correção para baixo
            
            📉 **OVERSOLD (Sobrevendido):**
            - O ativo foi vendido por muita gente, muito rápido
            - Preço pode ter caído "demais"
            - **RSI < 30** indica isso
            - 🟢 Possível recuperação para cima
            
            ---
            
            **⚠️ CUIDADO:**  
            Em tendências muito fortes, o ativo pode ficar oversold ou overbought 
            por MUITO tempo! Não é garantia de reversão.
            """)
            
        with st.expander("**Breakout / Breakdown** (Rompimentos)", expanded=False):
            st.markdown("""
            ### 🚀 Breakout (para cima) e 💥 Breakdown (para baixo)
            
            ---
            
            🚀 **BREAKOUT:**
            - Preço rompe uma **resistência** (teto) importante
            - Geralmente com aumento de volume
            - Indica força compradora
            - **Sinal de continuação de ALTA**
            
            💥 **BREAKDOWN:**
            - Preço rompe um **suporte** (chão) importante
            - Pode indicar pânico ou liquidação
            - **Sinal de continuação de BAIXA**
            
            ---
            
            **Falso Breakout:**  
            Às vezes o preço rompe o nível mas volta rapidamente.
            Por isso é importante confirmar com volume!
            """)
    
    # =========================================================================
    # TERMOS GERAIS
    # =========================================================================
    if selected_cat in ["Todos", "💰 Termos Gerais"]:
        st.subheader("💰 Termos Gerais de Trading")
        st.markdown("*Métricas e conceitos para avaliar performance*")
        
        with st.expander("**PnL - Lucro e Prejuízo** (Profit and Loss)", expanded=False):
            st.markdown("""
            ### 💵 PnL = Quanto você ganhou ou perdeu
            
            **Fórmula:**
            """)
            st.latex(r"PnL\% = \frac{\text{Capital Final} - \text{Capital Inicial}}{\text{Capital Inicial}} \times 100")
            st.markdown("""
            **Onde:**
            - **PnL%** = Lucro ou prejuízo em porcentagem
            - **Capital Final** = Quanto você tem DEPOIS das operações
            - **Capital Inicial** = Quanto você tinha ANTES das operações
            - **× 100** = Converte para porcentagem
            
            ---
            
            **Exemplo:**
            - Capital inicial: 10.000
            - Capital final: 11.500
            - PnL = (11.500 - 10.000) / 10.000 × 100 = **+15%**
            
            **No Gastor:** O PnL é exibido na sidebar e na aba Resultados.
            """)
            
        with st.expander("**Drawdown - Queda Máxima**", expanded=False):
            st.markdown("""
            ### 📉 Drawdown = A maior queda que você teve
            
            **Explicação simples:**  
            Imagine que seu capital chegou a 12.000 dólares (seu pico).
            Depois caiu para 10.000 dólares. O drawdown é essa queda de 2.000 dólares (16.67%).
            
            **Fórmula:**
            """)
            st.latex(r"Drawdown\% = \frac{\text{Valor no Pico} - \text{Valor no Vale}}{\text{Valor no Pico}} \times 100")
            st.markdown("""
            **Onde:**
            - **Drawdown%** = Queda máxima em porcentagem
            - **Valor no Pico** = Maior valor que seu capital atingiu
            - **Valor no Vale** = Menor valor após o pico
            
            ---
            
            **Por que é importante?**
            - Mede o RISCO de uma estratégia
            - Uma estratégia com 50% de drawdown significa que você perdeu METADE do dinheiro em algum momento
            
            **Limite FTMO:** Max Drawdown de 10%
            """)
            
        with st.expander("**Win Rate - Taxa de Acerto**", expanded=False):
            st.markdown("""
            ### 🎯 Win Rate = % de trades que deram lucro
            
            **Fórmula:**
            """)
            st.latex(r"Win Rate\% = \frac{\text{Trades com Lucro}}{\text{Total de Trades}} \times 100")
            st.markdown("""
            **Onde:**
            - **Win Rate%** = Porcentagem de acertos
            - **Trades com Lucro** = Quantas operações deram lucro
            - **Total de Trades** = Todas as operações (lucro + prejuízo)
            
            ---
            
            **Exemplo:**
            - 10 trades no total
            - 7 deram lucro, 3 deram prejuízo
            - Win Rate = 7/10 × 100 = **70%**
            
            ---
            
            **⚠️ ARMADILHA COMUM:**  
            Win Rate alto NÃO significa estratégia lucrativa!
            
            Exemplo de estratégia RUIM:
            - Win Rate: 90% (parece ótimo!)
            - Cada win: +10 dólares
            - Cada loss: -100 dólares
            - Resultado: 9 × 10 dólares - 1 × 100 dólares = **-10 dólares** (prejuízo!)
            """)
            
        with st.expander("**Slippage - Deslizamento de Preço**", expanded=False):
            st.markdown("""
            ### 💨 Slippage = Diferença entre preço esperado e preço real
            
            **Explicação simples:**  
            Você quer comprar por 100 dólares, mas quando a ordem é executada, 
            o preço já mudou para 100 dólares.50. Esse deslizamento é o slippage.
            
            ---
            
            **Por que acontece?**
            - Mercado muito volátil
            - Baixa liquidez (poucos compradores/vendedores)
            - Ordens muito grandes
            
            **Exemplo:**
            - Preço esperado: 50.000 dólares
            - Preço executado: 50.075 dólares
            - Slippage: 75 dólares (0.15%)
            
            **No Gastor:** O slippage é configurável por moeda e já está incluído nos cálculos.
            """)
            
        with st.expander("**Juros Compostos** (Reinvestimento)", expanded=False):
            st.markdown("""
            ### 🔄 Juros Compostos = Reinvestir os lucros
            
            **Explicação simples:**  
            Em vez de sempre operar com o mesmo valor, você reinveste 
            os lucros para aumentar as próximas posições. É o "efeito bola de neve".
            
            **Fórmula dos juros compostos:**
            """)
            st.latex(r"Capital_{final} = Capital_{inicial} \times (1 + taxa)^{n}")
            st.markdown("""
            **Onde:**
            - **Capital_final** = Quanto você terá no final
            - **Capital_inicial** = Quanto você começou
            - **taxa** = Retorno por período (ex: 0.05 = 5%)
            - **n** = Número de períodos (ex: 12 meses)
            - **(1 + taxa)^n** = O efeito "bola de neve"
            
            ---
            
            **Exemplo:**
            - Capital: 10.000
            - Retorno: 5% ao mês (taxa = 0.05)
            - Após 12 meses (sem reinvestir): 10.000 + 12×500 = 16.000
            - Após 12 meses (COM reinvestir): 10.000 × (1.05)^12 = **17.959**
            
            **No Gastor:** Ative "Juros Compostos" no Laboratório de Estratégias.
            """)
            
        with st.expander("**OOT - Validação Fora do Tempo** (Out-of-Time)", expanded=False):
            st.markdown("""
            ### 🔮 OOT = Testar em dados que o modelo nunca viu
            
            **O problema:**  
            Se você treina um modelo com todos os dados e testa nos mesmos dados,
            ele pode "decorar" o passado mas falhar no futuro (overfitting).
            
            **A solução (OOT):**  
            Separar os últimos 30 dias de dados e "escondê-los" do treinamento.
            O modelo só é testado nesses dados depois de treinado.
            
            ---
            
            **Como funciona no Gastor:**
            
            1. Você carrega 90 dias de dados
            2. **60 dias** são visíveis para você marcar trades e treinar o ML
            3. **30 dias** ficam "escondidos" para validação
            4. Se o modelo vai bem nos 30 dias OOT → estratégia confiável!
            
            ---
            
            **Por que isso importa?**  
            Uma estratégia que só funciona no passado é inútil. 
            O OOT simula como ela performaria no "futuro".
            """)
    
    st.divider()
    st.caption("💡 **Dica:** Clique em cada termo para expandir a explicação completa. Comece pelos 'Conceitos Básicos' se você é iniciante!")
    
    # =========================================================================
    # TAXAS E CUSTOS
    # =========================================================================
    if selected_cat in ["Todos", "💸 Taxas e Custos"]:
        st.subheader("💸 Taxas e Custos de Trading")
        st.markdown("*Entenda os custos que afetam cada operação*")
        
        with st.expander("**Taxa de Exchange (Exchange Fee)** - Comissão da Corretora", expanded=False):
            st.markdown("""
            ### 🏦 Taxa de Exchange = Comissão cobrada pela corretora
            
            **Explicação simples:**  
            Toda vez que você compra ou vende um ativo, a corretora (ex: Binance) cobra uma pequena taxa.
            É como pagar pelo serviço de conectar você ao mercado.
            
            ---
            
            **Tipos de taxa:**
            
            | Tipo | Descrição | Valor típico |
            |------|-----------|-------------|
            | **Maker** | Você coloca uma ordem que **adiciona** liquidez | 0.10% ou menos |
            | **Taker** | Você coloca uma ordem que **consome** liquidez | 0.10% |
            
            ---
            
            **Fórmula:**
            """)
            st.latex(r"\text{Custo da Taxa} = \text{Valor da Operação} \times \text{Taxa}")
            st.markdown("""
            **Exemplo:**
            - Você compra R$ 1.000 de Bitcoin
            - Taxa da exchange: 0.10%
            - Custo: R$ 1.000 × 0.001 = **R$ 1,00**
            
            ---
            
            **Comparativo de taxas por exchange:**
            
            | Exchange | Taxa Spot |
            |----------|----------|
            | Binance | 0.10% |
            | Coinbase | 0.50% |
            | Kraken | 0.26% |
            | KuCoin | 0.10% |
            
            **No Gastor:** O valor padrão é 0.10% (Binance). Você pode alterar na aba ⚙️ Configurações.
            """)
        
        with st.expander("**Slippage (Deslizamento)** - Diferença de Preço na Execução", expanded=False):
            st.markdown("""
            ### 💨 Slippage = O preço "escorregou" entre sua ordem e a execução
            
            **Explicação simples:**  
            Você quer comprar por R$ 100,00. Mas quando a corretora processa sua ordem,
            o preço já mudou para R$ 100,15. Esse "escorregão" de 15 centavos é o slippage.
            
            ---
            
            **Por que acontece?**
            
            | Causa | Explicação |
            |-------|------------|
            | **Volatilidade** | Preço muda rápido em mercados agitados |
            | **Baixa liquidez** | Poucos compradores/vendedores |
            | **Ordens grandes** | Sua ordem consome toda a liquidez disponível |
            | **Latência** | Demora entre sua ordem e a execução |
            
            ---
            
            **Slippage por moeda no Gastor:**
            
            | Moeda | Slippage | Justificativa |
            |-------|----------|---------------|
            | BTC/USDT | 0.10% | Maior liquidez do mercado |
            | ETH/USDT | 0.12% | Segunda maior liquidez |
            | SOL/USDT | 0.15% | Boa liquidez |
            | XRP/USDT | 0.12% | Alta liquidez histórica |
            | DOGE/USDT | 0.20% | Volátil, spreads maiores |
            | AVAX/USDT | 0.25% | Liquidez moderada |
            
            ---
            
            **Fórmula:**
            """)
            st.latex(r"\text{Custo do Slippage} = \text{Valor da Operacao} \times \text{Slippage}")
            st.markdown("""
            **Dica:** Moedas mais negociadas têm menor slippage. Altcoins pequenas podem ter slippage de 1% ou mais!
            
            **No Gastor:** Você pode personalizar o slippage de cada moeda na aba ⚙️ Configurações.
            """)
        
        with st.expander("**Taxa Total** - Custo Real de Cada Trade", expanded=False):
            st.markdown("""
            ### 📊 Taxa Total = Exchange Fee + Slippage
            
            **Explicação simples:**  
            A taxa total é a soma de todos os custos que você paga em uma operação.
            
            ---
            
            **Fórmula:**
            """)
            st.latex(r"\text{Taxa Total} = \text{Taxa de Exchange} + \text{Slippage}")
            st.markdown("""
            ---
            
            **Exemplo prático (SOL/USDT):**
            
            | Componente | Valor |
            |------------|-------|
            | Taxa Exchange | 0.10% |
            | Slippage | 0.15% |
            | **Taxa Total** | **0.25%** |
            
            ---
            
            **⚠️ IMPORTANTE: Taxa é cobrada DUAS vezes!**
            
            Em um trade completo (compra + venda), a taxa é aplicada:
            1. **Na compra** (entrada)
            2. **Na venda** (saída)
            
            """)
            st.latex(r"\text{Custo Total do Trade} = 2 \times \text{Taxa Total}")
            st.markdown("""
            **Exemplo:**
            - Taxa Total: 0.25%
            - Custo real de um trade completo: 2 × 0.25% = **0.50%**
            
            Isso significa que você precisa de pelo menos **0.50% de lucro** só para empatar!
            
            ---
            
            **Por que isso importa no Gastor?**
            
            O sistema aplica automaticamente essas taxas em todos os backtests,
            garantindo que os resultados sejam **realistas**. Uma estratégia que
            parece lucrativa sem taxas pode ser perdedora quando os custos são incluídos.
            """)
