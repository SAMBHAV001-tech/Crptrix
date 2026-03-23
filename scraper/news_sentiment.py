import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sqlalchemy import text
from backend.db import engine

analyzer = SentimentIntensityAnalyzer()

NEWS_SOURCES = {
    "CoinDesk": "https://www.coindesk.com/",
    "CoinTelegraph": "https://cointelegraph.com/",
    "CryptoSlate": "https://cryptoslate.com/"
}

def extract_headlines(url):
    # ✅ Updated request settings
    response = requests.get(
        url,
        timeout=20,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    if response.status_code == 429:
        print(f"⚠️ Rate limited by {url}, skipping.")
        return []

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    articles = set()
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text_content = tag.get_text(strip=True)
        if text_content and len(text_content) > 20:
            articles.add(text_content)

    print("Articles found:", len(articles))

    return list(articles)

def analyze_and_store():
    timestamp = datetime.now(timezone.utc)

    with engine.begin() as conn:
        for source_name, url in NEWS_SOURCES.items():
            try:
                articles = extract_headlines(url)

                if not articles:
                    continue

                scores = [
                    analyzer.polarity_scores(article)["compound"]
                    for article in articles
                ]

                sentiment_score = sum(scores) / len(scores)

                conn.execute(
                    text("""
                        INSERT INTO news_sentiment
                        (symbol, timestamp, sentiment_score, source)
                        VALUES ('BTC', :ts, :score, :source)
                        ON CONFLICT (symbol, timestamp)
                        DO NOTHING
                    """),
                    {
                        "ts": timestamp,
                        "score": sentiment_score,
                        "source": source_name
                    }
                )

                print(f"✅ {source_name}: {sentiment_score:.3f}")

                # polite delay between sites
                time.sleep(3)

            except Exception as e:
                print(f"❌ Error processing {source_name}: {e}")

if __name__ == "__main__":
    analyze_and_store()