import joblib

model = joblib.load("crop_model.pkl")

print("MODEL TYPE:", type(model).__name__)
print("\nTOTAL CROP CLASSES:", len(model.classes_))
print("\nCROP NAMES:")

for crop in model.classes_:
    print(crop)