import requests
import time
import statistics
from datetime import datetime

# Configuration
TESTNET_BASE_URL = "https://testnet.binancefuture.com"
SYMBOL = "BTCUSDT"

def get_json(url, params=None):
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"⚠️ Exception fetching {url}: {e}")
    return None

def calculate_atr(klines, period=14):
    # kline: [time, open, high, low, close, ...]
    # TR = Max(H-L, |H-Cp|, |L-Cp|)
    if len(klines) < period + 1: return 0
    
    trs = []
    for i in range(1, len(klines)):
        high = float(klines[i][2])
        low = float(klines[i][3])
        prev_close = float(klines[i-1][4])
        
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
        
    # Simple average for this demo (Wilder's smoothing is standard but SMA is close enough for checking magnitude)
    return sum(trs[-period:]) / period

def get_advanced_metrics():
    print(f"\n🔍 Fetching Advanced Metrics for {SYMBOL}...")
    
    # 1. Volatility (ATR) - Determines "How much price moves in 5 mins"
    # Helps set Profit Target (e.g. Target = 3 * ATR)
    klines = get_json(f"{TESTNET_BASE_URL}/fapi/v1/klines", {"symbol": SYMBOL, "interval": "5m", "limit": 20})
    atr_5m = 0
    if klines:
        atr_5m = calculate_atr(klines, 14)
        print(f"   📊 ATR (5m):      ${atr_5m:.2f}")
        print(f"      -> Expected Move per 5m candle: ±{atr_5m:.2f} USDT")
        print(f"      -> Suggested Target (3 candles): ${(atr_5m * 3):.2f}")
        
    # 2. Funding Rate - Determines "Sentiment / Crowdedness"
    # High Positive = Everyone Long = Potential Reversal Soon (Short Hold Time)
    funding = get_json(f"{TESTNET_BASE_URL}/fapi/v1/premiumIndex", {"symbol": SYMBOL})
    if funding:
        fr = float(funding['lastFundingRate'])
        print(f"   💰 Funding Rate:  {fr*100:.4f}%")
        if abs(fr) > 0.01:
            print("      -> High Funding! Trend might reverse soon (Shorten Hold Time).")
        else:
            print("      -> Normal Funding. Trend could be stable.")

    # 3. Open Interest - Determines "Trend Strength"
    # Rising OI + Price Move = Strong Trend (Long Hold Time)
    # Dropping OI + Price Move = Weak Trend (Profit Taking)
    oi_data = get_json(f"{TESTNET_BASE_URL}/fapi/v1/openInterest", {"symbol": SYMBOL})
    if oi_data:
        oi = float(oi_data['openInterest']) # Amount in BTC usually or USDT
        print(f"   📈 Open Interest: {oi:,.1f} BTC")
        print("      -> Check if this is rising vs 1 hour ago (requires history) to confirm trend strength.")

    # 4. Long/Short Ratio (Top Trader) - Sentiment
    # Testnet availability varies, let's try
    ls_ratio = get_json(f"{TESTNET_BASE_URL}/fapi/v1/topLongShortAccountRatio", {"symbol": SYMBOL, "period": "5m", "limit": 1})
    if ls_ratio and len(ls_ratio) > 0:
        ratio = float(ls_ratio[0]['longShortRatio'])
        print(f"   ⚖️ L/S Ratio:     {ratio:.2f}")
        if ratio > 2.0:
            print("      -> Retail is heavily Long. Contrarian Short might work.")
    else:
        print("   ⚖️ L/S Ratio:     Not available on Testnet/Endpoint")

    print("\n✅ Verification Complete.")

if __name__ == "__main__":
    get_advanced_metrics()
