"""
MODEL COMPARISON & EVALUATION
=============================
Trains several algorithms on the SAME data split and measures them with
standard machine-learning metrics. Nothing here is hand-written: every number
in model_comparison.json is produced by this script.

Run:   python compare_models.py
Output: model_comparison.json  (read by the Model Performance page)

Protocol
  * Crop recommendation (classification): stratified 80/20 hold-out split +
    stratified 5-fold cross-validation on the full dataset.
  * Yield prediction (regression): random 80/20 hold-out split + 5-fold
    cross-validation on the full dataset.
  * random_state = 42 everywhere so results are reproducible.
"""
import json
import time
import warnings

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    ExtraTreesClassifier, ExtraTreesRegressor, GradientBoostingClassifier,
    GradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score, mean_absolute_error,
    mean_squared_error, median_absolute_error, precision_recall_fscore_support,
    precision_score, r2_score, recall_score,
)
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_predict, cross_val_score, train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

warnings.filterwarnings("ignore")
SEED = 42
RESULT = {}

# Optional: set COMPARE_CACHE=<folder> to resume an interrupted run.
import os
import pickle

_CACHE = os.environ.get("COMPARE_CACHE")


def cached(key, compute):
    """Return compute() result, reusing a saved copy when caching is enabled."""
    if not _CACHE:
        return compute()
    os.makedirs(_CACHE, exist_ok=True)
    path = os.path.join(_CACHE, key.replace(" ", "_").replace("(", "").replace(")", "") + ".pkl")
    if os.path.exists(path):
        with open(path, "rb") as fh:
            return pickle.load(fh)
    value = compute()
    with open(path, "wb") as fh:
        pickle.dump(value, fh)
    return value

# =====================================================================
# 1. CROP RECOMMENDATION  (classification)
# =====================================================================
crop = pd.read_csv("crop_data.csv")
FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
X, y = crop[FEATURES], crop["label"]
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=SEED, stratify=y)
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

classifiers = {
    "Random Forest (used)": RandomForestClassifier(n_estimators=100, random_state=SEED),
    "Extra Trees": ExtraTreesClassifier(n_estimators=100, random_state=SEED),
    "Gradient Boosting": GradientBoostingClassifier(random_state=SEED),
    "Decision Tree": DecisionTreeClassifier(random_state=SEED),
    "K-Nearest Neighbors": Pipeline([("s", StandardScaler()), ("m", KNeighborsClassifier())]),
    "SVM (RBF)": Pipeline([("s", StandardScaler()), ("m", SVC(random_state=SEED))]),
    "Logistic Regression": Pipeline([("s", StandardScaler()), ("m", LogisticRegression(max_iter=2000))]),
    "Gaussian Naive Bayes": GaussianNB(),
}

crop_rows, fitted = [], {}


def run_classifier(name, model):
    t0 = time.time()
    model.fit(X_tr, y_tr)
    train_time = time.time() - t0
    t0 = time.time()
    pred = model.predict(X_te)
    pred_time = (time.time() - t0) / len(X_te) * 1000
    cv = cross_val_score(model, X, y, cv=skf, scoring="accuracy")
    row = {
        "model": name,
        "accuracy": round(accuracy_score(y_te, pred) * 100, 2),
        "precision": round(precision_score(y_te, pred, average="macro") * 100, 2),
        "recall": round(recall_score(y_te, pred, average="macro") * 100, 2),
        "f1": round(f1_score(y_te, pred, average="macro") * 100, 2),
        "cv_mean": round(cv.mean() * 100, 2),
        "cv_std": round(cv.std() * 100, 2),
        "cv_folds": [round(v * 100, 2) for v in cv],
        "train_seconds": round(train_time, 3),
        "predict_ms": round(pred_time, 4),
    }
    return row, pred


for name, model in classifiers.items():
    row, pred = cached("crop_" + name, lambda n=name, m=model: run_classifier(n, m))
    crop_rows.append(row)
    fitted[name] = (model, pred)
    print(f"[crop] {name:24s} acc={row['accuracy']:6.2f}  cv={row['cv_mean']:6.2f}+-{row['cv_std']:.2f}", flush=True)

# Out-of-fold predictions: every one of the samples is predicted by a model that
# never saw it during training, so ALL samples act as test data (not just 20%).
def run_oof():
    return cross_val_predict(RandomForestClassifier(n_estimators=100, random_state=SEED), X, y, cv=skf)


oof = cached("crop_oof", run_oof)
classes = sorted(y.unique())
y_all = y.to_numpy()
cm = confusion_matrix(y_all, oof, labels=classes)
p, r, f, s = precision_recall_fscore_support(y_all, oof, labels=classes, zero_division=0)
per_class = [
    {"crop": c, "precision": round(float(p[i]) * 100, 1), "recall": round(float(r[i]) * 100, 1),
     "f1": round(float(f[i]) * 100, 1), "support": int(s[i])}
    for i, c in enumerate(classes)
]
misclassified = [
    {"actual": classes[i], "predicted": classes[j], "count": int(cm[i][j])}
    for i in range(len(classes)) for j in range(len(classes)) if i != j and cm[i][j] > 0
]
oof_summary = {
    "samples": int(len(y_all)),
    "correct": int((oof == y_all).sum()),
    "accuracy": round(float((oof == y_all).mean()) * 100, 2),
    "precision": round(float(precision_score(y_all, oof, average="macro")) * 100, 2),
    "recall": round(float(recall_score(y_all, oof, average="macro")) * 100, 2),
    "f1": round(float(f1_score(y_all, oof, average="macro")) * 100, 2),
}
print("[crop] out-of-fold:", oof_summary, flush=True)

