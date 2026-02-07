#!/usr/bin/env python3
"""
📊 市場結構分析 + 動態交易參數建議
根據市場趨勢週期自動計算最佳持倉時間和獲利目標
"""

import requests
import json
from datetime import datetime
from pathlib import Path

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

def calculate_ema(closes, period=20):
    if len(closes) < period:
        return []
    
    alpha = 2 / (period + 1)
    ema = [sum(closes[:period]) / period]
    
    for i in range(period, len(closes)):
        val = (closes[i] * alpha) + (ema[-1] * (1 - alpha))
        ema.append(val)
        
    return [None] * (period - 1) + ema

def analyze_trend_stats(interval: str, limit: int = 500, verbose: bool = True):
    """分析特定時間框架的趨勢統計"""
    klines = get_json(f"{TESTNET_BASE_URL}/fapi/v1/klines", {"symbol": SYMBOL, "interval": interval, "limit": limit})
    if not klines or len(klines) < 50:
        return None

    closes = [float(k[4]) for k in klines]
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines]
    
    ema20 = calculate_ema(closes, 20)
    
    trends = []
    current_trend = None
    
    for i in range(20, len(closes)):
        price = closes[i]
        ema = ema20[i]
        if ema is None: continue
        
        trend_type = "LONG" if price > ema else "SHORT"
        
        if current_trend is None:
            current_trend = {
                'type': trend_type,
                'start_idx': i,
                'start_price': price,
                'high_price': price,
                'low_price': price
            }
        elif current_trend['type'] != trend_type:
            current_trend['end_idx'] = i - 1
            current_trend['end_price'] = closes[i-1]
            current_trend['max_move'] = (current_trend['high_price'] - current_trend['start_price']) / current_trend['start_price'] * 100 if current_trend['type'] == 'LONG' else (current_trend['start_price'] - current_trend['low_price']) / current_trend['start_price'] * 100
            trends.append(current_trend)
            
            current_trend = {
                'type': trend_type,
                'start_idx': i,
                'start_price': price,
                'high_price': price,
                'low_price': price
            }
        else:
            current_trend['high_price'] = max(current_trend['high_price'], price)
            current_trend['low_price'] = min(current_trend['low_price'], price)

    if current_trend:
        current_trend['end_idx'] = len(closes) - 1
        current_trend['end_price'] = closes[-1]
        current_trend['max_move'] = (current_trend['high_price'] - current_trend['start_price']) / current_trend['start_price'] * 100 if current_trend['type'] == 'LONG' else (current_trend['start_price'] - current_trend['low_price']) / current_trend['start_price'] * 100
        trends.append(current_trend)
        
    # 計算統計
    longs = [t for t in trends if t['type'] == 'LONG']
    shorts = [t for t in trends if t['type'] == 'SHORT']
    
    def calc_stats(trend_list):
        if not trend_list: return {'count': 0, 'avg_duration': 0, 'avg_move': 0, 'max_move': 0, 'p75_move': 0}
        durations = [t['end_idx'] - t['start_idx'] + 1 for t in trend_list]
        moves = [t.get('max_move', 0) for t in trend_list]
        
        sorted_moves = sorted(moves)
        p75_idx = int(len(sorted_moves) * 0.75)
        
        return {
            'count': len(trend_list),
            'avg_duration': sum(durations) / len(durations),
            'avg_move': sum(moves) / len(moves),
            'max_move': max(moves) if moves else 0,
            'p75_move': sorted_moves[p75_idx] if sorted_moves else 0  # 75 percentile
        }

    # 時間單位 (分鐘)
    unit_min = {'1m': 1, '5m': 5, '15m': 15, '30m': 30, '1h': 60}.get(interval, 1)
    
    long_stats = calc_stats(longs)
    short_stats = calc_stats(shorts)
    
    if verbose:
        print(f"\n📊 {interval} 時間框架趨勢分析")
        print(f"   🟢 多頭: {long_stats['count']} 次 | 平均 {long_stats['avg_duration']:.1f} 根 ({long_stats['avg_duration'] * unit_min:.1f} 分鐘) | 幅度 +{long_stats['avg_move']:.3f}%")
        print(f"   🔴 空頭: {short_stats['count']} 次 | 平均 {short_stats['avg_duration']:.1f} 根 ({short_stats['avg_duration'] * unit_min:.1f} 分鐘) | 幅度 -{short_stats['avg_move']:.3f}%")
    
    return {
        'interval': interval,
        'unit_min': unit_min,
        'long': long_stats,
        'short': short_stats,
        'avg_cycle_min': (long_stats['avg_duration'] + short_stats['avg_duration']) / 2 * unit_min,
        'volatility': (long_stats['avg_move'] + short_stats['avg_move']) / 2
    }

