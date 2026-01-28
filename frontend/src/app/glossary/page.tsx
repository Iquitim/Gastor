"use client";

import { useState, useMemo, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import "katex/dist/katex.min.css";
import { BlockMath } from "react-katex";

interface GlossaryItem {
    term: string;
    category: string;
    shortDescription: string;
    fullDescription: string;
    formula?: string;
    variables?: string[]; // Explicação das variáveis
    example?: string;
    inGastor?: string;
}

const GLOSSARY_ITEMS: GlossaryItem[] = [
    // CONCEITOS BÁSICOS
    {
        term: "Candle (Vela)",
        category: "Básico",
        shortDescription: 'Uma "foto" do preço em um período',
        fullDescription: `Cada candle mostra 4 informações:
• Open (Abertura): Preço no início
• High (Máxima): Maior preço atingido
• Low (Mínima): Menor preço atingido
• Close (Fechamento): Preço no final

Candle Verde: Fechou mais alto (preço subiu)
Candle Vermelho: Fechou mais baixo (preço caiu)`,
    },
    {
        term: "Timeframe",
        category: "Básico",
        shortDescription: 'O "zoom" do seu gráfico',
        fullDescription: `É o período que cada candle representa:
• 15 minutos = 96 candles/dia
• 1 hora = 24 candles/dia
• 4 horas = 6 candles/dia
• 1 dia = 1 candle/dia

Iniciantes geralmente começam com 1h ou 4h.`,
    },
    // MÉDIAS MÓVEIS
    {
        term: "SMA (Média Móvel Simples)",
        category: "Médias Móveis",
        shortDescription: "A média dos últimos N preços",
        fullDescription: `Soma dos últimos N preços de fechamento dividido por N.

Se o preço está ACIMA da SMA → tendência de ALTA
Se o preço está ABAIXO da SMA → tendência de BAIXA

SMAs comuns: 20 (curto), 50 (médio), 200 (longo prazo)`,
        formula: "SMA(n) = \\frac{P_1 + P_2 + ... + P_n}{n}",
        variables: [
            "P₁, P₂, ... Pₙ = Preços de fechamento dos últimos n candles",
            "n = Número de períodos (ex: 20, 50, 200)"
        ],
        example: "Últimos 5 preços: 100, 102, 98, 105, 103\nSMA(5) = 508 ÷ 5 = 101,60",
    },
    {
        term: "EMA (Média Móvel Exponencial)",
        category: "Médias Móveis",
        shortDescription: "SMA mais rápida, dá mais peso aos preços recentes",
        fullDescription: `A EMA reage mais rápido às mudanças de preço. Os preços mais recentes "valem mais" no cálculo.

Ideal para mercados voláteis como criptomoedas.
Gera sinais mais cedo (mas também mais falsos alarmes).`,
        formula: "EMA_t = P_t \\times k + EMA_{t-1} \\times (1-k)",
        variables: [
            "EMAₜ = Valor da EMA no período atual",
            "Pₜ = Preço de fechamento atual",
            "EMAₜ₋₁ = Valor da EMA no período anterior",
            "k = Fator de suavização = 2 / (n + 1)",
            "n = Número de períodos (ex: 9, 21, 50)"
        ],
        inGastor: "EMA(9) curto prazo, EMA(21) médio prazo, EMA(50) longo prazo",
    },
    {
        term: "Golden Cross / Death Cross",
        category: "Médias Móveis",
        shortDescription: "Cruzamento de médias móveis",
        fullDescription: `Golden Cross (Cruz Dourada):
Média rápida cruza a lenta de BAIXO para CIMA → Sinal de COMPRA

Death Cross (Cruz da Morte):
Média rápida cruza a lenta de CIMA para BAIXO → Sinal de VENDA`,
        inGastor: 'A estratégia "Golden Cross" usa EMA(9) vs EMA(21)',
    },
    // OSCILADORES
    {
        term: "RSI (Índice de Força Relativa)",
        category: "Osciladores",
        shortDescription: 'Termômetro de "cansaço" do preço (0 a 100)',
        fullDescription: `O RSI mede se o preço subiu "demais" ou caiu "demais".

> 70 = Sobrecomprado (subiu muito, pode cair)
30-70 = Zona neutra
< 30 = Sobrevendido (caiu muito, pode subir)

Período padrão: 14 candles`,
        formula: "RSI = 100 - \\frac{100}{1 + RS}",
        variables: [
            "RS = Força Relativa = Média dos Ganhos / Média das Perdas",
            "Média dos Ganhos = Soma das variações positivas / n",
            "Média das Perdas = Soma das variações negativas / n",
            "n = Período (geralmente 14)"
        ],
        inGastor: 'Estratégia "RSI Reversal" compra quando RSI < 30',
    },
    {
        term: "MACD",
        category: "Osciladores",
        shortDescription: "Mostra quando tendência ganha ou perde força",
        fullDescription: `MACD compara duas EMAs e mostra convergência/divergência.

3 componentes:
• Linha MACD = EMA(12) - EMA(26)
• Linha de Sinal = EMA(9) do MACD
• Histograma = MACD - Sinal

MACD cruza Sinal para CIMA → COMPRA
MACD cruza Sinal para BAIXO → VENDA`,
        formula: "MACD = EMA_{12} - EMA_{26}",
        variables: [
            "EMA₁₂ = Média Móvel Exponencial de 12 períodos",
            "EMA₂₆ = Média Móvel Exponencial de 26 períodos",
            "Linha de Sinal = EMA de 9 períodos do MACD"
        ],
        inGastor: 'Estratégias "MACD Crossover" e "MACD+RSI Combo"',
    },
    {
        term: "Stochastic RSI",
        category: "Osciladores",
        shortDescription: 'RSI "turbinado", ainda mais sensível',
        fullDescription: `É um "RSI do RSI". Torna o indicador mais rápido e sensível às mudanças.

Varia de 0 a 1:
> 0.8 = Muito sobrecomprado
< 0.2 = Muito sobrevendido

Ideal para operações rápidas (scalping).`,
        formula: "StochRSI = \\frac{RSI - RSI_{min}}{RSI_{max} - RSI_{min}}",
        variables: [
            "RSI = Valor atual do RSI",
            "RSIₘᵢₙ = Menor RSI nos últimos n períodos",
            "RSIₘₐₓ = Maior RSI nos últimos n períodos",
            "n = Período de lookback (geralmente 14)"
        ],
    },
    // VOLATILIDADE
    {
        term: "Bollinger Bands",
        category: "Volatilidade",
        shortDescription: 'Faixa que mostra se o preço está "esticado"',
        fullDescription: `3 linhas que se adaptam à volatilidade:
• Banda Superior = Média + 2× desvio
• Banda Média = SMA(20)
• Banda Inferior = Média - 2× desvio

Preço toca banda SUPERIOR → pode estar "caro"
Preço toca banda INFERIOR → pode estar "barato"
Bandas APERTADAS → explosão de movimento vem aí!`,
        formula: "BB_{\\pm} = SMA(20) \\pm 2\\sigma",
        variables: [
            "SMA(20) = Média móvel simples de 20 períodos",
            "σ = Desvio padrão dos últimos 20 preços",
            "2 = Multiplicador padrão (pode ser ajustado)"
        ],
        inGastor: '"Bollinger Bounce" compra na banda inferior',
    },
    {
        term: "ATR (Average True Range)",
        category: "Volatilidade",
        shortDescription: 'Mede o "tamanho médio" dos movimentos',
        fullDescription: `O ATR não diz direção, diz QUANTO o preço costuma se mover.
Útil para calcular stop loss e tamanho de posição.

ATR alto → Posição MENOR (mais risco)
ATR baixo → Posição MAIOR

Período padrão: 14 candles`,
        formula: "ATR = \\frac{1}{n}\\sum_{i=1}^{n} TR_i",
        variables: [
            "TR = True Range = máx(High - Low, |High - Close anterior|, |Low - Close anterior|)",
            "n = Período (geralmente 14)",
            "High = Máxima do candle",
            "Low = Mínima do candle"
        ],
        inGastor: "Usado no sizing dinâmico por volatilidade",
    },
    {
        term: "Donchian Channel",
        category: "Volatilidade",
        shortDescription: "Canal formado pelos extremos de preço",
        fullDescription: `Canal usando o maior HIGH e menor LOW dos últimos N períodos.

Preço rompe linha SUPERIOR → Breakout de ALTA
Preço rompe linha INFERIOR → Breakout de BAIXA

Período comum: 20 candles`,
        formula: "Upper = \\max(High_{n}) \\quad Lower = \\min(Low_{n})",
        variables: [
            "Upper = Linha superior do canal",
            "Lower = Linha inferior do canal",
            "Highₙ = Máximas dos últimos n candles",
            "Lowₙ = Mínimas dos últimos n candles",
            "n = Período (geralmente 20)"
        ],
        inGastor: '"Donchian Breakout" opera rompimentos',
    },
    // SINAIS
    {
        term: "Oversold / Overbought",
        category: "Sinais",
        shortDescription: "Condições extremas de compra/venda",
        fullDescription: `Overbought (Sobrecomprado):
Comprado por muita gente, muito rápido
RSI > 70 indica isso
Possível correção para baixo

Oversold (Sobrevendido):
Vendido por muita gente, muito rápido
RSI < 30 indica isso
Possível recuperação para cima

Atenção: Em tendências fortes, pode ficar nesses níveis por muito tempo!`,
    },
    {
        term: "Breakout / Breakdown",
        category: "Sinais",
        shortDescription: "Rompimentos de níveis importantes",
        fullDescription: `Breakout:
Preço rompe uma RESISTÊNCIA (teto)
Com aumento de volume = sinal de ALTA

Breakdown:
Preço rompe um SUPORTE (chão)
Pode indicar pânico = sinal de BAIXA

Falso Breakout: preço rompe mas volta rapidamente`,
    },
    // TERMOS GERAIS
    {
        term: "PnL (Profit and Loss)",
        category: "Termos Gerais",
        shortDescription: "Quanto você ganhou ou perdeu",
        fullDescription: `Lucro ou prejuízo total das operações.`,
        formula: "PnL\\% = \\frac{Capital_{final} - Capital_{inicial}}{Capital_{inicial}} \\times 100",
        variables: [
            "Capital final = Valor total após todas as operações",
            "Capital inicial = Valor investido no início",
            "PnL% = Variação percentual do capital"
        ],
        example: "Inicial: $10.000, Final: $11.500\nPnL = +15%",
    },
    {
        term: "Drawdown",
        category: "Termos Gerais",
        shortDescription: "A maior queda que você teve",
        fullDescription: `Mede o risco de uma estratégia.
Uma estratégia com 50% de drawdown significa que você perdeu METADE em algum momento.

Limite FTMO: Max Drawdown de 10%`,
        formula: "Drawdown\\% = \\frac{Pico - Vale}{Pico} \\times 100",
        variables: [
            "Pico = Maior valor atingido pelo patrimônio",
            "Vale = Menor valor após o pico (antes de nova máxima)"
        ],
    },
    {
        term: "Win Rate",
        category: "Termos Gerais",
        shortDescription: "% de trades que deram lucro",
        fullDescription: `Taxa de acerto.

Atenção: Win Rate alto NÃO significa lucro!
Ex: 90% de acerto com wins de $10 e losses de $100
= 9×$10 - 1×$100 = -$10 (prejuízo!)`,
        formula: "WinRate\\% = \\frac{\\text{Trades Lucrativos}}{\\text{Total de Trades}} \\times 100",
        variables: [
            "Trades Lucrativos = Número de operações com lucro",
            "Total de Trades = Todas as operações realizadas"
        ],
        example: "7 wins de 10 trades = 70% Win Rate",
    },
    {
        term: "Profit Factor",
        category: "Termos Gerais",
        shortDescription: "Lucro bruto dividido por prejuízo bruto",
        fullDescription: `Quanto você ganha para cada $1 que perde.

> 1.0 = Lucrativo
> 1.5 = Bom
> 2.0 = Excelente

É mais confiável que Win Rate isolado.`,
        formula: "PF = \\frac{\\sum Ganhos}{\\sum Perdas}",
        variables: [
            "∑ Ganhos = Soma de todos os lucros das operações",
            "∑ Perdas = Soma de todas as perdas das operações (valor absoluto)"
        ],
    },
    {
        term: "Slippage",
        category: "Taxas e Custos",
        shortDescription: "Diferença entre preço esperado e executado",
        fullDescription: `Você quer comprar por $100, mas executa por $100.15.
O "escorregão" de $0.15 é o slippage.

Causas:
• Mercado volátil
• Baixa liquidez
• Ordens grandes`,
        inGastor: "Slippage é configurável por moeda",
    },
    {
        term: "Taxa de Exchange",
        category: "Taxas e Custos",
        shortDescription: "Comissão cobrada pela corretora",
        fullDescription: `Paga a cada compra ou venda.

Tipos:
• Maker (adiciona liquidez): ~0.10%
• Taker (consome liquidez): ~0.10%

Taxas por exchange:
• Binance: 0.10%
• Coinbase: 0.50%
• Kraken: 0.26%`,
        inGastor: "Padrão: 0.10% (Binance). Configurável em Settings.",
    },
    {
        term: "Juros Compostos",
        category: "Termos Gerais",
        shortDescription: 'Reinvestir lucros - efeito "bola de neve"',
        fullDescription: `Em vez de operar sempre com o mesmo valor, reinveste os lucros.

Exemplo (5%/mês por 12 meses):
• Sem reinvestir: $10.000 → $16.000
• COM reinvestir: $10.000 → $17.959`,
        formula: "Capital_{final} = Capital_{inicial} \\times (1 + r)^n",
        variables: [
            "Capital inicial = Valor investido no início",
            "r = Taxa de retorno por período (ex: 0.05 = 5%)",
            "n = Número de períodos",
            "Capital final = Valor após todos os períodos"
        ],
        inGastor: 'Ative "Juros Compostos" no Laboratório',
    },
    {
        term: "OOT (Out-of-Time)",
        category: "Termos Gerais",
        shortDescription: "Validação em dados que o modelo nunca viu",
        fullDescription: `Separa dados para teste DEPOIS do treinamento.
Evita "decorar" o passado (overfitting).

No Gastor:
• 60 dias para treinar
• 30 dias "escondidos" para validar

Se funciona nos 30 dias OOT → estratégia confiável!`,
    },
];

const CATEGORIES = [
    "Todos",
    "Básico",
    "Médias Móveis",
    "Osciladores",
    "Volatilidade",
    "Sinais",
    "Termos Gerais",
    "Taxas e Custos",
];

function GlossaryContent() {
    const searchParams = useSearchParams();
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedCategory, setSelectedCategory] = useState("Todos");
    const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

    // Ler termo de busca da URL (vindo de links externos)
    useEffect(() => {
        const urlSearch = searchParams.get("search");
        if (urlSearch) {
            setSearchTerm(urlSearch);
            // Encontrar e expandir o item correspondente
            const matchingItem = GLOSSARY_ITEMS.find(
                item => item.term.toLowerCase().includes(urlSearch.toLowerCase())
            );
            if (matchingItem) {
                setExpandedItems(new Set([matchingItem.term]));
            }
        }
    }, [searchParams]);

    const filteredItems = useMemo(() => {
        return GLOSSARY_ITEMS.filter((item) => {
            const matchesSearch = searchTerm === "" ||
                item.term.toLowerCase().includes(searchTerm.toLowerCase()) ||
                item.shortDescription.toLowerCase().includes(searchTerm.toLowerCase());
            const matchesCategory = selectedCategory === "Todos" || item.category === selectedCategory;
            return matchesSearch && matchesCategory;
        });
    }, [searchTerm, selectedCategory]);

    const toggleExpand = (term: string) => {
        setExpandedItems(prev => {
            const newSet = new Set(prev);
            if (newSet.has(term)) {
                newSet.delete(term);
            } else {
                newSet.add(term);
            }
            return newSet;
        });
    };

    const expandAll = () => setExpandedItems(new Set(filteredItems.map(i => i.term)));
    const collapseAll = () => setExpandedItems(new Set());

    return (
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white">Glossário de Trading</h1>
                <p className="text-slate-400 mt-1">
                    Explicações simples para iniciantes e referência rápida
                </p>
            </div>

            {/* Search and Filter */}
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-4 mb-6">
                <div className="flex flex-col sm:flex-row gap-4">
                    <div className="flex-1">
                        <input
                            type="text"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            placeholder="Buscar termo..."
                            className="w-full bg-slate-800 border border-slate-700 rounded-md px-4 py-2 text-white placeholder-slate-400"
                        />
                    </div>
                    <div className="flex gap-2">
                        <select
                            value={selectedCategory}
                            onChange={(e) => setSelectedCategory(e.target.value)}
                            className="bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-white"
                        >
                            {CATEGORIES.map(cat => (
                                <option key={cat} value={cat}>{cat}</option>
                            ))}
                        </select>
                        <button
                            onClick={expandAll}
                            className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded-md"
                        >
                            Expandir
                        </button>
                        <button
                            onClick={collapseAll}
                            className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded-md"
                        >
                            Recolher
                        </button>
                    </div>
                </div>
            </div>

            {/* Results count */}
            <p className="text-sm text-slate-400 mb-4">
                {filteredItems.length} termo(s) encontrado(s)
            </p>

            {/* Glossary Items */}
            <div className="space-y-3">
                {filteredItems.map((item) => {
                    const isExpanded = expandedItems.has(item.term);
                    return (
                        <div
                            key={item.term}
                            className="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden"
                        >
                            <button
                                onClick={() => toggleExpand(item.term)}
                                className="w-full p-4 flex items-center justify-between text-left hover:bg-slate-800/50 transition-colors"
                            >
                                <div>
                                    <div className="text-white font-medium">{item.term}</div>
                                    <div className="text-sm text-slate-400">{item.shortDescription}</div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">
                                        {item.category}
                                    </span>
                                    <svg
                                        className={`w-4 h-4 text-slate-400 transition-transform ${isExpanded ? "rotate-180" : ""}`}
                                        fill="none"
                                        viewBox="0 0 24 24"
                                        stroke="currentColor"
                                    >
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                </div>
                            </button>

                            {isExpanded && (
                                <div className="px-4 pb-4 border-t border-slate-800">
                                    <div className="pt-4 space-y-4">
                                        <div className="text-slate-300 whitespace-pre-line">
                                            {item.fullDescription}
                                        </div>

                                        {item.formula && (
                                            <div className="bg-gradient-to-r from-slate-800 to-slate-800/50 rounded-lg p-4 border border-slate-700">
                                                <div className="flex items-center gap-2 text-xs text-slate-400 mb-3">
                                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.745 3A23.933 23.933 0 003 12c0 3.183.62 6.22 1.745 9M19.5 3c.967 2.78 1.5 5.817 1.5 9s-.533 6.22-1.5 9M8.25 8.885l1.444-.89a.75.75 0 011.105.402l2.402 7.206a.75.75 0 001.104.401l1.445-.889m-8.25.75l.213.09a1.687 1.687 0 002.062-.617l4.45-6.676a1.688 1.688 0 012.062-.618l.213.09" />
                                                    </svg>
                                                    Fórmula
                                                </div>
                                                <div className="flex justify-center py-2 text-emerald-400 text-lg">
                                                    <BlockMath math={item.formula} />
                                                </div>

                                                {/* Variables Legend */}
                                                {item.variables && item.variables.length > 0 && (
                                                    <div className="mt-4 pt-3 border-t border-slate-700">
                                                        <div className="text-xs text-slate-400 mb-2">Onde:</div>
                                                        <ul className="space-y-1">
                                                            {item.variables.map((v, idx) => (
                                                                <li key={idx} className="text-sm text-slate-300 flex items-start gap-2">
                                                                    <span className="text-emerald-500 mt-0.5">•</span>
                                                                    {v}
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}
                                            </div>
                                        )}

                                        {item.example && (
                                            <div className="bg-slate-800 rounded-lg p-4">
                                                <div className="text-xs text-slate-400 mb-2">Exemplo</div>
                                                <div className="text-white text-sm whitespace-pre-line">
                                                    {item.example}
                                                </div>
                                            </div>
                                        )}

                                        {item.inGastor && (
                                            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
                                                <div className="text-xs text-emerald-400 mb-2">No Gastor</div>
                                                <div className="text-emerald-300 text-sm">
                                                    {item.inGastor}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {filteredItems.length === 0 && (
                <div className="text-center py-12 text-slate-400">
                    Nenhum termo encontrado para &quot;{searchTerm}&quot;
                </div>
            )}

            {/* Tip */}
            <div className="mt-8 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
                <p className="text-sm text-slate-400">
                    <strong>Dica:</strong> Comece pelos termos &quot;Básico&quot; se você é iniciante!
                </p>
            </div>
        </div>
    );
}

// Wrapper com Suspense para useSearchParams (requerido pelo Next.js 14+)
export default function GlossaryPage() {
    return (
        <Suspense fallback={
            <div className="max-w-5xl mx-auto px-4 py-8">
                <div className="animate-pulse">
                    <div className="h-8 bg-slate-800 rounded w-1/3 mb-4"></div>
                    <div className="h-4 bg-slate-800 rounded w-1/2 mb-8"></div>
                    <div className="space-y-3">
                        {[...Array(5)].map((_, i) => (
                            <div key={i} className="h-20 bg-slate-800 rounded"></div>
                        ))}
                    </div>
                </div>
            </div>
        }>
            <GlossaryContent />
        </Suspense>
    );
}
