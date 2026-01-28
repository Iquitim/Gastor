import Link from "next/link";

// Termos que devem ser linkados para o glossário
const GLOSSARY_TERMS: Record<string, string> = {
    // Indicadores
    "RSI": "RSI (Índice de Força Relativa)",
    "EMA": "EMA (Média Móvel Exponencial)",
    "SMA": "SMA (Média Móvel Simples)",
    "MACD": "MACD",
    "Stochastic": "Stochastic RSI",
    "Bollinger": "Bollinger Bands",
    "ATR": "ATR (Average True Range)",
    "Donchian": "Donchian Channel",

    // Sinais
    "sobrevendido": "Oversold / Overbought",
    "sobrecomprado": "Oversold / Overbought",
    "breakout": "Breakout / Breakdown",
    "rompimento": "Breakout / Breakdown",
    "cruzamento": "Golden Cross / Death Cross",
    "Golden Cross": "Golden Cross / Death Cross",
    "Death Cross": "Golden Cross / Death Cross",

    // Métricas
    "drawdown": "Drawdown",
    "win rate": "Win Rate",
    "profit factor": "Profit Factor",
    "PnL": "PnL (Profit and Loss)",

    // Outros
    "volatilidade": "ATR (Average True Range)",
    "momentum": "MACD",
    "tendência": "SMA (Média Móvel Simples)",
};

interface LinkedTextProps {
    text: string;
    className?: string;
}

export default function LinkedText({ text, className = "" }: LinkedTextProps) {
    // Função para criar regex case-insensitive
    const createPattern = () => {
        const terms = Object.keys(GLOSSARY_TERMS)
            .sort((a, b) => b.length - a.length) // Termos maiores primeiro
            .map(term => term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')); // Escape regex chars
        return new RegExp(`\\b(${terms.join('|')})\\b`, 'gi');
    };

    const pattern = createPattern();
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    // Reset regex state
    pattern.lastIndex = 0;

    while ((match = pattern.exec(text)) !== null) {
        // Adiciona texto antes do match
        if (match.index > lastIndex) {
            parts.push(text.slice(lastIndex, match.index));
        }

        // Encontra o termo original (case-insensitive lookup)
        const matchedText = match[0];
        const termKey = Object.keys(GLOSSARY_TERMS).find(
            key => key.toLowerCase() === matchedText.toLowerCase()
        );
        const glossaryTerm = termKey ? GLOSSARY_TERMS[termKey] : matchedText;

        // Adiciona link
        parts.push(
            <Link
                key={`${match.index}-${matchedText}`}
                href={`/glossary?search=${encodeURIComponent(glossaryTerm)}`}
                className="text-emerald-400 hover:text-emerald-300 underline decoration-dotted underline-offset-2"
                title={`Ver no glossário: ${glossaryTerm}`}
            >
                {matchedText}
            </Link>
        );

        lastIndex = pattern.lastIndex;
    }

    // Adiciona texto restante
    if (lastIndex < text.length) {
        parts.push(text.slice(lastIndex));
    }

    return <span className={className}>{parts}</span>;
}
