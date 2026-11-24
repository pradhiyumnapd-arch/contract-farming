"""
Evaluate both ML models on a held-out 20% test split and save the results to
model_metrics.json, which the Project Overview page displays.

Uses the SAME configuration as train_model.py / train_yield_model.py
(RandomForest, random_state=42). Run:  python evaluate_models.py
"""
import json

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score, f1_score, mean_absolute_error, mean_squared_error, r2_score
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# ---------------- Crop recommendation (classification) ----------------
crop = pd.read_csv("crop_data.csv")
features = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
X_tr, X_te, y_tr, y_te = train_test_split(
    crop[features], crop["label"], test_size=0.2, random_state=42, stratify=crop["label"]
)
clf = RandomForestClassifier(n_estimators=100, random_state=42).fit(X_tr, y_tr)
pred = clf.predict(X_te)
crop_metrics = {
    "accuracy": round(accuracy_score(y_te, pred) * 100, 2),
    "f1_macro": round(f1_score(y_te, pred, average="macro") * 100, 2),
    "train_samples": int(len(X_tr)),
    "test_samples": int(len(X_te)),
}

# ---------------- Yield prediction (regression) ----------------
y = pd.read_csv("yield_data.csv").dropna()
cols = ["Crop", "Crop_Year", "Season", "State", "Area", "Annual_Rainfall", "Fertilizer", "Pesticide"]
Xy_tr, Xy_te, yy_tr, yy_te = train_test_split(y[cols], y["Yield"], test_size=0.2, random_state=42)
pipe = Pipeline([
    ("preprocessor", ColumnTransformer(
        [("categorical", OneHotEncoder(handle_unknown="ignore"), ["Crop", "Season", "State"])],
        remainder="passthrough")),
    ("model", RandomForestRegressor(n_estimators=50, random_state=42)),
]).fit(Xy_tr, yy_tr)
p2 = pipe.predict(Xy_te)
yield_metrics = {
    "r2": round(r2_score(yy_te, p2), 4),
    "mae": round(mean_absolute_error(yy_te, p2), 3),
    "rmse": round(mean_squared_error(yy_te, p2) ** 0.5, 3),
    "train_samples": int(len(Xy_tr)),
    "test_samples": int(len(Xy_te)),
}

with open("model_metrics.json", "w") as f:
    json.dump({"crop": crop_metrics, "yield": yield_metrics}, f, indent=2)
print(json.dumps({"crop": crop_metrics, "yield": yield_metrics}, indent=2))