def get_current_market_state():
    """獲取當前市場狀態"""
    # 獲取最近6小時數據 (72個5分鐘K線)
    klines = get_json(f"{TESTNET_BASE_URL}/fapi/v1/klines", {"symbol": SYMBOL, "interval": "5m", "limit": 72})
    if not klines:
        return None
    
    closes = [float(k[4]) for k in klines]
    current_price = closes[-1]
    
    # RSI 計算
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(diff if diff > 0 else 0)
        losses.append(abs(diff) if diff < 0 else 0)
    
    avg_gain = sum(gains[-14:]) / 14
    avg_loss = sum(losses[-14:]) / 14
    rsi = 100 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss))
    
    # 6小時變化
    change_6h = (closes[-1] - closes[0]) / closes[0] * 100
    
    # 1小時變化
    change_1h = (closes[-1] - closes[-12]) / closes[-12] * 100
    
    return {
        'price': current_price,
        'rsi': rsi,
        'change_6h': change_6h,
        'change_1h': change_1h
    }

def calculate_optimal_params(stats_1m, stats_5m, market_state):
    """
    根據市場結構計算最佳交易參數
    
    邏輯：
    1. 持倉時間 = 趨勢週期的 50-70%（在趨勢結束前出場）
    2. 獲利目標 = 平均趨勢幅度的 60-80%（保守獲利）
    3. 根據 RSI 調整：超買/超賣時更保守
    """
    
    # 使用 1m 和 5m 的平均值
    avg_cycle_sec = (stats_1m['avg_cycle_min'] + stats_5m['avg_cycle_min']) / 2 * 60  # 轉換為秒
    avg_move = (stats_1m['volatility'] + stats_5m['volatility']) / 2
    
    # 基礎參數
    base_hold_sec = avg_cycle_sec * 0.6  # 趨勢週期的 60%
    base_target_pct = avg_move * 0.7  # 平均幅度的 70%
    
    # RSI 調整因子
    rsi = market_state['rsi']
    if rsi > 70 or rsi < 30:
        # 超買/超賣：縮短持倉、降低目標
        rsi_factor = 0.7
    elif rsi > 60 or rsi < 40:
        rsi_factor = 0.85
    else:
        rsi_factor = 1.0
    
    # 波動率調整
    if avg_move < 0.05:
        # 低波動：需要更長時間
        vol_factor = 1.3
    elif avg_move > 0.2:
        # 高波動：縮短時間、提高目標
        vol_factor = 0.8
    else:
        vol_factor = 1.0
    
    # 最終計算
    optimal_hold_sec = base_hold_sec * rsi_factor * vol_factor
    optimal_target_pct = base_target_pct * rsi_factor
    
    # 100X 槓桿下的實際目標（考慮 4% 手續費）
    # 要獲利，毛利必須 > 4%，所以目標 = 4% + 實際想賺的
    leverage = 100
    fee_pct = 4.0  # 100X 槓桿 Maker 手續費 (0.02% * 2 sides * 100X)
    
    # 價格需要變動多少才能達到目標淨利
    price_move_needed = (optimal_target_pct + fee_pct) / leverage
    
    # 止損（風險報酬 1:1.5）
    stop_loss_pct = optimal_target_pct / 1.5
    
    # 最小持倉時間保護 (至少60秒避免假信號)
    optimal_hold_sec = max(optimal_hold_sec, 60)
    
    return {
        'optimal_hold_sec': optimal_hold_sec,
        'optimal_hold_min': optimal_hold_sec / 60,
        'target_net_pct': optimal_target_pct,
        'target_gross_pct': optimal_target_pct + fee_pct,
        'price_move_needed_pct': price_move_needed,
        'stop_loss_pct': max(stop_loss_pct, 5.0),  # 最低5%止損
        'rsi_factor': rsi_factor,
        'vol_factor': vol_factor,
        'market_cycle_min': avg_cycle_sec / 60,
        'market_avg_move': avg_move
    }