RESULT["crop"] = {
    "samples": int(len(crop)), "classes": len(classes),
    "train_size": int(len(X_tr)), "test_size": int(len(X_te)),
    "models": crop_rows,
    "classes_list": classes,
    "confusion_matrix": cm.tolist(),
    "per_class": per_class,
    "misclassified": sorted(misclassified, key=lambda d: -d["count"]),
    "oof": oof_summary,
}

# =====================================================================
# 2. YIELD PREDICTION  (regression)
# =====================================================================
yd = pd.read_csv("yield_data.csv").dropna()
COLS = ["Crop", "Crop_Year", "Season", "State", "Area", "Annual_Rainfall", "Fertilizer", "Pesticide"]
Xy, yy = yd[COLS], yd["Yield"]
Xy_tr, Xy_te, yy_tr, yy_te = train_test_split(Xy, yy, test_size=0.2, random_state=SEED)
kf = KFold(n_splits=5, shuffle=True, random_state=SEED)


def pipe(model, scale=False):
    steps = [("categorical", OneHotEncoder(handle_unknown="ignore"), ["Crop", "Season", "State"])]
    if scale:
        steps.append(("num", StandardScaler(), ["Crop_Year", "Area", "Annual_Rainfall", "Fertilizer", "Pesticide"]))
        pre = ColumnTransformer(steps)
    else:
        pre = ColumnTransformer(steps, remainder="passthrough")
    return Pipeline([("preprocessor", pre), ("model", model)])


regressors = {
    "Random Forest (used)": pipe(RandomForestRegressor(n_estimators=50, random_state=SEED)),
    "Extra Trees": pipe(ExtraTreesRegressor(n_estimators=50, random_state=SEED, n_jobs=-1)),
    "Gradient Boosting": pipe(GradientBoostingRegressor(random_state=SEED)),
    "Decision Tree": pipe(DecisionTreeRegressor(random_state=SEED)),
    "K-Nearest Neighbors": pipe(KNeighborsRegressor(n_jobs=-1), scale=True),
    "Ridge Regression": pipe(Ridge(), scale=True),
    "Linear Regression": pipe(LinearRegression(), scale=True),
}

yield_rows, yfitted = [], {}


def run_regressor(name, model):
    t0 = time.time()
    model.fit(Xy_tr, yy_tr)
    train_time = time.time() - t0
    pred = model.predict(Xy_te)
    cv = cross_val_score(model, Xy, yy, cv=kf, scoring="r2")
    row = {
        "model": name,
        "r2": round(float(r2_score(yy_te, pred)), 4),
        "mae": round(float(mean_absolute_error(yy_te, pred)), 3),
        "rmse": round(float(mean_squared_error(yy_te, pred) ** 0.5), 3),
        "medae": round(float(median_absolute_error(yy_te, pred)), 3),
        "cv_mean": round(float(cv.mean()), 4),
        "cv_std": round(float(cv.std()), 4),
        "cv_folds": [round(float(v), 4) for v in cv],
        "train_seconds": round(train_time, 3),
    }
    return row, pred


for name, model in regressors.items():
    row, pred = cached("yield_" + name, lambda n=name, m=model: run_regressor(n, m))
    yield_rows.append(row)
    yfitted[name] = pred
    print(f"[yield] {name:24s} r2={row['r2']:.4f} mae={row['mae']:.3f} cv={row['cv_mean']:.4f}", flush=True)

# predicted-vs-actual sample + residual summary for the model the project uses
used = yfitted["Random Forest (used)"]
actual = yy_te.to_numpy()
resid = actual - used
rng = np.random.RandomState(SEED)
idx = rng.choice(len(actual), size=min(500, len(actual)), replace=False)
# robust view: exclude the extreme outliers (top 1%) so the plot is readable
cap = float(np.percentile(actual, 99))
scatter = [[round(float(actual[i]), 3), round(float(used[i]), 3)] for i in idx if actual[i] <= cap]
within = lambda pct: round(float((np.abs(resid) <= np.abs(actual) * pct).mean() * 100), 1)

# relative accuracy on the typical (non-outlier) 99% of records
mask = actual <= cap
RESULT["yield"] = {
    "records": int(len(yd)), "train_size": int(len(Xy_tr)), "test_size": int(len(Xy_te)),
    "models": yield_rows,
    "scatter": scatter, "scatter_cap": round(cap, 2),
    "r2_typical": round(float(r2_score(actual[mask], used[mask])), 4),
    "mae_typical": round(float(mean_absolute_error(actual[mask], used[mask])), 3),
    "within_10pct": within(0.10), "within_20pct": within(0.20),
    "target_mean": round(float(yy.mean()), 3), "target_median": round(float(yy.median()), 3),
    "target_max": round(float(yy.max()), 1),
    "residual_mean": round(float(resid.mean()), 3),
    "residual_median": round(float(np.median(resid)), 3),
}

RESULT["meta"] = {"seed": SEED, "generated": time.strftime("%Y-%m-%d %H:%M")}
with open("model_comparison.json", "w") as fh:
    json.dump(RESULT, fh)
print("\nSaved model_comparison.json")
