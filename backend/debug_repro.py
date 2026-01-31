
import asyncio
import sys
import pandas as pd
from core.data_loader import get_market_data
from core.backtest import BacktestEngine

# Hardcoded params from user screenshot/context
COIN = "SOL/USDT"
DAYS = 90
TIMEFRAME = "1h"
INITIAL_BALANCE = 10000
USE_COMPOUND = True # Testing with Compound ON per recent changes
FEE_RATE = 0.0025   # Standard fee

STRATEGY_SLUG = "rsi_reversal"
PARAMS = {
    "rsi_period": 20,
    "rsi_buy": 30,
    "rsi_sell": 60
}

async def main():
    print(f"--- STARTING DETERMINISM TEST ---")
    print(f"Coin: {COIN}, Days: {DAYS}, Timeframe: {TIMEFRAME}")
    
    # 1. Fetch Data ONCE (to rule out fetch variance for now)
    print("Fetching data...")
    market_data = await get_market_data(COIN, DAYS, TIMEFRAME)
    data = market_data["data"]
    
    if not data:
        print("ERROR: No data found.")
        return

    print(f"Data Loaded: {len(data)} candles. Start: {data[0]['time']} End: {data[-1]['time']}")

    previous_pnl = None
    
    print("\n--- RUNNING 5 CONSECUTIVE BACKTESTS (Single Strategy) ---")
    for i in range(1, 6):
        engine = BacktestEngine(data, INITIAL_BALANCE, fee_rate=FEE_RATE, use_compound=USE_COMPOUND)
        result = engine.run(STRATEGY_SLUG, PARAMS)
        
        pnl = result['metrics']['total_pnl_pct']
        trades = result['metrics']['total_trades']
        final_bal = result['metrics']['final_balance']
        
        status = "OK"
        if previous_pnl is not None and abs(previous_pnl - pnl) > 1e-9:
            status = "MISMATCH !!!"
        
        print(f"Run #{i}: PnL={pnl:.4f}% | Trades={trades} | Balance={final_bal:.2f} | {status}")
        previous_pnl = pnl

    print("\n--- RUNNING OPTIMIZER LOGIC SIMULATION ---")
    # Simulate what happens in optimizer.py loop for this strategy
    # We will run a mini grid search check
    
    from itertools import product
    
    # Tiny grid around the target params to see if neighbor values create instability
    rsi_periods = [19, 20, 21]
    
    for _ in range(3): # Repeat the grid search 3 times
        print(f"--- Optimization Cycle ---")
        best_pnl = -9999
        best_params = {}
        
        for period in rsi_periods:
            test_params = PARAMS.copy()
            test_params["rsi_period"] = period
            
            engine = BacktestEngine(data, INITIAL_BALANCE, fee_rate=FEE_RATE, use_compound=USE_COMPOUND)
            res = engine.run(STRATEGY_SLUG, test_params)
            
            curr_pnl = res['metrics']['total_pnl_pct']
            if curr_pnl > best_pnl:
                best_pnl = curr_pnl
                best_params = test_params
            
        print(f"Best Found: PnL={best_pnl:.4f}% Params={best_params}")

if __name__ == "__main__":
    asyncio.run(main())
