import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# Load dataset
data = pd.read_csv("yield_data.csv")

# Remove rows with missing values
data = data.dropna()

# Input features
X = data[
    [
        "Crop",
        "Crop_Year",
        "Season",
        "State",
        "Area",
        "Annual_Rainfall",
        "Fertilizer",
        "Pesticide"
    ]
]

# Target
y = data["Yield"]

# Categorical and numerical columns
categorical_columns = [
    "Crop",
    "Season",
    "State"
]

numerical_columns = [
    "Crop_Year",
    "Area",
    "Annual_Rainfall",
    "Fertilizer",
    "Pesticide"
]

# Preprocessing
preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_columns
        )
    ],
    remainder="passthrough"
)

# ML model
model = RandomForestRegressor(
    n_estimators=50,
    random_state=42
)

# Complete pipeline
pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ]
)

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# Train
pipeline.fit(X_train, y_train)

# Predict
y_pred = pipeline.predict(X_test)

# Evaluation
mae = mean_absolute_error(y_test, y_pred)
rmse = mean_squared_error(y_test, y_pred) ** 0.5
r2 = r2_score(y_test, y_pred)

print("Yield Prediction Model Trained Successfully!")
print("MAE:", round(mae, 2))
print("RMSE:", round(rmse, 2))
print("R2 Score:", round(r2, 2))

# Save model
joblib.dump(pipeline, "yield_model.pkl")

print("yield_model.pkl created successfully!")