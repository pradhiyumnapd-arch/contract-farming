"""
INPUT LIMITS
============
One place that defines the allowed range for every numeric input.

  * "min" / "max"        hard limits - values outside are rejected (browser + server)
  * "typical_low/high"   range seen in most training records - shown as a hint
  * ranges come from the datasets the models were trained on (crop_data.csv,
    yield_data.csv), so the models are never asked to predict far outside
    what they learned.
"""


class InputRangeError(ValueError):
    """Raised when a submitted value is outside its allowed range."""


# -------------------- Crop recommendation form --------------------
CROP_LIMITS = {
    "farm_area": {"label": "Farm area", "unit": "acres", "min": 0.1, "max": 1000, "step": 0.1,
                  "typical_low": 1, "typical_high": 50, "example": "2.5"},
    "soil_ph": {"label": "Soil pH", "unit": "", "min": 3, "max": 10, "step": 0.1,
                "typical_low": 5.5, "typical_high": 7.7, "example": "6.5"},
    "nitrogen": {"label": "Nitrogen (N)", "unit": "", "min": 0, "max": 140, "step": 1,
                 "typical_low": 4, "typical_high": 116, "example": "90"},
    "phosphorus": {"label": "Phosphorus (P)", "unit": "", "min": 5, "max": 145, "step": 1,
                   "typical_low": 10, "typical_high": 132, "example": "42"},
    "potassium": {"label": "Potassium (K)", "unit": "", "min": 5, "max": 205, "step": 1,
                  "typical_low": 15, "typical_high": 199, "example": "43"},
    "temperature": {"label": "Temperature", "unit": "°C", "min": 5, "max": 45, "step": 0.1,
                    "typical_low": 17.5, "typical_high": 33.8, "example": "25"},
    "humidity": {"label": "Humidity", "unit": "%", "min": 10, "max": 100, "step": 0.1,
                 "typical_low": 20, "typical_high": 94, "example": "80"},
    # Farmers enter YEARLY rainfall. The crop model was trained on average MONTHLY
    # rainfall (20-300 mm), so the app divides the yearly value by 12 before predicting.
    "rainfall": {"label": "Annual rainfall", "unit": "mm", "min": 240, "max": 3600, "step": 1,
                 "typical_low": 400, "typical_high": 2460, "example": "1200"},
}

# -------------------- Yield prediction form --------------------
YIELD_LIMITS = {
    "crop_year": {"label": "Crop year", "unit": "", "min": 1997, "max": 2035, "step": 1,
                  "typical_low": 1997, "typical_high": 2035, "example": "2026"},
    "farm_area": {"label": "Farm area", "unit": "hectares", "min": 0.1, "max": 10000, "step": 0.1,
                  "typical_low": 0.5, "typical_high": 500, "example": "2.5"},
    "rainfall": {"label": "Annual rainfall", "unit": "mm", "min": 300, "max": 6600, "step": 1,
                 "typical_low": 530, "typical_high": 3000, "example": "1200"},
    # Fertilizer / pesticide are TOTAL kg for the farm. Limits are per hectare.
    "fertilizer_per_ha": {"label": "Fertilizer", "unit": "kg/ha", "min": 0, "max": 500,
                          "typical_low": 95, "typical_high": 195},
    "pesticide_per_ha": {"label": "Pesticide", "unit": "kg/ha", "min": 0, "max": 5,
                         "typical_low": 0.1, "typical_high": 0.4},
}

INPUT_LIMITS = {"crop": CROP_LIMITS, "yield": YIELD_LIMITS}


def _fmt(v):
    return f"{v:,.0f}" if float(v) == int(v) else f"{v:,}"


def _check(name, value, spec):
    unit = f" {spec['unit']}" if spec.get("unit") else ""
    if value != value:  # NaN
        raise InputRangeError(f"{spec['label']} must be a valid number.")
    if value < spec["min"] or value > spec["max"]:
        raise InputRangeError(
            f"{spec['label']} must be between {_fmt(spec['min'])} and {_fmt(spec['max'])}{unit} "
            f"(you entered {_fmt(value)})." + spec.get("note", "")
        )


def check_crop_inputs(values):
    """values: dict of field -> float. Raises InputRangeError on the first problem."""
    for field, spec in CROP_LIMITS.items():
        if field in values and values[field] is not None:
            _check(field, values[field], spec)


def check_yield_inputs(crop_year, farm_area, rainfall, fertilizer, pesticide):
    _check("crop_year", crop_year, YIELD_LIMITS["crop_year"])
    _check("farm_area", farm_area, YIELD_LIMITS["farm_area"])
    _check("rainfall", rainfall, YIELD_LIMITS["rainfall"])
    f_spec, p_spec = YIELD_LIMITS["fertilizer_per_ha"], YIELD_LIMITS["pesticide_per_ha"]
    f_max, p_max = f_spec["max"] * farm_area, p_spec["max"] * farm_area
    if fertilizer < 0 or fertilizer > f_max:
        raise InputRangeError(
            f"Fertilizer must be between 0 and {_fmt(round(f_max, 1))} kg for a {_fmt(farm_area)} ha farm "
            f"(max {_fmt(f_spec['max'])} kg per hectare). You entered {_fmt(fertilizer)} kg."
        )
    if pesticide < 0 or pesticide > p_max:
        raise InputRangeError(
            f"Pesticide must be between 0 and {_fmt(round(p_max, 2))} kg for a {_fmt(farm_area)} ha farm "
            f"(max {_fmt(p_spec['max'])} kg per hectare). You entered {_fmt(pesticide)} kg."
        )
