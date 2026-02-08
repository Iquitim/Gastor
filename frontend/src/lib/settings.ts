export interface StoredSettings {
    customFee?: number;
    initialBalance: number;
    useCompound: boolean;
    // Paper Trading settings
    paperTradingBalance: number;
    paperTradingCoin: string;
    paperTradingTimeframe: string;
    telegramChatId: string;
}

export const getStoredSettings = (coin?: string): StoredSettings => {
    let customFee: number | undefined = undefined;
    let initialBalance = 10000;
    let useCompound = true;
    // Paper Trading defaults
    let paperTradingBalance = 10000;
    let paperTradingCoin = "SOL/USDT";
    let paperTradingTimeframe = "1h";
    let telegramChatId = "";

    // Check if running in browser
    if (typeof window === 'undefined') {
        return { initialBalance, useCompound, paperTradingBalance, paperTradingCoin, paperTradingTimeframe, telegramChatId };
    }

    try {
        const savedSettings = localStorage.getItem("gastor_settings");
        if (savedSettings) {
            const parsed = JSON.parse(savedSettings);
            if (parsed.initialBalance) initialBalance = parsed.initialBalance;
            if (parsed.useCompound !== undefined) useCompound = parsed.useCompound;
            // Paper Trading
            if (parsed.paperTradingBalance) paperTradingBalance = parsed.paperTradingBalance;
            if (parsed.paperTradingCoin) paperTradingCoin = parsed.paperTradingCoin;
            if (parsed.paperTradingTimeframe) paperTradingTimeframe = parsed.paperTradingTimeframe;
            if (parsed.telegramChatId) telegramChatId = parsed.telegramChatId;

            // Fee Calculation (New Structure)
            if (coin && parsed.exchangeFee !== undefined) {
                const exchangeFee = parsed.exchangeFee;
                let slippage = 0;

                if (parsed.slippageOverrides && parsed.slippageOverrides[coin] !== undefined) {
                    slippage = parsed.slippageOverrides[coin];
                } else {
                    // Default Backend Slippage Values (Conservative Estimates)
                    const defaults: Record<string, number> = {
                        "BTC/USDT": 0.001,   // 0.10%
                        "ETH/USDT": 0.0012,  // 0.12%
                        "SOL/USDT": 0.0015,  // 0.15%
                        "XRP/USDT": 0.0012,  // 0.12%
                        "DOGE/USDT": 0.002,  // 0.20%
                        "AVAX/USDT": 0.0025  // 0.25%
                    };
                    // Default fallback for unknown coins is 0.3% (0.003)
                    slippage = defaults[coin] !== undefined ? defaults[coin] : 0.003;
                }
                customFee = exchangeFee + slippage;
            }
            // Backward compatibility (Old 'coins' structure)
            else if (coin && parsed.coins) {
                const coinCfg = parsed.coins[coin];
                if (coinCfg && coinCfg.enabled) {
                    // Fee + Slippage in decimal
                    customFee = (coinCfg.fee + coinCfg.slippage) / 100;
                }
            }
        }
    } catch (e) {
        console.error("Error reading settings", e);
    }

    return { customFee, initialBalance, useCompound, paperTradingBalance, paperTradingCoin, paperTradingTimeframe, telegramChatId };
};
