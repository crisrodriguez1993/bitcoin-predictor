# Bitcoin Intelligence Lab (Colab)

Sistema de análisis del comportamiento de Bitcoin combinando:

- Series de tiempo con modelos `LSTM`
- Variables macroeconómicas/mercado (balances e indicadores económicos)
- Análisis de sentimiento de redes sociales (Reddit) y fuentes cripto (Binance/mercado)

El objetivo es estimar:

1. Pronóstico de precio/retorno a 24h
2. Señal de recomendación de inversión a horizontes mayores (multiperiodo)

---

## Arquitectura de datos

### 1) Bronze (datos crudos)
- `data/bronze/market_data/`: OHLCV, volumen, funding/open interest, etc.
- `data/bronze/macro_data/`: tasas, inflación, dólar, índices, etc.
- `data/bronze/sentiment_data/`: posts/comentarios y metadatos de sentimiento

### 2) Silver (datos limpios)
- Estandarización de columnas y formatos
- Manejo de `nulls`, duplicados y outliers
- Unificación temporal por granularidad (1h, 4h, 1d)

### 3) Gold (dataset de modelado)
- Features finales para entrenamiento
- Dataset supervisado para horizonte 24h y ventanas mayores
- Variables objetivo + señal de inversión

---

## Estructura del repositorio

```text
bitcoin-predictor/
├── configs/
├── data/
│   ├── bronze/
│   │   ├── market_data/
│   │   ├── macro_data/
│   │   └── sentiment_data/
│   ├── silver/
│   └── gold/
├── models/
├── notebooks/
├── reports/
│   └── figures/
├── requirements.txt
└── .gitignore
```

---

## Notebooks iniciales (Colab-first)

1. `00_project_setup_colab.ipynb`
2. `01_bronze_ingestion_market_macro.ipynb`
3. `02_bronze_ingestion_sentiment.ipynb`
4. `03_silver_cleaning_unification.ipynb`
5. `04_gold_feature_engineering.ipynb`
6. `05_modeling_lstm_sentiment_forecast.ipynb`
7. `06_investment_signal_report.ipynb`

---

## Escala de sentimiento

Se usará una escala ordinal de 5 clases:

- Muy negativo = `-2`
- Negativo = `-1`
- Neutro = `0`
- Positivo = `1`
- Muy positivo = `2`

Esta señal se agregará por ventana temporal para tratarse como serie de tiempo.

---

## Próximo paso

Completar el notebook `00_project_setup_colab.ipynb` para:

- Montar Google Drive
- Instalar dependencias
- Definir rutas base del proyecto
- Validar acceso a fuentes de datos

