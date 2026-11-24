import joblib
import pandas as pd

data = pd.read_csv("crop_data.csv")
model = joblib.load("crop_model.pkl")

features = [
    "N", "P", "K",
    "temperature", "humidity", "ph", "rainfall"
]

print("\nCROP RECOMMENDATION TEST")
print("=" * 65)

for crop, group in data.groupby("label"):
    sample = group[features].median().to_frame().T

    probabilities = model.predict_proba(sample)[0]
    ranked = sorted(
        zip(model.classes_, probabilities),
        key=lambda x: x[1],
        reverse=True
    )

    print(f"\nActual crop profile: {crop}")
    print("Top 3 predictions:")

    for name, probability in ranked[:3]:
        print(f"  {name:18} {probability * 100:.2f}%")

print("\nTotal crop classes:", len(model.classes_))