export interface StoredSettings {
    customFee?: number;
    initialBalance: number;
    useCompound: boolean;
}

export const getStoredSettings = (coin?: string): StoredSettings => {
    let customFee: number | undefined = undefined;
    let initialBalance = 10000;
    let useCompound = true;

    // Check if running in browser
    if (typeof window === 'undefined') return { initialBalance, useCompound };

    try {
        const savedSettings = localStorage.getItem("gastor_settings");
        if (savedSettings) {
            const parsed = JSON.parse(savedSettings);
            if (parsed.initialBalance) initialBalance = parsed.initialBalance;
            if (parsed.useCompound !== undefined) useCompound = parsed.useCompound;

            if (coin && parsed.coins) {
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

    return { customFee, initialBalance, useCompound };
};
