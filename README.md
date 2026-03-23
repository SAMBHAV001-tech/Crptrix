# Crptrix — Crypto Market Intelligence System

**BTC Growth Probability Classifier using XGBoost and News Sentiment Analysis**

Live Demo: [https://crptrix.vercel.app]

> This project is built for academic and research demonstration purposes only. It does not constitute financial or investment advice of any kind.

---

## Overview

Crptrix is a cryptocurrency market intelligence system that estimates the short-term growth probability of Bitcoin (BTC) using machine learning and sentiment analysis. The system integrates live market data from the CoinGecko API with sentiment signals scraped from cryptocurrency news outlets, engineers predictive features over 24-hour rolling windows, and runs inference through a trained XGBoost binary classifier.

The model predicts whether BTC price will grow by more than 1% within the next 24 hours, achieving:

- **Accuracy:** 89.08%
- **ROC-AUC:** 0.9329
- **Recall (Growth class):** 83.13%

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.x |
| Web Framework | FastAPI |
| Database | PostgreSQL (Supabase) |
| Market Data | CoinGecko API |
| Sentiment Data | CoinDesk, CoinTelegraph, CryptoSlate |
| Sentiment Analysis | VADER |
| Machine Learning | XGBoost (binary:logistic) |
| Frontend | React / HTML Dashboard |
| Backend Deployment | Render |
| Frontend Deployment | Vercel |
| Automation | GitHub Actions (cron-based ingestion) |

---

## Repository Structure
```
crptrix/
├── database/       # DB connection setup and schema definitions
├── scraper/        # Live data ingestion (market + sentiment)
├── ml/             # Feature engineering pipeline and model training
├── backend/        # FastAPI prediction endpoints
├── frontend/       # Dashboard UI
└── scripts/        # Database setup and recovery utilities
```

---

## Data Pipeline

### Market Data
Live OHLCV (Open, High, Low, Close, Volume) data for Bitcoin is fetched from the CoinGecko API on a scheduled basis via GitHub Actions cron workflows. Data is stored in a `prices` table in PostgreSQL (~9,159 rows).

### Sentiment Data
Article headlines and content are scraped from CoinDesk, CoinTelegraph, and CryptoSlate, then processed through VADER to produce per-article sentiment scores. Scores are stored in a `news_sentiment` table (~103 rows).

### Feature Engineering
Five features are computed over 24-hour rolling windows and written to a `features` table (~8,002 rows):

| Feature | Description |
|---|---|
| `return_24h` | Percentage change in closing price over 24 hours |
| `volatility_24h` | Coefficient of Variation (std / mean) over 24 hours |
| `volume_change_24h` | Relative change in trading volume vs. prior 24h period |
| `avg_news_sentiment_24h` | Average VADER score from news articles in the past 24 hours |
| `sentiment_momentum` | Rolling difference in average sentiment scores |

The binary label is `1` if the 24-hour return exceeds 1% (growth), `0` otherwise.

---

## Model

**Algorithm:** XGBoost (XGBClassifier, binary:logistic)

Key hyperparameters:
```
n_estimators:     300
max_depth:        4
learning_rate:    0.05
subsample:        0.8
colsample_bytree: 0.8
scale_pos_weight: 10.982   # auto-computed for class imbalance
eval_metric:      logloss
```

The dataset has a significant class imbalance (91.6% no-growth, 8.4% growth). `scale_pos_weight` is used to penalise missed growth events during training. The model was trained on a 75/25 stratified split (5,991 train / 1,997 test).

### Feature Importance (XGBoost Gain)

| Rank | Feature | Score |
|---|---|---|
| 1 | `sentiment_momentum` | 0.2764 |
| 2 | `volatility_24h` | 0.2269 |
| 3 | `avg_news_sentiment_24h` | 0.2151 |
| 4 | `volume_change_24h` | 0.1466 |
| 5 | `return_24h` | 0.1351 |

Sentiment momentum is the single most predictive feature, indicating that directional shifts in market sentiment carry stronger short-term signal than price-based indicators alone.

---

## Evaluation Results

| Metric | Value |
|---|---|
| Accuracy | 89.08% |
| Balanced Accuracy | 86.38% |
| ROC-AUC | 0.9329 |
| PR-AUC | 0.6565 |
| Matthews MCC | 0.5421 |
| Precision (Growth) | 42.07% |
| Recall (Growth) | 83.13% |
| F1-Score (Growth) | 0.5587 |

The model is deliberately tuned for high recall — missing a genuine growth signal is treated as more costly than a false alarm.

---

## System Architecture
```
GitHub Actions (cron)
        |
        v
  [Scraper Module]
  CoinGecko API  +  News Scrapers (CoinDesk, CoinTelegraph, CryptoSlate)
        |
        v
  PostgreSQL (Supabase)
  prices | news_sentiment | features
        |
        v
  [Feature Engineering Pipeline]
        |
        v
  [XGBoost Model — Inference]
        |
        v
  FastAPI (REST endpoint) — deployed on Render
        |
        v
  Frontend Dashboard — deployed on Vercel
  https://crptrix.vercel.app
```

---

## Environment Variables
```env
DATABASE_URL=your_supabase_postgresql_connection_string
COINGECKO_API_KEY=your_coingecko_api_key
```

---

## Database Recovery

If the Supabase free-tier database expires:

1. Update the environment variable: `psql -h aws-1-ap-south-1.pooler.supabase.com -p 5432 -d postgres -U postgres.nnunlgdxfymapfyatmyb`
2. Run: `python scripts/setup_db.py`

This recreates all tables and resumes live data ingestion automatically.

---

## Disclaimer

Crptrix is built strictly for learning and academic demonstration. All predictions are probabilistic estimates based on historical patterns and sentiment signals. They should not be used as the sole basis for any trading or investment decision.

---

## References

- [CoinGecko API](https://www.coingecko.com/en/api)
- [VADER Sentiment Analysis — Hutto & Gilbert (2014)](https://ojs.aaai.org/index.php/ICWSM/article/view/14550)
- [XGBoost — Chen & Guestrin (2016)](https://arxiv.org/abs/1603.02754)
- [FastAPI](https://fastapi.tiangolo.com)
- [Supabase](https://supabase.com)
- [Render](https://render.com)
- [Vercel](https://vercel.com)
- [GitHub Actions](https://docs.github.com/en/actions)
