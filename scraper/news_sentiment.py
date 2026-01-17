import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sqlalchemy import text
from database.db import engine

analyzer = SentimentIntensityAnalyzer()

NEWS_SOURCES = {
    "CoinDesk": "https://www.coindesk.com/",
    "CoinTelegraph": "https://cointelegraph.com/",
    "CryptoSlate": "https://cryptoslate.com/"
}

HEADERS = {
    "User-Agent": (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    "Accept-Language": "en-US,en;q=0.9"
}

def extract_headlines(url):
    response = requests.get(url, headers=HEADERS, timeout=10)

    if response.status_code == 429:
        print(f"⚠️ Rate limited by {url}, skipping.")
        return []

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    headlines = set()
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = tag.get_text(strip=True)
        if text and len(text) > 20:
            headlines.add(text)

    return list(headlines)

def analyze_and_store():
    timestamp = datetime.now(timezone.utc)

    with engine.begin() as conn:
        for source, url in NEWS_SOURCES.items():
            try:
                headlines = extract_headlines(url)

                if not headlines:
                    continue

                scores = [
                    analyzer.polarity_scores(h)["compound"]
                    for h in headlines
                ]

                avg_sentiment = sum(scores) / len(scores)

                conn.execute(
                    text("""
                        INSERT INTO news_sentiment
                        (symbol, timestamp, sentiment_score, source)
                        VALUES ('BTC', :ts, :score, :source)
                    """),
                    {
                        "ts": timestamp,
                        "score": avg_sentiment,
                        "source": source
                    }
                )

                print(f"✅ {source}: {avg_sentiment:.3f}")

                # polite delay between sites
                time.sleep(3)

            except Exception as e:
                print(f"❌ Error processing {source}: {e}")

if __name__ == "__main__":
    analyze_and_store()
