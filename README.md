# Intelligent System for Ft Analysis and Prediction

**Master's Thesis – Artificial Intelligence Program**  
**Universidad San Francisco de Quito (USFQ)**  
**Author**: Cristian Rodríguez  
**Institution**: Universidad San Francisco de Quito (USFQ)  
**Program**: Master's in Artificial Intelligence  
**Repository**: [bitcoin-predictor](https://github.com/crisrodriguez1993/bitcoin-predictor)

---

*This README is updated regularly to reflect the current development status. Last update: October 13, 2025*uez  
**Year:** 2025  
**Last Updated:** October 13, 2025

---

## Project Status & Progress

### **Phase 1: Data Acquisition (COMPLETED)**
**Status:** Fully implemented and tested  
**Implementation Date:** October 13, 2025  
**Achievement:** Multi-source data pipeline with 2,913 historical Bitcoin records

### **Phase 2: Data Cleaning & Normalization (NEXT)**
**Status:** Ready to implement  
**Description:** Data preprocessing and standardization for ML pipeline

### **Upcoming Phases**
- **Phase 3:** Sentiment Analysis (FinBERT integration)
- **Phase 4:** Feature Engineering (Technical indicators: RSI, MACD, etc.)
- **Phase 5:** Predictive Modeling (LSTM implementation)
- **Phase 6:** Evaluation & Backtesting
- **Phase 7:** Visualization & API Serving

---

## Project Description

This project develops an **intelligent system** for analyzing and predicting financial market movements, focusing on the **Bitcoin (BTC)** market.

The system integrates **financial time series**, **news sentiment analysis**, and **deep learning models** (FinBERT + LSTM) to predict both the **direction** (up/down) and **magnitude** of Bitcoin price changes over a **24-hour horizon**.

The architecture combines **technical indicators** (RSI, MACD, volatility, momentum) with **sentiment extracted from financial news** to enhance the model's predictive accuracy.  
All components are automated through a modular pipeline designed for research reproducibility and potential deployment in real-time environments.

---

## Project Objectives

- **Collect and process historical price data from multiple sources** *(Phase 1 - COMPLETED)*
- **Apply pre-trained language models (FinBERT / XLM-R) for sentiment scoring** *(Phase 3)*
- **Combine technical and sentiment features to train predictive deep learning models** *(Phase 4-5)*
- **Evaluate the model's robustness using walk-forward validation and backtesting** *(Phase 6)*
- **Implement an interactive dashboard and API for visualization and inference** *(Phase 7)*

---

## Current Implementation Status

### **Phase 1: Multi-Source Data Acquisition System**

#### **Completed Objectives:**
- **Multi-source data collection**: Binance + Yahoo Finance APIs
- **Configurable pipeline**: Environment-based configuration (.env)
- **Data lake architecture**: Bronze layer implementation
- **Quality assurance**: Data validation and error handling
- **File management**: Automatic cleanup and metadata tracking

#### **Technical Implementation:**

**Data Sources Active:**
- **Binance API**: 3 intervals (1h, 4h, 1d) → 3,000 records
- **Yahoo Finance API**: 2 intervals (1h, 1d) → 2,171 records
- **CoinGecko API**: Available (currently disabled)
- **CoinAPI**: Available (requires API key)

**System Features:**
- **Environment Configuration**: `.env` file for secure parameter management
- **Multi-source Integration**: Automatic data combination and deduplication
- **Smart File Management**: Replaces old files, optional backup system
- **Data Validation**: OHLCV integrity checks and timezone standardization
- **Metadata Tracking**: JSON files with download timestamps and source info
- **Rate Limiting**: Configurable API request delays
- **Professional Logging**: Structured logs with configurable levels

#### **Current Data Status:**
```
Latest Bitcoin Price: $115,645.75 USD
Historical Coverage: January 2023 → October 2025 (2.75 years)
Total Unique Records: 2,913 data points
Data Sources: 2 active APIs (Binance + Yahoo Finance)
Update Capability: Real-time data acquisition

Data Distribution by Source:
- Binance 1h: 1,000 records (last 41 days)
- Binance 4h: 1,000 records (last 166 days)  
- Binance 1d: 1,000 records (last 2.7 years)
- Yahoo 1h: 1,439 records (last 60 days)
- Yahoo 1d: 732 records (last 2 years)
```

#### **Generated Bronze Layer Data:**
```
data/bronze/
├── binance_btc_1h.csv      # Hourly Binance OHLCV data
├── binance_btc_4h.csv      # 4-hour Binance OHLCV data
├── binance_btc_1d.csv      # Daily Binance OHLCV data
├── yahoo_btc_1h.csv        # Hourly Yahoo Finance data
├── yahoo_btc_1d.csv        # Daily Yahoo Finance data
├── btc_combined_data.csv   # Main combined dataset
└── *.json                  # Metadata & configuration files
```

#### **Data Quality Metrics:**
- **Completeness**: 100% for enabled sources
- **Consistency**: Standardized OHLCV format across all sources
- **Timeliness**: Real-time capability with latest market data
- **Accuracy**: Direct API feeds from major financial data providers
- **Integrity**: Automated validation of price relationships (OHLC logic)

---

## How to Run the Current System

### **Prerequisites:**
```bash
# Clone the repository
git clone https://github.com/crisrodriguez1993/bitcoin-predictor.git
cd "02. Dev/bitcoin-predictor"

# Install required packages
pip install -r requirements.txt
```

### **Configuration:**
1. Copy `.env.example` to `.env`
2. Adjust configuration parameters as needed (default settings work fine)
3. For additional sources, add API keys to `.env`

### **Execute Data Acquisition:**
```bash
# Run the data acquisition system
python src/data/fetch_price_data_btc.py

# The system will:
# 1. Show current Bitcoin price
# 2. Offer data management options
# 3. Fetch data from configured sources
# 4. Save results to data/bronze/
```

---

## Technical Specifications

### **Current Technology Stack:**
- **Language**: Python 3.14+
- **Data Processing**: Pandas, NumPy
- **APIs**: Binance, Yahoo Finance (yfinance)
- **Configuration**: python-dotenv
- **Data Storage**: CSV files (Bronze layer)

### **Planned Additions:**
- **NLP**: Transformers, FinBERT
- **ML/DL**: TensorFlow/PyTorch, scikit-learn
- **Visualization**: Streamlit, Plotly
- **API**: FastAPI, Uvicorn
- **Technical Analysis**: TA-Lib

---

## Next Steps (Phase 2)

### **Immediate Priority: Data Cleaning & Normalization**

1. **Data Quality Assessment**
   - Missing value analysis
   - Outlier detection
   - Consistency checks across sources

2. **Data Preprocessing**
   - Handle missing timestamps
   - Normalize price scales
   - Synchronize different time intervals

3. **Silver Layer Implementation**
   - Clean, validated datasets
   - Standardized schemas
   - Ready for feature engineering


---

## � Contact Information

**Author**: Cristian Rodríguez  
**Institution**: Universidad San Francisco de Quito (USFQ)  
**Program**: Master's in Artificial Intelligence  
**Repository**: [bitcoin-predictor](https://github.com/crisrodriguez1993/bitcoin-predictor)

---

---

*This README is updated regularly to reflect the current development status. Last update: October 13, 2025*
