Crptrix

Crptrix is a student-built crypto market intelligence project that analyzes live market data and public sentiment to estimate short-term growth probability and risk.
The project is for educational and research purposes only.

Tech Stack:

Python
FastAPI
PostgreSQL (Render)
CoinGecko API (market data)
Reddit API (sentiment)
XGBoost (ML)
VADER (sentiment analysis)
Bolt AI (frontend)

What Crptrix Does:

Fetches live cryptocurrency market data
Collects public sentiment signals
Builds features for ML models
Predicts probability of price growth, not exact prices
Provides explainable insights

Project Structure:
database/   → DB connection & schema
scraper/    → Live data ingestion
ml/         → Feature engineering & models
backend/    → FastAPI services
frontend/   → UI (Bolt AI)
scripts/    → Setup & recovery scripts

Database Setup / Recovery:

If the Render database expires:
setx DATABASE_URL "NEW_RENDER_DB_URL"
python scripts/setup_db.py

This recreates tables and starts live data ingestion.

### Cloud Ingestion
Data ingestion is automated using GitHub Actions cron workflows, enabling cost-free scheduled execution for public repositories.

Data Sources:

Market data: CoinGecko API
Sentiment data: Reddit (PRAW)
Market data powered by CoinGecko.

Disclaimer:

Crptrix does not provide trading or investment advice.
It is built strictly for learning and academic demonstration.