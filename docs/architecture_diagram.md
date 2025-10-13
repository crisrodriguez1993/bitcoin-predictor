# 🧩 System Architecture – Intelligent Financial Market Analysis and Prediction

This diagram illustrates the full **data flow** of the intelligent system for
financial market analysis and Bitcoin price prediction.  
It represents each module from data ingestion to model serving and monitoring.

```text
               ┌───────────────────────────────────┐
               │          Data Sources             │
               │───────────────────────────────────│
               │ - Binance / Yahoo Finance (prices)│
               │ - Kaggle Financial News / RSS     │
               │ - NASDAQ Data Link (optional)     │
               └───────────────┬───────────────────┘
                               │
                               ▼
               ┌───────────────────────────────────┐
               │          Data Ingestion           │
               │───────────────────────────────────│
               │ • Collect price and news data     │
               │ • Store raw datasets (bronze)     │
               │ • Validate API connections        │
               └───────────────┬───────────────────┘
                               │
                               ▼
               ┌───────────────────────────────────┐
               │    Cleaning & Normalization       │
               │───────────────────────────────────│
               │ • Remove nulls / duplicates       │
               │ • Standardize timestamps to UTC   │
               │ • Harmonize formats               │
               └───────────────┬───────────────────┘
                               │
                               ▼
               ┌───────────────────────────────────┐
               │     NLP Sentiment Analysis        │
               │───────────────────────────────────│
               │ • FinBERT / XLM-R models          │
               │ • Windows: 6h / 12h / 24h         │
               │ • Exponential weighting           │
               │ • Aggregate sentiment features    │
               └───────────────┬───────────────────┘
                               │
                               ▼
               ┌───────────────────────────────────┐
               │      Feature Engineering          │
               │───────────────────────────────────│
               │ • Compute RSI, MACD, Volatility   │
               │ • Merge technical + sentiment data│
               │ • Output: /data/gold/features.csv │
               └───────────────┬───────────────────┘
                               │
                               ▼
               ┌───────────────────────────────────┐
               │        Predictive Modeling        │
               │───────────────────────────────────│
               │ • Models: LSTM / GRU / TFT        │
               │ • Targets: Direction & Δ% change  │
               │ • Walk-forward cross-validation   │
               │ • Output: /models/LSTM_v1.pkl     │
               └───────────────┬───────────────────┘
                               │
                               ▼
               ┌───────────────────────────────────┐
               │     Evaluation & Backtesting      │
               │───────────────────────────────────│
               │ • Metrics: AUC, F1, Sharpe, MaxDD │
               │ • Simulate trading performance    │
               │ • Output: /reports/backtest.html  │
               └───────────────┬───────────────────┘
                               │
                               ▼
               ┌───────────────────────────────────┐
               │     Visualization & Serving       │
               │───────────────────────────────────│
               │ • Streamlit dashboard             │
               │ • FastAPI REST endpoints          │
               │ • Drift monitoring & retraining   │
               │ • Retraining every 7 days         │
               └───────────────────────────────────┘
