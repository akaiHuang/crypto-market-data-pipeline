import json
import glob
import os
import pandas as pd
from datetime import datetime

LOG_DIR = "logs/whale_paper_trader"

def predict_profit():
    # 1. Load Data to calculate Frequency
    files = glob.glob(os.path.join(LOG_DIR, "trades_*.json"))
    files.sort(key=os.path.getmtime, reverse=True)
    recent_files = files[:10]
    
    all_trades = []
    for f in recent_files:
        try:
            with open(f, 'r') as file:
                data = json.load(file)
                trades = data.get('trades', [])
                all_trades.extend(trades)
        except: pass
        
    if not all_trades: return

    df = pd.DataFrame(all_trades)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Calculate Total Hours Analyzed (Range of timestamps)
    total_hours = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600
    if total_hours < 0.1: total_hours = 1 # Avoid div by zero for single burst
    
    print(f"📊 DATA BASIS")
    print(f"   Analyzed History: {total_hours:.1f} hours")
    print(f"   Total Trades:     {len(df)}")
    
    # --- SCENARIO 1: Binance Optimized (Swing > 1m) ---
    # Filter: Hold > 60s
    swing_trades = df[df['hold_seconds'] > 60]
    swing_count = len(swing_trades)
    swing_freq = swing_count / total_hours
    
    # Avg Gross PnL for Swings
    swing_gross_avg = swing_trades['pnl_pct'].mean() if not swing_trades.empty else 0
    
    # Binance Fees (50x)
    # Fee Rate: 0.04% (Taker) or 0.02% (Maker). Let's assume mix 0.03%
    # Fee on Margin = 0.03% * 50 * 2 = 3.0%
    binance_fee_cost = 0.03 * 50 * 2 
    
    swing_net_avg = swing_gross_avg - binance_fee_cost
    
    # Projection 8h
    b_trades_8h = swing_freq * 8
    b_total_pnl = b_trades_8h * swing_net_avg
    b_final_capital = 100 * (1 + b_total_pnl/100) # Simple interest approx for short duration
    
    # --- SCENARIO 2: dYdX Zero Fee (Scalping < 1m) ---
    # Filter: All trades (since high freq includes scalps) or just Scalps < 60s
    # The user would likely run the scalping strategy
    scalp_trades = df[df['hold_seconds'] <= 60]
    scalp_count = len(scalp_trades)
    scalp_freq = scalp_count / total_hours
    
    # Avg Gross PnL for Scalps (This is Net on dYdX)
    scalp_gross_avg = scalp_trades['pnl_pct'].mean() if not scalp_trades.empty else 0
    dydx_fee_cost = 0.0
    
    scalp_net_avg = scalp_gross_avg - dydx_fee_cost
    
    # Projection 8h
    d_trades_8h = scalp_freq * 8
    d_total_pnl = d_trades_8h * scalp_net_avg
    d_final_capital = 100 * (1 + d_total_pnl/100)

    print(f"\n🔮 PROFITS PROJECTION (8 Hours, $100 Start, 50x Leverage)")
    print("=" * 60)
    
    print(f"1. Binance Optimized (Swing > 1m)")
    print(f"   Strategy:       Low Frequency, Quality Signals")
    print(f"   Trades/Hour:    {swing_freq:.1f}")
    print(f"   Est Trades:     {int(b_trades_8h)}")
    print(f"   Avg Gross PnL:  +{swing_gross_avg:.2f}%")
    print(f"   Fee Cost (50x): -{binance_fee_cost:.2f}% (Est. 0.03% avg)")
    print(f"   Avg Net PnL:    {swing_net_avg:.2f}%")
    if swing_net_avg > 0:
        print(f"   💰 Est Profit:   +${(b_final_capital - 100):.2f}")
        print(f"   💵 Final Balance: ${b_final_capital:.2f}")
    else:
        print(f"   💸 Est Loss:     -${(100 - b_final_capital):.2f}")
        print(f"   ⚠️ Risk: Fees might eat all profits unless Swing PnL > 3%.")

    print(f"\n2. dYdX Zero Fee (Scalping < 1m)")
    print(f"   Strategy:       High Frequency, Noise Harvesting")
    print(f"   Trades/Hour:    {scalp_freq:.1f}")
    print(f"   Est Trades:     {int(d_trades_8h)}")
    print(f"   Avg Gross PnL:  +{scalp_gross_avg:.2f}%")
    print(f"   Fee Cost:       $0.00")
    print(f"   Avg Net PnL:    +{scalp_net_avg:.2f}%")
    
    # Compound interest might be huge here, but keeping simple for comparison
    d_final_capital_compound = 100 * ((1 + scalp_net_avg/100) ** int(d_trades_8h))
    
    print(f"   💰 Est Profit:   +${(d_final_capital - 100):.2f} (Simple)")
    if d_final_capital_compound < 10000: # Sanity check output
        print(f"   🚀 Est Profit:   +${(d_final_capital_compound - 100):.2f} (Compounded!)")
    else:
        print(f"   🚀 Est Profit:   > +$1,000.00 (Compounded - Theoretical)")
        
    print(f"   💵 Final Balance: ${max(d_final_capital, d_final_capital_compound):.2f}")

if __name__ == "__main__":
    predict_profit()
