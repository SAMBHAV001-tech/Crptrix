import os
import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix

db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

# Load data
df = pd.read_sql("SELECT * FROM features", engine)

X = df[
    [
        "return_24h",
        "volatility_24h",
        "volume_change_24h",
        "avg_news_sentiment_24h",
        "sentiment_momentum",
    ]
]
y = df["label"]

# Train-test split (time-safe)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, shuffle=False
)

# Model
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# Evaluation
y_pred = model.predict(X_test)

print("📊 Logistic Regression Results")
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))
