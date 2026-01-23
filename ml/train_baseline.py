import os
import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# --- DB CONNECTION ---
db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise RuntimeError("DATABASE_URL not set")

engine = create_engine(db_url)

# --- LOAD DATA ---
df = pd.read_sql("""
    SELECT
        return_24h,
        volatility_24h,
        volume_change_24h,
        avg_news_sentiment_24h,
        sentiment_momentum,
        label
    FROM features
""", engine)

# --- FEATURES & TARGET ---
X = df.drop(columns=["label"])
y = df["label"]

# --- TRAIN / TEST SPLIT ---
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.25,
    random_state=42,
    stratify=y
)

# --- PIPELINE (SCALING + LOGREG) ---
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        solver="lbfgs"
    ))
])

# --- TRAIN ---
pipeline.fit(X_train, y_train)

# --- EVALUATE ---
y_pred = pipeline.predict(X_test)

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred, digits=4))
