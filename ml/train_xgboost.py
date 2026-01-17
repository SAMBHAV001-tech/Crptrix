import os
import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from xgboost import XGBClassifier
import joblib

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

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, shuffle=False
)

model = XGBClassifier(
    n_estimators=200,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric="logloss",
    random_state=42
)

model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print("📊 XGBoost Results")
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))

# Save model
joblib.dump(model, "ml/model.pkl")
print("✅ Model saved as ml/model.pkl")
