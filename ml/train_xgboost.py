import os
import pandas as pd
import joblib
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from xgboost import XGBClassifier


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

X = df.drop(columns=["label"])
y = df["label"]

# --- TRAIN / TEST SPLIT ---
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.25,
    random_state=42,
    stratify=y
)

# --- HANDLE CLASS IMBALANCE ---
pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

# --- MODEL ---
model = XGBClassifier(
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=pos_weight,
    objective="binary:logistic",
    eval_metric="logloss",
    random_state=42,
    n_jobs=-1
)

# --- TRAIN ---
model.fit(X_train, y_train)

# --- EVALUATE ---
y_pred = model.predict(X_test)

print("\n📊 XGBoost Results")
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred, digits=4))

# --- FEATURE IMPORTANCE ---
importance = pd.Series(
    model.feature_importances_,
    index=X.columns
).sort_values(ascending=False)

print("\n🔍 Feature Importance:")
print(importance)

# Save model for backend inference
os.makedirs("backend", exist_ok=True)
joblib.dump(model, "backend/xgboost_model.joblib")

print("✅ XGBoost model saved to backend/xgboost_model.joblib")