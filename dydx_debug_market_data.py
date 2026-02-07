#!/usr/bin/env python3
"""
📊 dYdX 市場結構分析工具
使用 dYdX v4 API 獲取數據並進行分析
"""

import asyncio
import sys
import os
import pandas as pd
from datetime import datetime

# Add root directory to path to allow importing dydx module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from dydx.dydx_trader import DydxTrader
except ImportError:
    print("⚠️  無法導入 dYdX 模組，請確保已安裝 dydx-v4-client 並位於正確目錄")
    sys.exit(1)

MARGIN_SYMBOL = "BTC-USD"

async def analyze_dydx_market():
    print("==================================================")
    print(f"📈 dYdX 市場結構分析 ({MARGIN_SYMBOL})")
    print("==================================================")
    
    trader = DydxTrader()
    await trader.connect()
    
    # 1. 獲取基本價格與市場數據
    print("\n🔍 獲取即時數據...")
    market = await trader.get_market(MARGIN_SYMBOL)
    if not market:
        print("❌ 無法獲取市場數據")
        return

    price = float(market.get('oraclePrice', 0))
    vol_24h = float(market.get('volume24H', 0))
    # nextFundingRate is a decimal, e.g. 0.0001
    funding = float(market.get('nextFundingRate', 0)) * 100
    oi = float(market.get('openInterest', 0))
    
    # 2. 獲取訂單簿計算 OBI
    obi = 0
    orderbook = await trader.get_orderbook(MARGIN_SYMBOL)
    if orderbook:
        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])
        
        # 只取前 20 檔或更深
        bid_vol = sum(float(b['size']) for b in bids)
        ask_vol = sum(float(a['size']) for a in asks)
        
        if (bid_vol + ask_vol) > 0:
            obi = (bid_vol - ask_vol) / (bid_vol + ask_vol)

    # 3. 獲取 K 線 (1MIN, 5MIN, 30MIN)
    # dYdX resolutions: 1MIN, 5MIN, 15MIN, 30MIN, 1HOUR, 4HOURS
    print("\n📊 分析趨勢結構...")
    
    async def get_stats(res, limit=100):
        candles = await trader.get_candles(MARGIN_SYMBOL, resolution=res, limit=limit)
        if not candles or not candles.get("candles"):
            return None
        
        # Candles come new to old usually? dYdX specific check needed. 
        # Standard dYdX response is usually reverse chronological, index 0 is latest.
        # But let's verify by checking timestamps if implementing strictly.
        # Assuming index 0 is NEWEST.
        data = candles["candles"]
        
        # Sort by time ascending
        data.sort(key=lambda x: x['startedAt'])
        
        closes = [float(c['close']) for c in data]
        
        # Price Change
        change = (closes[-1] - closes[0]) / closes[0] * 100
        
        # RSI 14
        if len(closes) > 14:
            gains = []
            losses = []
            for i in range(1, len(closes)):
                diff = closes[i] - closes[i-1]
                gains.append(max(diff, 0))
                losses.append(abs(min(diff, 0)))
            
            avg_gain = sum(gains[-14:]) / 14
            avg_loss = sum(losses[-14:]) / 14
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
        else:
            rsi = 50
            
        return {
            'change': change,
            'rsi': rsi,
            'closes': closes
        }

    stats_1m = await get_stats("1MIN", 60)   # 1小時
    stats_5m = await get_stats("5MINS", 72)   # 6小時
    stats_30m = await get_stats("30MINS", 48) # 24小時
    
    # 4. 報告
    print(f"\n📊 DATA SNAPSHOT:")
    print(f"   • Price:       ${price:,.2f}")
    print(f"   • OBI:         {obi:+.3f}  (>0.3 Bullish, <-0.3 Bearish)")
    print(f"   • Funding:     {funding:.4f}%")
    print(f"   • OI:          {oi:,.2f}")
    
    if stats_1m:
        print(f"   • RSI (1m):    {stats_1m['rsi']:.1f}")
        print(f"   • Change 1h:   {stats_1m['change']:+.3f}% (1m candles)")
        
    if stats_5m:
        print(f"   • RSI (5m):    {stats_5m['rsi']:.1f}")
        print(f"   • Change 6h:   {stats_5m['change']:+.3f}% (5m candles)")
        
    # 5. 趨勢判斷
    print(f"\n🤖 dYdX SYSTEM TRIGGER CHECK:")
    
    obi_status = "NEUTRAL"
    if obi > 0.3: obi_status = "🟢 BULLISH"
    elif obi < -0.3: obi_status = "🔴 BEARISH"
    
    print(f"   1. Order Book:   {obi_status} ({obi:.3f})")
    
    # 動量檢查 (5分線最後一根的變化)
    if stats_5m and len(stats_5m['closes']) >= 2:
        last_close = stats_5m['closes'][-1]
        prev_close = stats_5m['closes'][-2]
        mom_change = (last_close - prev_close) / prev_close * 100
        
        mom_status = "NEUTRAL"
        if abs(mom_change) > 0.05:
            mom_status = "✅ ACTIVE"
        else:
            mom_status = "⚠️ FLAT"
            
        print(f"   2. Momentum:     {mom_status} ({mom_change:+.3f}%)")
    
    print("\n✅ Verification Complete.")

if __name__ == "__main__":
    asyncio.run(analyze_dydx_market())
