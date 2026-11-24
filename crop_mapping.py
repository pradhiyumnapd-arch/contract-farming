"""
Maps a crop recommended by the crop model to the matching crop name in the
yield dataset, so the recommended crop can flow straight into Yield Prediction.

The two datasets use different names (for example "blackgram" vs "Urad"), so
exact matching would fail for most crops. Crops with no equivalent in the
yield dataset return None - the app then says so instead of guessing.
"""

# crop-model name (lower case)  ->  yield-dataset name
CROP_TO_YIELD = {
    "rice": "Rice",
    "wheat": "Wheat",
    "maize": "Maize",
    "banana": "Banana",
    "coconut": "Coconut",
    "jute": "Jute",
    "cotton": "Cotton(lint)",
    "blackgram": "Urad",                 # black gram = urad
    "chickpea": "Gram",                  # chickpea = gram
    "lentil": "Masoor",                  # lentil = masoor
    "mothbeans": "Moth",
    "mungbean": "Moong(Green Gram)",
    "pigeonpeas": "Arhar/Tur",           # pigeon pea = arhar / tur
    "kidneybeans": "Peas & beans (Pulses)",   # closest category in the dataset
    # No equivalent in the yield dataset:
    # apple, coffee, grapes, mango, muskmelon, orange, papaya, pomegranate,
    # tomato, watermelon
}


def yield_crop_for(crop_name, available_crops):
    """Return the exact yield-dataset crop string for a recommended crop, or None."""
    if not crop_name:
        return None
    key = str(crop_name).strip().lower().replace(" ", "")
    target = CROP_TO_YIELD.get(key)
    if target is None:
        return None
    for name in available_crops:          # return the dataset's exact spelling
        if name.strip().lower() == target.strip().lower():
            return name
    return None
