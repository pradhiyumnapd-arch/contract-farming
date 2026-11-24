import pandas as pd

data = pd.read_csv("crop_data.csv")

crop = "cotton"

sample = data[data["label"] == crop].iloc[0]

print("\nACTUAL DATASET PROFILE:", crop)
print("Farm area: 3 acres")
print("Soil type: Loamy")
print("Soil pH:", sample["ph"])
print("Nitrogen:", sample["N"])
print("Phosphorus:", sample["P"])
print("Potassium:", sample["K"])
print("Temperature:", sample["temperature"])
print("Humidity:", sample["humidity"])
print("Rainfall to enter:", sample["rainfall"] * 12)