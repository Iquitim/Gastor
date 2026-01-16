"""
Stress Test - RSI Reversal Strategy
====================================
Testa a estratégia em múltiplos períodos para validar robustez.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Adiciona raiz do projeto ao path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.data_manager import DataManager
from src.core.indicators import calc_rsi
from src.strategies.rsi_reversal import RSIReversalStrategy
from src.core.portfolio import adjust_trade_amounts, apply_risk_management
from src.ui.tab_results import calculate_portfolio_evolution, calculate_metrics, calculate_drawdown
from src.core.config import get_total_fee

def run_backtest(df, initial_balance=1000, rsi_buy=20, rsi_sell=60, use_compound=True, sizing='volatilidade_atr'):
    """Roda backtest completo em um DataFrame."""
    
    # Aplica estratégia
    strategy = RSIReversalStrategy()
    raw_trades = strategy.apply(df, rsi_buy=rsi_buy, rsi_sell=rsi_sell)
    
    if not raw_trades:
        return None
    
    # Aplica Risk Management (Sizing)
    trades = apply_risk_management(raw_trades, df, sizing)
    
    # Ajusta amounts
    last_price = df['close'].iloc[-1]
    last_ts = df.index[-1]
    
    adjusted = adjust_trade_amounts(
        trades, initial_balance, 100, True, last_price, last_ts, use_compound
    )
    
    if not adjusted:
        return None
    
    # Calcula métricas
    evolution = calculate_portfolio_evolution(adjusted, df, initial_balance)
    if evolution.empty:
        return None
        
    metrics = calculate_metrics(adjusted, evolution, initial_balance)
    dd = calculate_drawdown(evolution)
    
    return {
        'start': df.index[0].strftime('%Y-%m-%d'),
        'end': df.index[-1].strftime('%Y-%m-%d'),
        'days': (df.index[-1] - df.index[0]).days,
        'pnl_pct': metrics['total_pnl_pct'],
        'win_rate': metrics['win_rate'],
        'trades': metrics['completed_trades'],
        'max_dd': dd['max_drawdown_pct'],
        'profit_factor': metrics['profit_factor'],
        'final_value': metrics['final_value']
    }

def main():
    print("=" * 60)
    print("STRESS TEST - RSI Reversal (rsi_buy=20, rsi_sell=60)")
    print("Modo: Juros Compostos + Sizing por Volatilidade ATR")
    print("=" * 60)
    print()
    
    # Configurações
    coin = 'SOL/USDT'
    initial_balance = 1000
    
    # Períodos de teste (diferentes janelas de tempo)
    test_periods = [
        ('90 dias (curto)', 90),
        ('120 dias (médio)', 120),
        ('180 dias (longo)', 180),
        ('365 dias (1 ano)', 365),
    ]
    
    results = []
    
    for period_name, days in test_periods:
        print(f"\n📊 Testando: {period_name}...")
        
        try:
            # Carrega dados usando DataManager
            dm = DataManager()
            df = dm.get_ccxt_historical_data(coin, '1h', days, 'binance')
            
            if df is None or df.empty:
                print(f"   ❌ Sem dados para {days} dias")
                continue
            
            # Adiciona RSI (necessário para a estratégia)
            df['rsi'] = calc_rsi(df['close'], 14)
            
            result = run_backtest(df, initial_balance)
            
            if result:
                result['period'] = period_name
                results.append(result)
                
                # Status
                status = "✅" if result['pnl_pct'] > 0 and result['max_dd'] < 10 else "⚠️"
                print(f"   {status} PnL: {result['pnl_pct']:+.2f}% | WR: {result['win_rate']:.1f}% | DD: -{result['max_dd']:.2f}% | Trades: {result['trades']}")
            else:
                print(f"   ❌ Sem trades gerados")
                
        except Exception as e:
            import traceback
            print(f"   ❌ Erro: {e}")
            traceback.print_exc()
    
    # Resumo
    if results:
        print("\n" + "=" * 60)
        print("📈 RESUMO DO STRESS TEST")
        print("=" * 60)
        
        df_results = pd.DataFrame(results)
        
        print(f"\n{'Período':<20} {'PnL %':>10} {'Win Rate':>10} {'Max DD':>10} {'Trades':>8}")
        print("-" * 60)
        
        for r in results:
            pnl_str = f"{r['pnl_pct']:+.2f}%"
            wr_str = f"{r['win_rate']:.1f}%"
            dd_str = f"-{r['max_dd']:.2f}%"
            print(f"{r['period']:<20} {pnl_str:>10} {wr_str:>10} {dd_str:>10} {r['trades']:>8}")
        
        print("-" * 60)
        
        # Estatísticas agregadas
        avg_pnl = np.mean([r['pnl_pct'] for r in results])
        min_pnl = min([r['pnl_pct'] for r in results])
        max_pnl = max([r['pnl_pct'] for r in results])
        avg_wr = np.mean([r['win_rate'] for r in results])
        worst_dd = max([r['max_dd'] for r in results])
        
        print(f"\n📊 ESTATÍSTICAS AGREGADAS:")
        print(f"   • PnL Médio: {avg_pnl:+.2f}%")
        print(f"   • PnL Mínimo: {min_pnl:+.2f}%")
        print(f"   • PnL Máximo: {max_pnl:+.2f}%")
        print(f"   • Win Rate Médio: {avg_wr:.1f}%")
        print(f"   • Pior Drawdown: -{worst_dd:.2f}%")
        
        # Avaliação FTMO
        print(f"\n🎯 AVALIAÇÃO FTMO:")
        ftmo_pass = all(r['pnl_pct'] >= 10 and r['max_dd'] < 10 for r in results)
        partial_pass = any(r['pnl_pct'] >= 10 and r['max_dd'] < 10 for r in results)
        
        if ftmo_pass:
            print("   ✅ APROVADO em TODOS os períodos testados!")
        elif partial_pass:
            passed = sum(1 for r in results if r['pnl_pct'] >= 10 and r['max_dd'] < 10)
            print(f"   ⚠️ APROVADO em {passed}/{len(results)} períodos")
        else:
            print("   ❌ REPROVADO em todos os períodos")
        
        # Risco
        print(f"\n⚠️ ANÁLISE DE RISCO:")
        if worst_dd >= 9:
            print(f"   🔴 ALERTA: Drawdown máximo de {worst_dd:.2f}% está MUITO PRÓXIMO do limite FTMO (10%)")
        elif worst_dd >= 7:
            print(f"   🟡 ATENÇÃO: Drawdown de {worst_dd:.2f}% deixa margem limitada")
        else:
            print(f"   🟢 BOM: Drawdown de {worst_dd:.2f}% deixa margem de segurança adequada")
            
        if min_pnl < 0:
            print(f"   🔴 ALERTA: Houve período com PREJUÍZO ({min_pnl:.2f}%)")
        
        # Recomendação final
        print(f"\n💡 RECOMENDAÇÃO FINAL:")
        if ftmo_pass and worst_dd < 8:
            print("   ✅ Estratégia ROBUSTA - pode prosseguir com paper trading")
        elif partial_pass:
            print("   ⚠️ Estratégia INSTÁVEL - funciona em alguns períodos mas não em outros")
            print("   → Considere ajustar parâmetros ou adicionar filtros")
        else:
            print("   ❌ Estratégia NÃO RECOMENDADA para FTMO Challenge")
            print("   → Busque otimização adicional ou estratégia diferente")

if __name__ == "__main__":
    main()