def save_dynamic_config(params, market_state):
    """保存動態配置到 JSON"""
    config_path = Path("config/dynamic_trading_params.json")
    
    config = {
        '_comment': '根據市場結構自動生成的動態交易參數',
        '_generated': datetime.now().isoformat(),
        'market_state': {
            'price': round(market_state['price'], 2),
            'rsi': round(market_state['rsi'], 1),
            'change_6h_pct': round(market_state['change_6h'], 3),
            'change_1h_pct': round(market_state['change_1h'], 3)
        },
        'recommended_params': {
            'min_hold_seconds': round(params['optimal_hold_sec']),
            'optimal_hold_minutes': round(params['optimal_hold_min'], 1),
            'target_net_profit_pct': round(params['target_net_pct'], 2),
            'target_gross_profit_pct': round(params['target_gross_pct'], 2),
            'price_move_target_pct': round(params['price_move_needed_pct'], 4),
            'stop_loss_pct': round(params['stop_loss_pct'], 2)
        },
        'market_analysis': {
            'avg_trend_cycle_minutes': round(params['market_cycle_min'], 1),
            'avg_trend_magnitude_pct': round(params['market_avg_move'], 4)
        },
        'adjustment_factors': {
            'rsi_factor': params['rsi_factor'],
            'volatility_factor': params['vol_factor']
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    return config_path

def main():
    print("=" * 70)
    print("📊 市場結構分析 + 動態交易參數建議")
    print("=" * 70)
    
    # 分析不同時間框架
    print("\n🔍 分析趨勢週期...")
    stats_1m = analyze_trend_stats("1m", 1000)
    stats_5m = analyze_trend_stats("5m", 500)
    stats_30m = analyze_trend_stats("30m", 200)
    
    if not stats_1m or not stats_5m:
        print("❌ 無法獲取市場數據")
        return
    
    # 顯示週期摘要
    print(f"\n⏱️ 趨勢週期摘要:")
    print(f"   1m 週期: {stats_1m['avg_cycle_min']:.1f} 分鐘 | 幅度: {stats_1m['volatility']:.3f}%")
    print(f"   5m 週期: {stats_5m['avg_cycle_min']:.1f} 分鐘 | 幅度: {stats_5m['volatility']:.3f}%")
    if stats_30m:
        print(f"  30m 週期: {stats_30m['avg_cycle_min']:.1f} 分鐘 | 幅度: {stats_30m['volatility']:.3f}%")
    
    # 獲取當前市場狀態
    print("\n🎯 當前市場狀態...")
    market_state = get_current_market_state()
    if market_state:
        print(f"   價格: ${market_state['price']:,.2f}")
        print(f"   RSI: {market_state['rsi']:.1f}")
        print(f"   6h 變化: {market_state['change_6h']:+.3f}%")
        print(f"   1h 變化: {market_state['change_1h']:+.3f}%")
    else:
        market_state = {'price': 0, 'rsi': 50, 'change_6h': 0, 'change_1h': 0}
    
    # 計算最佳參數
    print("\n" + "=" * 70)
    print("💡 建議交易參數 (100X 槓桿)")
    print("=" * 70)
    
    params = calculate_optimal_params(stats_1m, stats_5m, market_state)
    
    print(f"\n⏱️ 持倉時間建議:")
    print(f"   最小持倉: {params['optimal_hold_sec']:.0f} 秒 ({params['optimal_hold_min']:.1f} 分鐘)")
    print(f"   市場週期: {params['market_cycle_min']:.1f} 分鐘 (持倉約週期的 60%)")
    
    print(f"\n📊 獲利目標建議:")
    print(f"   淨利目標: +{params['target_net_pct']:.2f}% (扣除手續費後)")
    print(f"   毛利目標: +{params['target_gross_pct']:.2f}% (含 4% 手續費)")
    print(f"   價格需漲: {params['price_move_needed_pct']:.4f}%")
    
    print(f"\n🛡️ 止損建議:")
    print(f"   止損線: -{params['stop_loss_pct']:.2f}%")
    actual_rr = params['target_net_pct'] / params['stop_loss_pct'] if params['stop_loss_pct'] > 0 else 0
    if actual_rr < 0.5:
        print(f"   ⚠️ 風險報酬: 1:{actual_rr:.2f} (風險過高！)")
        print(f"   → 100X 下手續費吃掉大部分利潤，建議降低槓桿")
    else:
        print(f"   風險報酬: 1:{actual_rr:.1f}")
    
    print(f"\n📝 調整因子:")
    rsi_note = "(超買/超賣，保守)" if params['rsi_factor'] < 1 else "(正常)"
    vol_note = "(低波動，延長)" if params['vol_factor'] > 1 else "(高波動，縮短)" if params['vol_factor'] < 1 else "(正常)"
    print(f"   RSI 因子: {params['rsi_factor']:.2f} {rsi_note}")
    print(f"   波動因子: {params['vol_factor']:.2f} {vol_note}")
    
    # 保存配置
    config_path = save_dynamic_config(params, market_state)
    print(f"\n✅ 配置已保存: {config_path}")
    
    # 實際建議
    print("\n" + "=" * 70)
    print("🎯 實際操作建議")
    print("=" * 70)
    
    if params['market_avg_move'] < 0.08:
        print("\n⚠️ 當前市場波動較低 (趨勢幅度 < 0.08%)")
        print("   → 建議：減少交易頻率，等待更明確趨勢")
        print("   → 或者：降低槓桿至 50X 減少手續費影響")
    elif params['market_avg_move'] > 0.15:
        print("\n🚀 當前市場波動較高 (趨勢幅度 > 0.15%)")
        print("   → 建議：可適度增加倉位")
        print("   → 注意：設置嚴格止損防止大虧")
    else:
        print("\n✅ 當前市場波動正常")
        print("   → 建議：按照上述參數執行")
    
    if market_state['rsi'] > 65:
        print(f"\n⚠️ RSI {market_state['rsi']:.0f} 偏高")
        print("   → 做多要謹慎，考慮等回調")
    elif market_state['rsi'] < 35:
        print(f"\n⚠️ RSI {market_state['rsi']:.0f} 偏低")
        print("   → 做空要謹慎，考慮等反彈")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
