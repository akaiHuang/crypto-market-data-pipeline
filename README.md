# Crypto Market Data Pipeline

## About

Crypto Market Data Pipeline 是一套面向量化研究的市場數據管線，負責擷取、清洗與儲存交易所 K 線等時間序列資料。適合用於建立可重現的研究資料底座，支援回測、因子研究與資料品質監控。

## About (EN)

Crypto Market Data Pipeline is a production-oriented data pipeline for collecting, cleaning, and storing multi-exchange market time series. It provides a reproducible data foundation for backtesting, quantitative research, and data quality operations.

## 📋 Quick Summary

> 📊 **Crypto Market Data Pipeline** 是一套生產級加密貨幣市場數據管線，專為量化交易研究打造。💹 已成功擷取並處理超過 **310 萬筆 K 線數據**，涵蓋 Binance Futures 與 dYdX v4 兩大交易所，時間跨度近 6 年（2019-2025）。🔬 核心模組包含市場結構分析（EMA/RSI 趨勢週期）、進階微觀結構指標（ATR 波動率、資金費率、未平倉量）、以及利潤預測引擎。🤖 整合 XGBoost、LightGBM、scikit-learn 等機器學習框架與 Optuna 超參數優化，支援策略回測與部署。📈 數據資產涵蓋 28+ 結構化數據集，包括鯨魚追蹤、清算壓力、技術信號品質評估等。⚙️ 技術棧涵蓋 Python、pandas、FastAPI、Celery 任務佇列及 Prometheus 監控。🎯 適合量化交易員、數據科學家、以及需要大規模歷史數據進行演算法交易策略研究的團隊！

### 3.1M K-Line Data Engineering at Scale

> Production-grade pipeline for ingesting, processing, and analyzing massive cryptocurrency market data across multiple exchanges and timeframes.

---

## 💡 Why This Exists

Quantitative crypto trading demands comprehensive historical data -- not sample datasets, but millions of data points spanning years of market cycles. Most publicly available tools handle toy-scale data. This pipeline was built to ingest and process **3.1 million+ K-line records** across multiple exchanges (Binance, dYdX) and timeframes, transforming raw market feeds into analysis-ready datasets for strategy research and live trading systems.

The result: a complete data foundation for building, backtesting, and deploying algorithmic trading strategies with statistical confidence.

---

## 🏗️ Architecture

```
Exchange APIs (Binance Futures, dYdX v4)
              |
     Rate-Limited Ingestion
              |
   +----------+----------+
   |          |          |
 1m K-lines  5m       30m        <-- Multi-timeframe collection
   |          |          |
   +----------+----------+
              |
     Data Validation & Storage
              |
   +----------+----------+----------+
   |          |          |          |
 Market      Trend      Profit     Advanced
 Structure   Analysis   Prediction Metrics
 Analysis    (EMA/RSI)  (ML-ready) (ATR/OBI/Funding)
```

### Core Modules

| Module | Purpose |
|--------|---------|
| `debug_market_data.py` | Market structure analysis with dynamic trading parameter optimization. Calculates EMA-based trend cycles, RSI momentum, and outputs optimal hold times and profit targets for leveraged trading. |
| `dydx_debug_market_data.py` | dYdX v4 protocol-specific market analyzer. Async orderbook depth, OBI (Order Book Imbalance), funding rate, and multi-resolution candle analysis. |
| `fetch_advanced_metrics.py` | Advanced market microstructure metrics: ATR volatility measurement, funding rate sentiment, open interest trend strength, and long/short ratio analysis. |
| `predict_profit.py` | Profit projection engine comparing Binance (swing, fee-adjusted) vs dYdX (zero-fee scalping) strategies across historical trade logs. |

### Data Assets

The `data/` directory contains **28+ structured datasets** including:

- **Historical K-lines**: Multi-year 1-minute resolution data (2019-2025)
- **AI Analysis Logs**: Machine learning model outputs and predictions
- **Backtest Sessions**: Strategy simulation results across market conditions
- **Whale Tracking**: Large-order detection and institutional flow data
- **Liquidation Pressure**: Leverage cascade risk measurements
- **Signal Analysis**: Technical indicator signal quality assessments

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Language** | Python 3.11+ |
| **Exchange APIs** | python-binance, ccxt, dYdX v4 Client |
| **Data Processing** | pandas, NumPy, SciPy, PyArrow |
| **Technical Indicators** | TA-Lib (6 core indicators) |
| **Machine Learning** | XGBoost, LightGBM, scikit-learn, Optuna |
| **Time Series** | Prophet, statsmodels |
| **Visualization** | Plotly, Matplotlib, Seaborn |
| **API Framework** | FastAPI, uvicorn, WebSockets |
| **Task Queue** | Celery, Flower |
| **Monitoring** | Prometheus |

---

## 🏁 Quick Start

```bash
# Clone and set up
cd crypto-market-data-pipeline
pip install -r requirements.txt

# Run market structure analysis (Binance Futures)
python debug_market_data.py

# Run dYdX market analysis
python dydx_debug_market_data.py

# Fetch advanced market microstructure metrics
python fetch_advanced_metrics.py

# Run profit prediction based on trade logs
python predict_profit.py
```

---

## 📈 Key Metrics

| Metric | Value |
|--------|-------|
| Total K-line Records | 3,100,000+ |
| Data Coverage | 2019-12 to 2025-11 (5.9 years) |
| Base Resolution | 1-minute |
| Derived Timeframes | 3m, 5m, 8m, 10m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 3d, 1w |
| Exchanges Supported | Binance Futures, dYdX v4 |
| Data Categories | 28+ structured datasets |

---

## ✍️ Author

**Huang Akai (Kai)** -- Founder @ Universal FAW Labs | Creative Technologist | Ex-Ogilvy | 15+ years experience

---

## 📄 License

MIT
