"""
Helper that gathers real, live facts about the project (datasets, trained
model, code base) for the Project Overview page. Pure Python - no Flask.
"""
import json
import os

FEATURE_LABELS = {
    "N": "Nitrogen (N)",
    "P": "Phosphorus (P)",
    "K": "Potassium (K)",
    "temperature": "Temperature",
    "humidity": "Humidity",
    "ph": "Soil pH",
    "rainfall": "Rainfall",
}
CROP_FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]


def _count_lines(folder, extensions):
    total, files = 0, 0
    if not os.path.isdir(folder):
        return 0, 0
    for name in os.listdir(folder):
        if name.endswith(extensions):
            files += 1
            with open(os.path.join(folder, name), "r", encoding="utf-8", errors="ignore") as f:
                total += sum(1 for _ in f)
    return total, files


def build_overview(crop_model, yield_data, ml_crops, root_path, route_count):
    # ---- measured model quality (created by evaluate_models.py) ----
    metrics = None
    metrics_path = os.path.join(root_path, "model_metrics.json")
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path) as f:
                metrics = json.load(f)
        except (OSError, ValueError):
            metrics = None

    # ---- feature importance straight from the trained crop model ----
    importances = []
    try:
        values = list(crop_model.feature_importances_)
        importances = sorted(
            [
                {"name": FEATURE_LABELS[n], "value": round(float(v) * 100, 1)}
                for n, v in zip(CROP_FEATURES, values)
            ],
            key=lambda x: x["value"],
            reverse=True,
        )
    except Exception:
        importances = []

    # ---- yield dataset insights ----
    per_year = yield_data.groupby("Crop_Year").size()
    years = [[int(y), int(c)] for y, c in per_year.items()]

    top_states = [
        {"name": str(s), "value": int(c)}
        for s, c in yield_data["State"].value_counts().head(8).items()
    ]
    seasons = [
        {"name": str(s).strip(), "value": int(c)}
        for s, c in yield_data["Season"].str.strip().value_counts().items()
    ]

    # ---- crop-recommendation dataset size ----
    crop_samples = 0
    try:
        with open(os.path.join(root_path, "crop_data.csv"), "r", encoding="utf-8") as f:
            crop_samples = max(sum(1 for _ in f) - 1, 0)
    except OSError:
        pass

    py_lines, py_files = _count_lines(root_path, (".py",))
    html_lines, html_files = _count_lines(os.path.join(root_path, "templates"), (".html",))
    css_lines, _ = _count_lines(os.path.join(root_path, "static", "css"), (".css",))
    js_lines, _ = _count_lines(os.path.join(root_path, "static", "js"), (".js",))

    return {
        "metrics": metrics,
        "importances": importances,
        "years": years,
        "top_states": top_states,
        "seasons": seasons,
        "counts": {
            "crop_samples": int(crop_samples),
            "ml_crops": len(ml_crops),
            "yield_records": int(len(yield_data)),
            "yield_crops": int(yield_data["Crop"].nunique()),
            "states": int(yield_data["State"].nunique()),
            "year_from": int(yield_data["Crop_Year"].min()),
            "year_to": int(yield_data["Crop_Year"].max()),
            "routes": int(route_count),
            "templates": int(html_files),
            "code_lines": int(py_lines + html_lines + css_lines + js_lines),
            "py_lines": int(py_lines),
            "py_files": int(py_files),
        },
    }


def load_comparison(root_path):
    """Load the results written by compare_models.py (or None if not run yet)."""
    path = os.path.join(root_path, "model_comparison.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None
