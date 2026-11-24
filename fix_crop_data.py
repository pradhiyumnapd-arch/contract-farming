"""
FIX: rainfall scale mismatch in crop_data.csv
=============================================
The 22 original crops have rainfall of 20-299 mm (an average monthly value),
but the tomato and wheat rows were added with 306-1,193 mm (yearly-style
totals). The two scales never overlap, so any rainfall above ~300 mm made the
model answer "tomato" or "wheat", and those two crops were separable by
rainfall alone.

This script converts the tomato and wheat rainfall to the same monthly-average
scale (yearly total / 12). The original file is kept as crop_data_original.csv.

Run once:   python fix_crop_data.py     then:   python train_model.py
"""
import os
import shutil

import pandas as pd

SOURCE = "crop_data.csv"
BACKUP = "crop_data_original.csv"

if not os.path.exists(BACKUP):
    shutil.copy(SOURCE, BACKUP)

data = pd.read_csv(BACKUP)
mask = data["label"].isin(["tomato", "wheat"])
data.loc[mask, "rainfall"] = (data.loc[mask, "rainfall"] / 12).round(2)
data.to_csv(SOURCE, index=False)

print("Converted tomato/wheat rainfall to monthly-average scale (/12).")
print(data.groupby(mask.map({True: "tomato+wheat", False: "other 22 crops"}))["rainfall"].agg(["min", "max"]).round(1))
