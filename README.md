# Assured Contract Farming

ML-powered crop recommendation, yield prediction and contract farming platform (Flask).

## Run
```
pip install flask flask-sqlalchemy scikit-learn pandas joblib
python app.py
```
Open http://127.0.0.1:5000

## Pages
Home · Dashboard · Search & Apply · Crop Selection · Yield Prediction · Chatbot ·
Farming Schedule · Technical Guidelines · Project Overview · Model Performance

## Models
| Model | Algorithm | Data | Script |
|---|---|---|---|
| Crop recommendation | Random Forest classifier | `crop_data.csv` (2,400 samples, 24 crops) | `train_model.py` |
| Yield prediction | Random Forest regressor pipeline | `yield_data.csv` (19,689 records) | `train_yield_model.py` |

Reproduce every metric shown in the app: `python compare_models.py` (writes `model_comparison.json`)
and `python evaluate_models.py` (writes `model_metrics.json`).

## Data note (important)
In the original `crop_data.csv`, the tomato and wheat rows used a different rainfall scale
(306-1,193 mm) from the other 22 crops (20-299 mm), so any rainfall above ~300 mm was always
recommended as tomato or wheat. `fix_crop_data.py` converts those rows to the same
average-monthly scale (yearly total / 12). The original is kept as `crop_data_original.csv`.
The crop form asks for **annual rainfall (mm)** and divides it by 12 before predicting, because the model works on monthly averages.

## Crop names between the two models
`crop_mapping.py` links recommended crops to yield-dataset crops (for example blackgram -> Urad).
Apple, coffee, grapes, mango, muskmelon, orange, papaya, pomegranate, tomato and watermelon
have no equivalent in the yield dataset.

## Input limits
All allowed ranges live in `input_limits.py` and are applied in the forms and on the server.
