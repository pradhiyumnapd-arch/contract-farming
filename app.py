from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

import joblib
import pandas as pd

from overview_data import build_overview, load_comparison
from crop_mapping import yield_crop_for as _yield_crop_for
from input_limits import (
    INPUT_LIMITS, InputRangeError, check_crop_inputs, check_yield_inputs
)


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)

app.secret_key = "change-this-to-something-random"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///farming.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ============================================================
# LOAD MACHINE LEARNING MODELS
# ============================================================

crop_model = joblib.load("crop_model.pkl")
yield_model = joblib.load("yield_model.pkl")


# ============================================================
# LOAD YIELD DATASET
# ============================================================

yield_data = pd.read_csv("yield_data.csv")

YIELD_STATES = sorted(
    yield_data["State"].dropna().unique().tolist()
)

YIELD_SEASONS = sorted(
    yield_data["Season"].dropna().unique().tolist()
)

YIELD_CROPS = sorted(
    yield_data["Crop"].dropna().unique().tolist()
)


# ============================================================
# CROP RECOMMENDATION CROPS
# ============================================================

ML_CROPS = [
    "Rice",
    "Maize",
    "Chickpea",
    "Kidney Beans",
    "Pigeon Peas",
    "Moth Beans",
    "Mung Bean",
    "Black Gram",
    "Lentil",
    "Pomegranate",
    "Banana",
    "Mango",
    "Grapes",
    "Watermelon",
    "Muskmelon",
    "Apple",
    "Orange",
    "Papaya",
    "Coconut",
    "Cotton",
    "Jute",
    "Coffee",
    "Wheat",
    "Tomato"
]


# ============================================================
# SEARCH & APPLY CONTRACT CROPS
# ============================================================

CROPS = [
    "Rice",
    "Wheat",
    "Maize",
    "Cotton",
    "Tomato"
]


LOCATIONS = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal"
]


# ============================================================
# DATABASE MODELS
# ============================================================

class Farmer(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    farm_area = db.Column(
        db.Float,
        nullable=True
    )

    soil_type = db.Column(
        db.String(50),
        nullable=True
    )

    soil_ph = db.Column(
        db.Float,
        nullable=True
    )


class Contract(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    company = db.Column(
        db.String(150),
        nullable=False
    )

    crop = db.Column(
        db.String(100),
        nullable=False
    )

    location = db.Column(
        db.String(100),
        nullable=False
    )

    price = db.Column(
        db.Float,
        nullable=False
    )


class ContractApplication(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    farmer_id = db.Column(
        db.Integer,
        db.ForeignKey("farmer.id"),
        nullable=False
    )

    contract_id = db.Column(
        db.Integer,
        db.ForeignKey("contract.id"),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Pending",
        nullable=False
    )

    applied_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )

    contract = db.relationship(
        Contract,
        backref="applications"
    )


# ============================================================
# DATABASE CREATION + INITIAL CONTRACT DATA
# ============================================================

# ============================================================
# DATABASE CREATION + INITIAL CONTRACT DATA
# ============================================================

with app.app_context():

    db.create_all()

    initial_contracts = [

        # ====================================================
        # RICE
        # ====================================================

        Contract(
            company="Karnataka Agro Foods",
            crop="Rice",
            location="Karnataka",
            price=25000
        ),

        Contract(
            company="Andhra Grain Partners",
            crop="Rice",
            location="Andhra Pradesh",
            price=27000
        ),

        Contract(
            company="Punjab Rice Collective",
            crop="Rice",
            location="Punjab",
            price=28500
        ),

        Contract(
            company="Tamil Nadu Paddy Foods",
            crop="Rice",
            location="Tamil Nadu",
            price=26000
        ),

        Contract(
            company="Chhattisgarh Rice Network",
            crop="Rice",
            location="Chhattisgarh",
            price=25500
        ),

        # ====================================================
        # WHEAT
        # ====================================================

        Contract(
            company="Northern Grains Pvt Ltd",
            crop="Wheat",
            location="Karnataka",
            price=28000
        ),

        Contract(
            company="Madhya Bharat Grains",
            crop="Wheat",
            location="Madhya Pradesh",
            price=30000
        ),

        Contract(
            company="Punjab Wheat Producers",
            crop="Wheat",
            location="Punjab",
            price=31500
        ),

        Contract(
            company="Haryana Grain Network",
            crop="Wheat",
            location="Haryana",
            price=30500
        ),

        Contract(
            company="Rajasthan Wheat Foods",
            crop="Wheat",
            location="Rajasthan",
            price=29500
        ),

        # ====================================================
        # MAIZE
        # ====================================================

        Contract(
            company="Fresh Produce India",
            crop="Maize",
            location="Karnataka",
            price=22000
        ),

        Contract(
            company="Deccan Maize Foods",
            crop="Maize",
            location="Maharashtra",
            price=24000
        ),

        Contract(
            company="Andhra Maize Collective",
            crop="Maize",
            location="Andhra Pradesh",
            price=23500
        ),

        Contract(
            company="Tamil Nadu Maize Network",
            crop="Maize",
            location="Tamil Nadu",
            price=22500
        ),

        Contract(
            company="Madhya Pradesh Maize Group",
            crop="Maize",
            location="Madhya Pradesh",
            price=24500
        ),

        # ====================================================
        # COTTON
        # ====================================================

        Contract(
            company="Cotton Growers Association",
            crop="Cotton",
            location="Karnataka",
            price=32000
        ),

        Contract(
            company="Maharashtra Cotton Network",
            crop="Cotton",
            location="Maharashtra",
            price=35000
        ),

        Contract(
            company="Gujarat Cotton Partners",
            crop="Cotton",
            location="Gujarat",
            price=36000
        ),

        Contract(
            company="Telangana Cotton Collective",
            crop="Cotton",
            location="Telangana",
            price=34000
        ),

        Contract(
            company="Punjab Cotton Producers",
            crop="Cotton",
            location="Punjab",
            price=33000
        ),

        # ====================================================
        # TOMATO
        # ====================================================

        Contract(
            company="Green Harvest Pvt Ltd",
            crop="Tomato",
            location="Karnataka",
            price=30000
        ),

        Contract(
            company="Maharashtra Fresh Produce",
            crop="Tomato",
            location="Maharashtra",
            price=32500
        ),

        Contract(
            company="Tamil Nadu Vegetable Foods",
            crop="Tomato",
            location="Tamil Nadu",
            price=31500
        ),

        Contract(
            company="Andhra Fresh Farms",
            crop="Tomato",
            location="Andhra Pradesh",
            price=31000
        ),

        Contract(
            company="Telangana Tomato Network",
            crop="Tomato",
            location="Telangana",
            price=30500
        )
    ]

    # ========================================================
    # ADD ONLY MISSING CONTRACTS
    # This keeps existing farmer accounts/applications safe.
    # ========================================================

    for contract in initial_contracts:

        existing_contract = Contract.query.filter_by(
            company=contract.company,
            crop=contract.crop,
            location=contract.location
        ).first()

        if not existing_contract:

            db.session.add(contract)

    db.session.commit()


# ============================================================
# LOGIN REQUIRED DECORATOR
# ============================================================

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "farmer_id" not in session:

            flash(
                "Please login to continue."
            )

            return redirect(
                url_for("login")
            )

        # The saved login may point to a farmer that no longer exists in
        # this database (for example after switching project folders).
        if db.session.get(Farmer, session["farmer_id"]) is None:

            session.clear()

            flash(
                "Your session has expired. Please log in again."
            )

            return redirect(
                url_for("login")
            )

        return f(*args, **kwargs)

    return decorated_function


# ============================================================
# HOME
# ============================================================

@app.route("/")
@login_required
def candidate_home():

    return render_template(
        "candidate_home.html",
        farmer_name=session.get("farmer_name"),
        active="home"
    )


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not name or not email or not password:

            flash(
                "Please fill in all required fields."
            )

            return render_template(
                "register.html"
            )

        existing_farmer = Farmer.query.filter_by(
            email=email
        ).first()

        if existing_farmer:

            flash(
                "An account with this email already exists."
            )

            return render_template(
                "register.html"
            )

        farmer = Farmer(
            name=name,
            email=email,
            password_hash=generate_password_hash(
                password
            )
        )

        db.session.add(farmer)
        db.session.commit()

        flash(
            "Registration successful. Please login."
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        farmer = Farmer.query.filter_by(
            email=email
        ).first()

        if farmer and check_password_hash(
            farmer.password_hash,
            password
        ):

            session["farmer_id"] = farmer.id
            session["farmer_name"] = farmer.name

            flash(
                "Login successful."
            )

            return redirect(
                url_for("candidate_home")
            )

        flash(
            "Invalid email or password."
        )

    return render_template(
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():

    farmer = Farmer.query.get(
        session["farmer_id"]
    )

    recommended_contracts = Contract.query.order_by(
        Contract.id
    ).all()

    applications = ContractApplication.query.filter_by(
        farmer_id=session["farmer_id"]
    ).order_by(
        ContractApplication.id.desc()
    ).all()

    # Latest ML results saved by Crop Selection and Yield Prediction
    crop_result = session.get("dashboard_crop", {})
    yield_result = session.get("dashboard_yield", {})
    recommended_crop = crop_result.get("recommended_crop")

    # Show contracts that match the recommended crop (fall back to all)
    if recommended_crop:
        matching = [
            c for c in recommended_contracts
            if (c.crop or "").strip().lower() == recommended_crop.strip().lower()
        ]
        if matching:
            recommended_contracts = matching

    return render_template(
        "dashboard.html",
        farmer=farmer,
        recommended_crop=recommended_crop,
        predicted_yield=yield_result.get("predicted_yield"),
        total_production=yield_result.get("total_production"),
        farm_area=farmer.farm_area,
        soil_type=farmer.soil_type,
        soil_ph=farmer.soil_ph,
        nitrogen=crop_result.get("nitrogen"),
        phosphorus=crop_result.get("phosphorus"),
        potassium=crop_result.get("potassium"),
        temperature=crop_result.get("temperature"),
        humidity=crop_result.get("humidity"),
        rainfall=crop_result.get("rainfall"),
        applications=applications,
        recommended_contracts=recommended_contracts,
        farmer_name=session.get("farmer_name"),
        active="dashboard"
    )


# ============================================================
# SEARCH & APPLY
# ============================================================
@app.route(
    "/search-apply",
    methods=["GET", "POST"]
)
@login_required
def search_apply():

    crop = ""
    location = ""
    farm_area = ""
    searched = False

    filtered_contracts = Contract.query.order_by(
        Contract.id
    ).all()

    locations = [
        row[0]
        for row in db.session.query(
            Contract.location
        ).distinct().order_by(
            Contract.location
        ).all()
    ]

    # ============================================================
    # GET REQUEST
    # Used when coming from Yield Prediction
    # ============================================================

    if request.method == "GET":

        crop = request.args.get(
            "crop",
            ""
        ).strip()

        location = request.args.get(
            "location",
            ""
        ).strip()

        farm_area = request.args.get(
            "farm_area",
            ""
        ).strip()

        # If a crop was passed from Yield Prediction,
        # automatically filter the contracts.
        if crop or location:

            searched = True

            query = Contract.query

            if crop:

                query = query.filter(
                    db.func.lower(
                        Contract.crop
                    ) == crop.lower()
                )

            if location:

                query = query.filter(
                    db.func.lower(
                        Contract.location
                    ) == location.lower()
                )

            filtered_contracts = query.order_by(
                Contract.id
            ).all()

    # ============================================================
    # POST REQUEST
    # Normal Search & Apply form
    # ============================================================

    if request.method == "POST":

        searched = True

        crop = request.form.get(
            "crop",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        farm_area = request.form.get(
            "farm_area",
            ""
        ).strip()

        query = Contract.query

        if crop:

            query = query.filter(
                db.func.lower(
                    Contract.crop
                ) == crop.lower()
            )

        if location:

            query = query.filter(
                db.func.lower(
                    Contract.location
                ) == location.lower()
            )

        filtered_contracts = query.order_by(
            Contract.id
        ).all()

    return render_template(
        "search_apply.html",
        contracts=filtered_contracts,
        crops=CROPS,
        locations=locations,
        crop=crop,
        location=location,
        farm_area=farm_area,
        searched=searched,
        farmer_name=session.get("farmer_name"),
        active="search_apply"
    )


# ============================================================
# APPLY FOR CONTRACT
# ============================================================

@app.route(
    "/apply/<int:contract_id>",
    methods=["POST"]
)
@login_required
def apply_for_contract(contract_id):

    farmer_id = session["farmer_id"]

    contract = Contract.query.get_or_404(
        contract_id
    )

    existing_application = ContractApplication.query.filter_by(
        farmer_id=farmer_id,
        contract_id=contract_id
    ).first()

    if existing_application:

        flash(
            "You have already applied for this contract."
        )

        return redirect(
            url_for("search_apply")
        )

    application = ContractApplication(
        farmer_id=farmer_id,
        contract_id=contract_id,
        status="Pending"
    )

    db.session.add(application)

    db.session.commit()

    flash(
        f"Application submitted successfully for {contract.company}."
    )

    return redirect(
        url_for("search_apply")
    )


# ============================================================
# CROP SELECTION - MACHINE LEARNING
# ============================================================
@app.route(
    "/crop-selection",
    methods=["GET", "POST"]
)
@login_required
def crop_selection():

    farmer = Farmer.query.get(
        session["farmer_id"]
    )

    prediction = None
    top_crops = []

    farm_area = farmer.farm_area or ""
    soil_type = farmer.soil_type or ""
    soil_ph = farmer.soil_ph or ""

    nitrogen = ""
    phosphorus = ""
    potassium = ""
    temperature = ""
    humidity = ""
    rainfall = ""

    if request.method == "POST":

        farm_area = request.form.get("farm_area", "")
        soil_type = request.form.get("soil_type", "")
        soil_ph = request.form.get("soil_ph", "")

        nitrogen = request.form.get("nitrogen", "")
        phosphorus = request.form.get("phosphorus", "")
        potassium = request.form.get("potassium", "")

        temperature = request.form.get("temperature", "")
        humidity = request.form.get("humidity", "")
        rainfall = request.form.get("rainfall", "")

        try:

            nitrogen_value = float(nitrogen)
            phosphorus_value = float(phosphorus)
            potassium_value = float(potassium)

            temperature_value = float(temperature)
            humidity_value = float(humidity)
            soil_ph_value = float(soil_ph)
            rainfall_value = float(rainfall)

            # Validate input values
            check_crop_inputs({
                "nitrogen": nitrogen_value,
                "phosphorus": phosphorus_value,
                "potassium": potassium_value,
                "temperature": temperature_value,
                "humidity": humidity_value,
                "soil_ph": soil_ph_value,
                "rainfall": rainfall_value
            })

            # Prepare input for the ML model
            input_data = pd.DataFrame([[
              nitrogen_value,
             phosphorus_value,
             potassium_value,
             temperature_value,
             humidity_value,
             soil_ph_value,
             rainfall_value / 12
           ]], columns=[
               "N", "P", "K",
                "temperature", "humidity", "ph", "rainfall"
         ])

            # Predict the highest-ranked crop
            prediction = crop_model.predict(
                input_data
            )[0]

            prediction = str(prediction)

            # Get suitability scores for all crop classes
            probabilities = crop_model.predict_proba(
                input_data
            )[0]

            # Rank all crops from highest to lowest score
            ranked = sorted(
                zip(crop_model.classes_, probabilities),
                key=lambda item: item[1],
                reverse=True
            )

            # Store all 24 crop recommendations
            top_crops = [
                {
                    "name": str(name),
                    "confidence": round(float(prob) * 100, 1)
                }
                for name, prob in ranked
            ]

            # Update farmer profile
            try:
                farmer.farm_area = float(farm_area)
            except (ValueError, TypeError):
                pass

            farmer.soil_type = soil_type

            try:
                farmer.soil_ph = float(soil_ph)
            except (ValueError, TypeError):
                pass

            db.session.commit()

            # Save result for dashboard
            session["dashboard_crop"] = {
                "recommended_crop": prediction,
                "nitrogen": nitrogen_value,
                "phosphorus": phosphorus_value,
                "potassium": potassium_value,
                "temperature": temperature_value,
                "humidity": humidity_value,
                "rainfall": rainfall_value
            }

        except InputRangeError as range_error:

            flash(str(range_error))

        except (
            ValueError,
            TypeError,
            KeyError
        ):

            flash(
                "Please enter valid numerical values."
            )

    return render_template(
        "crop_selection.html",
        recommendation=prediction,
        top_crops=top_crops,
        farm_area=farm_area,
        soil_type=soil_type,
        soil_ph=soil_ph,
        nitrogen=nitrogen,
        phosphorus=phosphorus,
        potassium=potassium,
        temperature=temperature,
        humidity=humidity,
        rainfall=rainfall,
        crops=ML_CROPS,
        farmer_name=session.get("farmer_name"),
        active="crop_selection"
    )
@app.route(
    "/technical-guidelines",
    methods=["GET", "POST"]
)
@login_required
def technical_guidelines():

    crops = ML_CROPS

    crop = request.args.get(
        "crop",
        ""
    ).strip()

    if request.method == "POST":

        crop = request.form.get(
            "crop",
            ""
        ).strip()

    if crop not in crops:

        crop = crops[0]


    technical_guidelines_data = {

        "Rice": {
            "icon": "🌾",
            "stage": "Land Preparation → Sowing → Tillering → Flowering → Grain Filling → Harvest",
            "water": "Maintain suitable field moisture, especially during tillering, flowering and grain filling. Avoid unnecessary prolonged waterlogging.",
            "soil": "Fertile soil with good water-holding capacity and suitable drainage. Maintain balanced soil fertility.",
            "nutrients": "Nitrogen, phosphorus and potassium should be managed according to soil condition and crop stage.",
            "pests": "Monitor regularly for stem borers, leaf folders, planthoppers and other common rice pests.",
            "weather": "Monitor rainfall, temperature and humidity because excessive moisture can increase disease pressure.",
            "actions": [
                "Prepare and level the field before planting.",
                "Use healthy and suitable-quality seed.",
                "Maintain appropriate water levels during early crop establishment.",
                "Control weeds before they compete strongly with the crop.",
                "Monitor nutrient requirements during vegetative growth.",
                "Inspect regularly for insects and disease symptoms.",
                "Maintain suitable moisture during flowering and grain filling.",
                "Harvest when grains reach appropriate maturity."
            ],
            "warnings": [
                "Excessive standing water outside the required crop stage.",
                "Sudden pest population increases.",
                "Yellowing or abnormal leaf growth.",
                "Disease symptoms developing after prolonged wet weather."
            ]
        },


        "Maize": {
            "icon": "🌽",
            "stage": "Land Preparation → Sowing → Vegetative Growth → Tasseling → Silking → Grain Filling → Harvest",
            "water": "Maintain adequate moisture during germination, rapid vegetative growth, tasseling, silking and grain filling.",
            "soil": "Well-drained fertile soil with good organic matter and suitable nutrient availability.",
            "nutrients": "Nitrogen is particularly important during vegetative growth. Phosphorus and potassium support root and reproductive development.",
            "pests": "Monitor for stem borers, fall armyworm and other chewing or sucking pests.",
            "weather": "Watch for drought stress around tasseling and silking and excessive rainfall that may cause waterlogging.",
            "actions": [
                "Prepare a well-drained seedbed.",
                "Sow quality seed at recommended depth and spacing.",
                "Control weeds during early crop establishment.",
                "Apply nutrients according to soil and crop requirements.",
                "Monitor plants during rapid vegetative growth.",
                "Inspect tasseling and silking plants for pest damage.",
                "Maintain suitable moisture during grain filling.",
                "Harvest when cobs and grains reach appropriate maturity."
            ],
            "warnings": [
                "Leaf damage caused by caterpillars or borers.",
                "Severe moisture stress during tasseling.",
                "Waterlogging around plant roots.",
                "Premature drying or poor grain development."
            ]
        },


        "Chickpea": {
            "icon": "🌱",
            "stage": "Land Preparation → Sowing → Vegetative Growth → Flowering → Pod Formation → Maturity → Harvest",
            "water": "Chickpea generally requires controlled irrigation. Avoid excessive moisture and waterlogging.",
            "soil": "Well-drained soil with suitable fertility is preferred. Avoid poorly drained fields.",
            "nutrients": "Balanced phosphorus, potassium and other nutrients should be maintained based on soil conditions.",
            "pests": "Monitor particularly for pod borers, aphids and other insects during flowering and pod development.",
            "weather": "Cool and relatively dry conditions are generally favourable. Excess humidity can increase disease risk.",
            "actions": [
                "Prepare a well-drained seedbed.",
                "Use healthy, quality seed.",
                "Monitor germination and early plant establishment.",
                "Control weeds before they compete with the crop.",
                "Monitor flowering plants carefully.",
                "Inspect developing pods for insect damage.",
                "Avoid excessive irrigation near maturity.",
                "Harvest after plants and pods reach suitable maturity."
            ],
            "warnings": [
                "Waterlogging after irrigation or heavy rainfall.",
                "Pod damage caused by insects.",
                "Leaf spots or fungal symptoms.",
                "Excessive vegetative growth with poor pod formation."
            ]
        },


        "Kidney Beans": {
            "icon": "🫘",
            "stage": "Land Preparation → Sowing → Germination → Vegetative Growth → Flowering → Pod Development → Harvest",
            "water": "Maintain consistent soil moisture while avoiding prolonged waterlogging.",
            "soil": "Loose, fertile and well-drained soil supports healthy root and plant development.",
            "nutrients": "Balanced nutrient management is important, particularly during vegetative and reproductive growth.",
            "pests": "Monitor for aphids, bean beetles, caterpillars and other common bean pests.",
            "weather": "Avoid excessive heat and moisture stress during flowering and pod formation.",
            "actions": [
                "Prepare loose and well-drained soil.",
                "Sow healthy seed at suitable depth.",
                "Monitor germination carefully.",
                "Remove weeds during early growth.",
                "Maintain adequate moisture during flowering.",
                "Monitor developing pods for pests.",
                "Avoid excessive irrigation near maturity.",
                "Harvest mature pods at the correct stage."
            ],
            "warnings": [
                "Persistent waterlogging.",
                "Leaf yellowing or poor plant growth.",
                "Heavy pest infestation.",
                "Premature pod drying."
            ]
        },


        "Pigeon Peas": {
            "icon": "🌱",
            "stage": "Land Preparation → Sowing → Vegetative Growth → Flowering → Pod Development → Maturity → Harvest",
            "water": "Provide moisture when required but avoid excessive irrigation and waterlogging.",
            "soil": "Well-drained soil with good fertility is preferred.",
            "nutrients": "Maintain balanced soil fertility and monitor plant growth for nutrient deficiencies.",
            "pests": "Regularly inspect flowering and pod stages for pod borers and other insects.",
            "weather": "Monitor rainfall and prolonged humidity because excessive moisture may increase disease pressure.",
            "actions": [
                "Prepare the field before sowing.",
                "Use quality seed and suitable spacing.",
                "Control weeds during early growth.",
                "Monitor vegetative development.",
                "Inspect flowering plants regularly.",
                "Monitor pod formation for pest damage.",
                "Maintain suitable soil moisture.",
                "Harvest mature pods at the correct stage."
            ],
            "warnings": [
                "Pod borer damage.",
                "Excessive water accumulation.",
                "Sudden leaf yellowing.",
                "Disease symptoms during prolonged wet weather."
            ]
        },


        "Moth Beans": {
            "icon": "🌱",
            "stage": "Land Preparation → Sowing → Germination → Vegetative Growth → Flowering → Pod Formation → Harvest",
            "water": "Moth bean is relatively drought tolerant but needs suitable moisture during establishment and reproductive stages.",
            "soil": "Well-drained soil is preferred, particularly in areas with irregular rainfall.",
            "nutrients": "Maintain balanced fertility according to soil conditions.",
            "pests": "Inspect regularly for pod and foliage pests.",
            "weather": "Avoid excessive moisture and monitor crops during periods of heavy rainfall.",
            "actions": [
                "Prepare the field and remove weeds.",
                "Sow quality seed at suitable depth.",
                "Monitor germination.",
                "Control weeds during early growth.",
                "Inspect plants during flowering.",
                "Monitor developing pods.",
                "Avoid unnecessary irrigation.",
                "Harvest when pods reach maturity."
            ],
            "warnings": [
                "Waterlogging.",
                "Severe insect damage.",
                "Poor germination.",
                "Disease symptoms after prolonged rainfall."
            ]
        },


        "Mung Bean": {
            "icon": "🌱",
            "stage": "Land Preparation → Sowing → Germination → Vegetative Growth → Flowering → Pod Development → Harvest",
            "water": "Provide adequate moisture during establishment and flowering while avoiding excessive irrigation.",
            "soil": "Well-drained fertile soil is preferred.",
            "nutrients": "Balanced nutrient availability supports vegetative growth and pod formation.",
            "pests": "Monitor for whiteflies, aphids, pod borers and other common pests.",
            "weather": "Monitor rainfall and humidity because wet conditions may encourage disease development.",
            "actions": [
                "Prepare a fine seedbed.",
                "Sow healthy seed.",
                "Monitor germination.",
                "Control weeds early.",
                "Monitor flowering plants.",
                "Inspect pods for insect damage.",
                "Maintain suitable moisture.",
                "Harvest mature pods promptly."
            ],
            "warnings": [
                "Rapid pest increase.",
                "Excessive rainfall.",
                "Leaf yellowing.",
                "Pod damage."
            ]
        },


        "Black Gram": {
            "icon": "🌱",
            "stage": "Land Preparation → Sowing → Germination → Vegetative Growth → Flowering → Pod Development → Harvest",
            "water": "Maintain moderate soil moisture and avoid waterlogging.",
            "soil": "Fertile and well-drained soil supports good black gram production.",
            "nutrients": "Maintain balanced nutrients based on soil testing and crop condition.",
            "pests": "Monitor for sucking pests, pod borers and other insect damage.",
            "weather": "High humidity and excessive rainfall may increase disease pressure.",
            "actions": [
                "Prepare a suitable seedbed.",
                "Sow quality seed.",
                "Monitor germination.",
                "Control weeds.",
                "Maintain appropriate moisture.",
                "Inspect flowering plants.",
                "Monitor pods for pest damage.",
                "Harvest when the majority of pods mature."
            ],
            "warnings": [
                "Waterlogging.",
                "Leaf disease symptoms.",
                "Heavy insect activity.",
                "Uneven maturity."
            ]
        },


        "Lentil": {
            "icon": "🌱",
            "stage": "Land Preparation → Sowing → Vegetative Growth → Flowering → Pod Formation → Maturity → Harvest",
            "water": "Avoid excessive irrigation. Moderate moisture is generally sufficient.",
            "soil": "Well-drained soil with suitable fertility is preferred.",
            "nutrients": "Balanced phosphorus, potassium and other nutrients should be maintained according to soil conditions.",
            "pests": "Monitor for aphids, pod borers and fungal disease symptoms.",
            "weather": "Cooler conditions are generally suitable, while excessive humidity can increase disease risk.",
            "actions": [
                "Prepare a fine and well-drained seedbed.",
                "Sow quality lentil seed.",
                "Monitor early plant establishment.",
                "Control weeds.",
                "Monitor flowering.",
                "Inspect developing pods.",
                "Reduce irrigation near maturity.",
                "Harvest after plants become suitably mature."
            ],
            "warnings": [
                "Excessive irrigation.",
                "Fungal disease symptoms.",
                "Aphid infestation.",
                "Premature crop drying."
            ]
        },


        "Pomegranate": {
            "icon": "🍎",
            "stage": "Site Preparation → Planting → Establishment → Vegetative Growth → Flowering → Fruit Development → Harvest",
            "water": "Maintain consistent moisture, particularly during establishment and fruit development. Avoid waterlogging.",
            "soil": "Deep, fertile and well-drained soil is preferred.",
            "nutrients": "Apply balanced nutrients based on tree age, soil condition and fruiting stage.",
            "pests": "Monitor for fruit borer, aphids, mites and other common orchard pests.",
            "weather": "Monitor humidity and rainfall because they can influence fungal and fruit-related problems.",
            "actions": [
                "Select a suitable orchard site.",
                "Prepare planting pits properly.",
                "Plant healthy saplings.",
                "Maintain weed-free conditions around trees.",
                "Train and prune trees appropriately.",
                "Monitor flowering and fruit set.",
                "Protect developing fruits.",
                "Harvest mature fruits carefully."
            ],
            "warnings": [
                "Fruit cracking.",
                "Borer damage.",
                "Excessive humidity.",
                "Poor drainage around tree roots."
            ]
        },


        "Banana": {
            "icon": "🍌",
            "stage": "Land Preparation → Planting → Establishment → Vegetative Growth → Flowering → Bunch Development → Harvest",
            "water": "Banana requires regular moisture but does not tolerate prolonged waterlogging.",
            "soil": "Deep, fertile and well-drained soil with good organic matter is suitable.",
            "nutrients": "Balanced nutrient management is essential because banana has relatively high nutrient demand.",
            "pests": "Monitor for rhizome pests, thrips, aphids and other common banana pests.",
            "weather": "Strong winds and extreme moisture conditions can damage banana plants.",
            "actions": [
                "Prepare fertile planting pits.",
                "Use healthy planting material.",
                "Provide regular irrigation.",
                "Control weeds around plants.",
                "Apply nutrients according to crop requirements.",
                "Support plants when necessary.",
                "Monitor bunch development.",
                "Harvest at suitable maturity."
            ],
            "warnings": [
                "Waterlogging.",
                "Strong wind damage.",
                "Leaf disease.",
                "Poor bunch development."
            ]
        },


        "Mango": {
            "icon": "🥭",
            "stage": "Site Preparation → Planting → Establishment → Vegetative Growth → Flowering → Fruit Development → Harvest",
            "water": "Young trees require regular irrigation; mature trees need careful irrigation management according to rainfall and fruit stage.",
            "soil": "Deep, well-drained soil with suitable fertility supports healthy mango trees.",
            "nutrients": "Apply nutrients according to tree age, soil condition and fruiting requirements.",
            "pests": "Monitor for fruit flies, hoppers, mealybugs and other orchard pests.",
            "weather": "Flowering and fruit development are influenced by temperature, rainfall and humidity.",
            "actions": [
                "Select suitable planting material.",
                "Prepare orchard pits.",
                "Plant healthy grafted saplings.",
                "Maintain weed-free tree basins.",
                "Prune and train trees appropriately.",
                "Monitor flowering.",
                "Protect developing fruits.",
                "Harvest mature fruits carefully."
            ],
            "warnings": [
                "Fruit fly infestation.",
                "Flowering damage.",
                "Excessive humidity.",
                "Waterlogging."
            ]
        },


        "Grapes": {
            "icon": "🍇",
            "stage": "Planting → Training → Vegetative Growth → Flowering → Fruit Set → Berry Development → Harvest",
            "water": "Irrigation should be managed carefully to maintain suitable vine growth and fruit quality.",
            "soil": "Well-drained soil is important because grape roots are sensitive to prolonged waterlogging.",
            "nutrients": "Balanced nutrition should be adjusted according to vine growth and fruit development.",
            "pests": "Monitor for mealybugs, thrips, mites and fungal diseases.",
            "weather": "High humidity and prolonged rainfall can increase fungal disease pressure.",
            "actions": [
                "Prepare the site and support system.",
                "Plant healthy vines.",
                "Train vines onto the support structure.",
                "Manage canopy growth.",
                "Monitor flowering and fruit set.",
                "Protect berries from pests and disease.",
                "Manage irrigation during fruit development.",
                "Harvest bunches at suitable maturity."
            ],
            "warnings": [
                "Fungal infection after rainfall.",
                "Excessive canopy humidity.",
                "Berry cracking.",
                "Pest infestation."
            ]
        },


        "Watermelon": {
            "icon": "🍉",
            "stage": "Land Preparation → Sowing → Vine Growth → Flowering → Fruit Set → Fruit Development → Harvest",
            "water": "Maintain consistent moisture, especially during flowering and fruit development, while avoiding waterlogging.",
            "soil": "Loose, fertile and well-drained soil is preferred.",
            "nutrients": "Balanced nutrients are required for vigorous vines and fruit development.",
            "pests": "Monitor for aphids, beetles, fruit flies and other pests.",
            "weather": "Warm conditions generally support growth, while excessive rainfall may increase disease pressure.",
            "actions": [
                "Prepare loose fertile soil.",
                "Sow healthy seeds.",
                "Monitor seedling establishment.",
                "Control weeds.",
                "Manage irrigation during vine growth.",
                "Monitor flowering and fruit set.",
                "Protect developing fruits.",
                "Harvest according to maturity indicators."
            ],
            "warnings": [
                "Waterlogging.",
                "Fruit damage.",
                "Sudden wilting.",
                "Pest infestation."
            ]
        },


        "Muskmelon": {
            "icon": "🍈",
            "stage": "Land Preparation → Sowing → Vine Growth → Flowering → Fruit Set → Fruit Development → Harvest",
            "water": "Maintain consistent moisture during growth but reduce unnecessary irrigation near maturity.",
            "soil": "Well-drained sandy loam or similar loose soil is generally suitable.",
            "nutrients": "Balanced nutrition supports vine growth and fruit development.",
            "pests": "Monitor for aphids, fruit flies, beetles and mites.",
            "weather": "Warm and relatively dry conditions are generally favourable.",
            "actions": [
                "Prepare loose and fertile soil.",
                "Sow quality seed.",
                "Monitor seedling growth.",
                "Control weeds.",
                "Maintain suitable irrigation.",
                "Monitor flowers and fruit set.",
                "Protect developing fruits.",
                "Harvest when fruits reach suitable maturity."
            ],
            "warnings": [
                "Excessive irrigation.",
                "Fruit cracking.",
                "Fungal disease.",
                "Insect damage."
            ]
        },


        "Apple": {
            "icon": "🍎",
            "stage": "Site Preparation → Planting → Establishment → Vegetative Growth → Flowering → Fruit Development → Harvest",
            "water": "Maintain suitable soil moisture during active growth and fruit development without waterlogging.",
            "soil": "Deep, fertile and well-drained soil is preferred.",
            "nutrients": "Balanced nutrient management should consider tree age, soil testing and fruit load.",
            "pests": "Monitor for aphids, mites, fruit moths and other orchard pests.",
            "weather": "Apple performance strongly depends on suitable temperature and climatic conditions for the selected variety.",
            "actions": [
                "Select a suitable variety and site.",
                "Prepare planting pits.",
                "Plant healthy grafted saplings.",
                "Train and prune the trees.",
                "Maintain balanced nutrition.",
                "Monitor flowering and pollination.",
                "Protect developing fruits.",
                "Harvest at appropriate maturity."
            ],
            "warnings": [
                "Frost damage during flowering.",
                "Pest infestation.",
                "Fungal disease.",
                "Poor drainage."
            ]
        },


        "Orange": {
            "icon": "🍊",
            "stage": "Site Preparation → Planting → Establishment → Vegetative Growth → Flowering → Fruit Development → Harvest",
            "water": "Maintain regular irrigation during dry periods while preventing waterlogging.",
            "soil": "Well-drained fertile soil is preferred for citrus production.",
            "nutrients": "Balanced nitrogen, phosphorus, potassium and micronutrients support tree health and fruit production.",
            "pests": "Monitor for citrus psylla, aphids, mites, fruit flies and other pests.",
            "weather": "Monitor temperature, rainfall and humidity throughout flowering and fruit development.",
            "actions": [
                "Select a suitable orchard site.",
                "Plant healthy citrus saplings.",
                "Maintain weed-free tree basins.",
                "Apply nutrients according to tree requirements.",
                "Monitor flowering.",
                "Inspect fruits for pest damage.",
                "Maintain appropriate irrigation.",
                "Harvest mature fruits carefully."
            ],
            "warnings": [
                "Leaf curling or unusual leaf growth.",
                "Fruit damage.",
                "Waterlogging.",
                "Pest infestation."
            ]
        },


        "Papaya": {
            "icon": "🍈",
            "stage": "Land Preparation → Planting → Establishment → Vegetative Growth → Flowering → Fruit Development → Harvest",
            "water": "Provide regular moisture while maintaining excellent drainage.",
            "soil": "Fertile, loose and well-drained soil is essential.",
            "nutrients": "Regular balanced nutrition supports rapid vegetative and fruit development.",
            "pests": "Monitor for mites, aphids, fruit flies and other pests.",
            "weather": "Warm conditions are generally suitable, but excessive rain can increase disease risk.",
            "actions": [
                "Prepare well-drained planting pits.",
                "Plant healthy seedlings.",
                "Maintain irrigation.",
                "Control weeds.",
                "Apply nutrients according to crop growth.",
                "Monitor flowering and fruit set.",
                "Inspect developing fruits.",
                "Harvest fruits at suitable maturity."
            ],
            "warnings": [
                "Waterlogging.",
                "Leaf curl.",
                "Fruit damage.",
                "Sudden plant wilting."
            ]
        },


        "Coconut": {
            "icon": "🥥",
            "stage": "Site Preparation → Planting → Establishment → Vegetative Growth → Flowering → Nut Development → Harvest",
            "water": "Provide adequate irrigation during dry periods, particularly for young palms.",
            "soil": "Deep, fertile and well-drained soil supports healthy root development.",
            "nutrients": "Balanced macro- and micronutrients should be supplied according to soil and palm age.",
            "pests": "Monitor for rhinoceros beetle, red palm weevil and other palm pests.",
            "weather": "Monitor drought, heavy rainfall and strong winds that may affect palms.",
            "actions": [
                "Select a suitable planting site.",
                "Prepare pits and plant healthy seedlings.",
                "Maintain adequate moisture during establishment.",
                "Keep the palm basin free from excessive weeds.",
                "Apply nutrients according to palm requirements.",
                "Monitor flowering and nut formation.",
                "Inspect palms regularly for pests.",
                "Harvest mature nuts according to intended use."
            ],
            "warnings": [
                "Palm pest infestation.",
                "Severe drought stress.",
                "Waterlogging.",
                "Strong wind damage."
            ]
        },


        "Cotton": {
            "icon": "🌿",
            "stage": "Land Preparation → Sowing → Vegetative Growth → Flowering → Boll Formation → Boll Opening → Picking",
            "water": "Maintain suitable moisture during establishment, flowering and boll development while avoiding excessive water.",
            "soil": "Deep, fertile and well-drained soil supports cotton growth.",
            "nutrients": "Balanced nitrogen, phosphorus and potassium management is important for healthy plants and boll formation.",
            "pests": "Regularly monitor for sucking pests and bollworm-related damage.",
            "weather": "Monitor rainfall and humidity because excessive moisture can increase disease risk.",
            "actions": [
                "Prepare the field properly.",
                "Sow quality cotton seed.",
                "Control early weeds.",
                "Monitor vegetative growth.",
                "Scout regularly during flowering.",
                "Inspect developing bolls.",
                "Monitor pest populations.",
                "Pick fully opened bolls at suitable intervals."
            ],
            "warnings": [
                "Boll damage.",
                "Sucking pest infestation.",
                "Excessive vegetative growth.",
                "Waterlogging."
            ]
        },


        "Jute": {
            "icon": "🌿",
            "stage": "Land Preparation → Sowing → Seedling Growth → Vegetative Growth → Stem Development → Maturity → Harvest",
            "water": "Maintain adequate moisture during establishment and active growth without prolonged waterlogging.",
            "soil": "Fertile soil with adequate moisture supports good fibre production.",
            "nutrients": "Balanced nutrient availability supports strong stem growth and fibre development.",
            "pests": "Monitor foliage for insect damage and disease symptoms.",
            "weather": "Warm and humid conditions generally favour growth, but excessive moisture can increase disease risk.",
            "actions": [
                "Prepare a fine seedbed.",
                "Sow quality seed.",
                "Thin overcrowded seedlings.",
                "Control weeds.",
                "Maintain suitable moisture.",
                "Monitor stem development.",
                "Inspect plants for pests and disease.",
                "Harvest at suitable fibre maturity."
            ],
            "warnings": [
                "Excessive weed competition.",
                "Poor plant population.",
                "Disease after heavy rainfall.",
                "Premature harvesting."
            ]
        },


        "Coffee": {
            "icon": "☕",
            "stage": "Planting → Establishment → Vegetative Growth → Flowering → Berry Formation → Ripening → Harvest",
            "water": "Maintain suitable soil moisture, particularly during dry periods and important flowering and berry-development stages.",
            "soil": "Deep, fertile and well-drained soil rich in organic matter is preferred.",
            "nutrients": "Balanced nutrient management should consider soil condition, plant age and expected yield.",
            "pests": "Monitor for coffee berry borer, stem borers and other pests.",
            "weather": "Coffee benefits from suitable temperature, shade and rainfall patterns. Excessive humidity may encourage fungal problems.",
            "actions": [
                "Select suitable planting material.",
                "Prepare the plantation with appropriate shade.",
                "Maintain soil moisture and organic matter.",
                "Prune and manage shade trees.",
                "Monitor flowering.",
                "Inspect berries for pest damage.",
                "Maintain nutrition during berry development.",
                "Harvest ripe cherries selectively."
            ],
            "warnings": [
                "Coffee berry borer damage.",
                "Excessive humidity.",
                "Drought stress.",
                "Poor shade management."
            ]
        },


        "Wheat": {
            "icon": "🌾",
            "stage": "Land Preparation → Sowing → Germination → Tillering → Flowering → Grain Filling → Harvest",
            "water": "Provide irrigation at important growth stages such as establishment, tillering and grain filling according to soil and weather conditions.",
            "soil": "Well-prepared fertile soil with suitable drainage is preferred.",
            "nutrients": "Nitrogen is important for vegetative growth while phosphorus and potassium support root and grain development.",
            "pests": "Monitor for aphids, termites and other crop pests and inspect regularly for disease symptoms.",
            "weather": "Temperature during flowering and grain filling can strongly influence yield and grain quality.",
            "actions": [
                "Prepare a fine and level seedbed.",
                "Use certified quality seed.",
                "Sow at recommended depth and spacing.",
                "Control weeds during early growth.",
                "Monitor tillering and crop nutrition.",
                "Provide irrigation at important growth stages.",
                "Monitor for pests and diseases.",
                "Harvest when grains reach appropriate maturity."
            ],
            "warnings": [
                "Moisture stress during grain filling.",
                "Rust or other disease symptoms.",
                "Heavy weed competition.",
                "Lodging before harvest."
            ]
        },


        "Tomato": {
            "icon": "🍅",
            "stage": "Nursery → Transplanting → Vegetative Growth → Flowering → Fruit Set → Fruit Development → Harvest",
            "water": "Maintain consistent soil moisture and avoid irregular irrigation that can contribute to fruit problems.",
            "soil": "Fertile, well-drained soil with good organic matter is preferred.",
            "nutrients": "Balanced nutrients are important during vegetative growth, flowering and fruit development.",
            "pests": "Monitor for fruit borer, whiteflies, aphids, mites and other common tomato pests.",
            "weather": "Monitor temperature, humidity and rainfall because environmental conditions influence flowering and disease development.",
            "actions": [
                "Raise healthy seedlings in a suitable nursery.",
                "Prepare the field before transplanting.",
                "Transplant healthy seedlings at recommended spacing.",
                "Control weeds and maintain irrigation.",
                "Monitor flowering and fruit set.",
                "Support plants where required.",
                "Inspect fruits for pest and disease damage.",
                "Harvest according to the required maturity stage."
            ],
            "warnings": [
                "Leaf curl or abnormal leaf growth.",
                "Fruit borer damage.",
                "Fungal disease after prolonged wet weather.",
                "Irregular irrigation and fruit cracking."
            ]
        }
    }


    guideline = technical_guidelines_data.get(
        crop
    )

    if guideline is None:

        crop = "Rice"

        guideline = technical_guidelines_data["Rice"]


    return render_template(
        "technical_guidelines.html",

        crops=crops,

        crop=crop,

        guideline=guideline,

        farmer_name=session.get("farmer_name"),

        active="technical_guidelines"
    )

# ============================================================
# FARMING SCHEDULE
# ============================================================

@app.route(
    "/farming-schedule",
    methods=["GET", "POST"]
)
@login_required
def farming_schedule():

    crop = ""

    schedule = None

    tips = None

    farming_schedules = {

        "Rice": [
            {
                "day": "Land Preparation",
                "task": "Prepare the field by ploughing and levelling the soil. Maintain suitable soil moisture before planting."
            },
            {
                "day": "Sowing / Nursery",
                "task": "Use healthy seeds and establish seedlings or direct sowing according to the cultivation method."
            },
            {
                "day": "Early Growth",
                "task": "Maintain adequate soil moisture and control weeds during early crop establishment."
            },
            {
                "day": "Vegetative Stage",
                "task": "Apply recommended nutrients and maintain proper water management for healthy tillering."
            },
            {
                "day": "Reproductive Stage",
                "task": "Maintain consistent irrigation during panicle development and flowering."
            },
            {
                "day": "Grain Filling",
                "task": "Monitor crop health, pests and diseases while maintaining suitable field moisture."
            },
            {
                "day": "Harvesting",
                "task": "Harvest when grains reach appropriate maturity and moisture conditions."
            }
        ],

        "Maize": [
            {
                "day": "Land Preparation",
                "task": "Plough and level the field. Prepare a well-drained seedbed with suitable soil moisture."
            },
            {
                "day": "Sowing",
                "task": "Sow healthy maize seeds at suitable spacing and depth."
            },
            {
                "day": "Early Growth",
                "task": "Maintain soil moisture and remove weeds competing with young plants."
            },
            {
                "day": "Vegetative Growth",
                "task": "Apply recommended nitrogen and other nutrients according to crop requirements."
            },
            {
                "day": "Tasseling & Silking",
                "task": "Maintain adequate irrigation and closely monitor for pest attacks."
            },
            {
                "day": "Grain Development",
                "task": "Maintain crop health and monitor grain filling and disease symptoms."
            },
            {
                "day": "Harvesting",
                "task": "Harvest when cobs and grains reach suitable maturity and moisture."
            }
        ],

        "Chickpea": [
            {
                "day": "Land Preparation",
                "task": "Prepare a fine, well-drained seedbed and avoid excessive soil moisture."
            },
            {
                "day": "Sowing",
                "task": "Use healthy, quality seeds and maintain suitable plant spacing."
            },
            {
                "day": "Seedling Stage",
                "task": "Monitor germination and control early weeds."
            },
            {
                "day": "Vegetative Stage",
                "task": "Maintain moderate soil moisture and monitor nutrient requirements."
            },
            {
                "day": "Flowering",
                "task": "Monitor irrigation carefully and inspect plants for pod borer and other pests."
            },
            {
                "day": "Pod Development",
                "task": "Protect developing pods from pest and disease damage."
            },
            {
                "day": "Harvesting",
                "task": "Harvest when plants dry and pods turn mature brown."
            }
        ],

        "Kidney Beans": [
            {
                "day": "Land Preparation",
                "task": "Prepare a loose, well-drained soil bed with adequate organic matter."
            },
            {
                "day": "Sowing",
                "task": "Plant healthy seeds at suitable depth and spacing."
            },
            {
                "day": "Germination",
                "task": "Maintain adequate moisture without waterlogging."
            },
            {
                "day": "Vegetative Stage",
                "task": "Control weeds and provide balanced nutrients for healthy plant growth."
            },
            {
                "day": "Flowering",
                "task": "Maintain consistent moisture and monitor plants for insect damage."
            },
            {
                "day": "Pod Development",
                "task": "Monitor pod formation and protect the crop from diseases."
            },
            {
                "day": "Harvesting",
                "task": "Harvest when pods and plants reach appropriate maturity and begin drying."
            }
        ],

        "Pigeon Peas": [
            {
                "day": "Land Preparation",
                "task": "Prepare well-drained soil and remove weeds before planting."
            },
            {
                "day": "Sowing",
                "task": "Sow quality seeds at suitable spacing according to the variety."
            },
            {
                "day": "Early Growth",
                "task": "Control weeds and maintain appropriate soil moisture."
            },
            {
                "day": "Vegetative Growth",
                "task": "Monitor plant development and provide nutrients when required."
            },
            {
                "day": "Flowering",
                "task": "Monitor flowering plants for pod borer and other pests."
            },
            {
                "day": "Pod Formation",
                "task": "Protect pods from insects and maintain suitable field conditions."
            },
            {
                "day": "Harvesting",
                "task": "Harvest mature pods when they reach the appropriate dry stage."
            }
        ],

        "Moth Beans": [
            {
                "day": "Land Preparation",
                "task": "Prepare a well-drained field and remove existing weeds."
            },
            {
                "day": "Sowing",
                "task": "Sow healthy seeds at suitable spacing and shallow depth."
            },
            {
                "day": "Germination",
                "task": "Ensure adequate moisture during germination while avoiding waterlogging."
            },
            {
                "day": "Vegetative Stage",
                "task": "Control weeds and monitor crop growth."
            },
            {
                "day": "Flowering",
                "task": "Monitor plants for insect pests and maintain suitable soil moisture."
            },
            {
                "day": "Pod Development",
                "task": "Inspect pods and plants regularly for pest and disease symptoms."
            },
            {
                "day": "Harvesting",
                "task": "Harvest when pods become mature and dry."
            }
        ],

        "Mung Bean": [
            {
                "day": "Land Preparation",
                "task": "Prepare a fine and well-drained seedbed."
            },
            {
                "day": "Sowing",
                "task": "Sow quality mung bean seeds at suitable spacing."
            },
            {
                "day": "Early Growth",
                "task": "Maintain suitable moisture and control weeds."
            },
            {
                "day": "Vegetative Stage",
                "task": "Monitor crop growth and maintain balanced nutrient availability."
            },
            {
                "day": "Flowering",
                "task": "Monitor flowering plants for insect pests and moisture stress."
            },
            {
                "day": "Pod Formation",
                "task": "Protect developing pods from pests and diseases."
            },
            {
                "day": "Harvesting",
                "task": "Harvest mature pods in stages to reduce shattering losses."
            }
        ],

        "Black Gram": [
            {
                "day": "Land Preparation",
                "task": "Prepare a loose, well-drained field and remove weeds."
            },
            {
                "day": "Sowing",
                "task": "Sow healthy black gram seeds at suitable depth and spacing."
            },
            {
                "day": "Germination",
                "task": "Maintain sufficient moisture without excessive irrigation."
            },
            {
                "day": "Vegetative Stage",
                "task": "Control weeds and monitor crop nutrition."
            },
            {
                "day": "Flowering",
                "task": "Monitor for insect pests and avoid moisture stress."
            },
            {
                "day": "Pod Development",
                "task": "Inspect developing pods and manage pest and disease problems."
            },
            {
                "day": "Harvesting",
                "task": "Harvest when most pods become mature and dry."
            }
        ],

        "Lentil": [
            {
                "day": "Land Preparation",
                "task": "Prepare a fine, well-drained seedbed suitable for pulse cultivation."
            },
            {
                "day": "Sowing",
                "task": "Sow quality lentil seeds at recommended spacing."
            },
            {
                "day": "Germination",
                "task": "Monitor emergence and control early weeds."
            },
            {
                "day": "Vegetative Stage",
                "task": "Maintain suitable soil moisture and monitor crop development."
            },
            {
                "day": "Flowering",
                "task": "Monitor the crop for pest and disease symptoms."
            },
            {
                "day": "Pod Development",
                "task": "Protect pods and avoid excessive irrigation near maturity."
            },
            {
                "day": "Harvesting",
                "task": "Harvest when plants turn yellow-brown and pods become mature."
            }
        ],

        "Pomegranate": [
            {
                "day": "Site Preparation",
                "task": "Select a well-drained site and prepare planting pits with suitable organic matter."
            },
            {
                "day": "Planting",
                "task": "Plant healthy pomegranate saplings at appropriate spacing."
            },
            {
                "day": "Establishment",
                "task": "Provide regular irrigation and protect young plants from weeds."
            },
            {
                "day": "Vegetative Growth",
                "task": "Train and prune plants to establish a strong canopy structure."
            },
            {
                "day": "Flowering",
                "task": "Monitor flowering and maintain consistent moisture conditions."
            },
            {
                "day": "Fruit Development",
                "task": "Monitor fruit growth, pests and diseases while maintaining irrigation."
            },
            {
                "day": "Harvesting",
                "task": "Harvest mature fruits when they develop suitable colour and size."
            }
        ],

        "Banana": [
            {
                "day": "Land Preparation",
                "task": "Prepare fertile, well-drained soil with adequate organic matter."
            },
            {
                "day": "Planting",
                "task": "Plant healthy banana suckers or tissue-culture plants at suitable spacing."
            },
            {
                "day": "Establishment",
                "task": "Provide regular irrigation and remove competing weeds."
            },
            {
                "day": "Vegetative Growth",
                "task": "Apply recommended nutrients and maintain adequate soil moisture."
            },
            {
                "day": "Flowering",
                "task": "Monitor the emergence of the flower and protect the plant from pests."
            },
            {
                "day": "Fruit Development",
                "task": "Support bunch development and maintain adequate irrigation and nutrition."
            },
            {
                "day": "Harvesting",
                "task": "Harvest bunches when fruits reach appropriate maturity for the intended market."
            }
        ],

        "Mango": [
            {
                "day": "Site Preparation",
                "task": "Select a suitable site with good drainage and prepare planting pits."
            },
            {
                "day": "Planting",
                "task": "Plant healthy grafted mango saplings at recommended spacing."
            },
            {
                "day": "Establishment",
                "task": "Irrigate young plants and control weeds around the root zone."
            },
            {
                "day": "Vegetative Growth",
                "task": "Maintain balanced nutrition and prune where necessary to develop canopy structure."
            },
            {
                "day": "Flowering",
                "task": "Monitor flowering and inspect for pests and diseases."
            },
            {
                "day": "Fruit Development",
                "task": "Maintain suitable irrigation and protect developing fruits."
            },
            {
                "day": "Harvesting",
                "task": "Harvest mature fruits carefully to minimize mechanical damage."
            }
        ],

        "Grapes": [
            {
                "day": "Land Preparation",
                "task": "Prepare well-drained soil and establish suitable support structures."
            },
            {
                "day": "Planting",
                "task": "Plant healthy grape cuttings or vines at suitable spacing."
            },
            {
                "day": "Training",
                "task": "Train vines onto the support system and establish the desired canopy."
            },
            {
                "day": "Vegetative Growth",
                "task": "Manage irrigation, nutrients and pruning for balanced vine growth."
            },
            {
                "day": "Flowering",
                "task": "Monitor flowering and protect the crop from fungal diseases."
            },
            {
                "day": "Fruit Development",
                "task": "Manage irrigation and canopy conditions while monitoring fruit quality."
            },
            {
                "day": "Harvesting",
                "task": "Harvest grape bunches when they reach suitable maturity and quality."
            }
        ],

        "Watermelon": [
            {
                "day": "Land Preparation",
                "task": "Prepare loose, fertile and well-drained soil with adequate organic matter."
            },
            {
                "day": "Sowing",
                "task": "Sow healthy seeds at suitable spacing and depth."
            },
            {
                "day": "Early Growth",
                "task": "Maintain moisture and control weeds around young plants."
            },
            {
                "day": "Vine Development",
                "task": "Manage irrigation and nutrient supply as vines spread across the field."
            },
            {
                "day": "Flowering",
                "task": "Monitor flowering and support pollination through healthy field conditions."
            },
            {
                "day": "Fruit Development",
                "task": "Maintain consistent irrigation and monitor fruits for pest and disease damage."
            },
            {
                "day": "Harvesting",
                "task": "Harvest when fruits develop suitable maturity indicators and quality."
            }
        ],

        "Muskmelon": [
            {
                "day": "Land Preparation",
                "task": "Prepare fertile, loose and well-drained soil."
            },
            {
                "day": "Sowing",
                "task": "Sow healthy seeds at suitable spacing and depth."
            },
            {
                "day": "Seedling Stage",
                "task": "Maintain suitable moisture and protect young seedlings from weeds."
            },
            {
                "day": "Vine Growth",
                "task": "Provide nutrients and irrigation while managing weeds."
            },
            {
                "day": "Flowering",
                "task": "Monitor flowers and maintain healthy conditions for pollination."
            },
            {
                "day": "Fruit Development",
                "task": "Maintain consistent moisture and inspect developing fruits for pests."
            },
            {
                "day": "Harvesting",
                "task": "Harvest when fruits develop suitable aroma, colour and maturity."
            }
        ],

        "Apple": [
            {
                "day": "Site Preparation",
                "task": "Select a suitable climate and well-drained site and prepare planting pits."
            },
            {
                "day": "Planting",
                "task": "Plant healthy grafted apple saplings at recommended spacing."
            },
            {
                "day": "Establishment",
                "task": "Provide adequate irrigation and maintain a weed-free root zone."
            },
            {
                "day": "Vegetative Growth",
                "task": "Prune and train trees while maintaining balanced nutrition."
            },
            {
                "day": "Flowering",
                "task": "Monitor flowering and ensure suitable pollination conditions."
            },
            {
                "day": "Fruit Development",
                "task": "Maintain irrigation and monitor fruits for pests and diseases."
            },
            {
                "day": "Harvesting",
                "task": "Harvest fruits at appropriate maturity according to variety and market requirements."
            }
        ],

        "Orange": [
            {
                "day": "Site Preparation",
                "task": "Select a sunny, well-drained site and prepare planting pits."
            },
            {
                "day": "Planting",
                "task": "Plant healthy citrus saplings at suitable spacing."
            },
            {
                "day": "Establishment",
                "task": "Maintain regular irrigation and keep the root zone free from weeds."
            },
            {
                "day": "Vegetative Growth",
                "task": "Provide balanced nutrients and prune damaged or unwanted branches."
            },
            {
                "day": "Flowering",
                "task": "Monitor flowering and protect plants from pests and diseases."
            },
            {
                "day": "Fruit Development",
                "task": "Maintain irrigation and nutrition during fruit enlargement."
            },
            {
                "day": "Harvesting",
                "task": "Harvest mature oranges carefully to prevent fruit damage."
            }
        ],

        "Papaya": [
            {
                "day": "Land Preparation",
                "task": "Prepare fertile, well-drained soil and suitable planting pits."
            },
            {
                "day": "Planting",
                "task": "Plant healthy papaya seedlings at recommended spacing."
            },
            {
                "day": "Establishment",
                "task": "Maintain regular irrigation and remove weeds around plants."
            },
            {
                "day": "Vegetative Growth",
                "task": "Provide balanced nutrients and monitor plant health."
            },
            {
                "day": "Flowering",
                "task": "Monitor flowering plants and inspect for pest and disease symptoms."
            },
            {
                "day": "Fruit Development",
                "task": "Maintain irrigation and protect developing fruits from pests."
            },
            {
                "day": "Harvesting",
                "task": "Harvest fruits when they reach appropriate maturity and colour."
            }
        ],

        "Coconut": [
            {
                "day": "Site Preparation",
                "task": "Select a suitable site with good drainage and prepare planting pits."
            },
            {
                "day": "Planting",
                "task": "Plant healthy coconut seedlings at recommended spacing."
            },
            {
                "day": "Establishment",
                "task": "Provide irrigation during establishment and control weeds around palms."
            },
            {
                "day": "Vegetative Growth",
                "task": "Apply recommended nutrients and maintain soil moisture."
            },
            {
                "day": "Flowering",
                "task": "Monitor palms for flowering and pest damage."
            },
            {
                "day": "Nut Development",
                "task": "Maintain adequate irrigation and nutrition during nut development."
            },
            {
                "day": "Harvesting",
                "task": "Harvest mature coconuts according to the intended use and market."
            }
        ],

        "Cotton": [
            {
                "day": "Land Preparation",
                "task": "Prepare a well-drained field and ensure suitable soil fertility."
            },
            {
                "day": "Sowing",
                "task": "Sow quality cotton seed at recommended spacing."
            },
            {
                "day": "Early Growth",
                "task": "Maintain soil moisture and control weeds around young plants."
            },
            {
                "day": "Vegetative Stage",
                "task": "Apply recommended nutrients and monitor crop growth."
            },
            {
                "day": "Flowering",
                "task": "Monitor the crop closely for sucking pests and bollworm-related damage."
            },
            {
                "day": "Boll Development",
                "task": "Maintain suitable moisture and protect developing bolls from pests and diseases."
            },
            {
                "day": "Picking",
                "task": "Pick fully opened cotton bolls at suitable intervals to maintain fibre quality."
            }
        ],

        "Jute": [
            {
                "day": "Land Preparation",
                "task": "Prepare a fine seedbed with adequate moisture and remove weeds."
            },
            {
                "day": "Sowing",
                "task": "Broadcast or line-sow quality jute seeds at suitable density."
            },
            {
                "day": "Seedling Stage",
                "task": "Thin overcrowded seedlings and control weeds during early growth."
            },
            {
                "day": "Vegetative Growth",
                "task": "Maintain adequate moisture and monitor crop nutrition."
            },
            {
                "day": "Stem Development",
                "task": "Monitor plant height, stem development and pest or disease symptoms."
            },
            {
                "day": "Maturity",
                "task": "Prepare for harvesting when plants reach suitable fibre maturity."
            },
            {
                "day": "Harvesting",
                "task": "Harvest plants at the appropriate maturity and process them for fibre extraction."
            }
        ],

        "Coffee": [
            {
                "day": "Site Preparation",
                "task": "Select suitable shaded, well-drained land and prepare planting areas."
            },
            {
                "day": "Planting",
                "task": "Plant healthy coffee seedlings at recommended spacing."
            },
            {
                "day": "Establishment",
                "task": "Maintain shade, soil moisture and weed control around young plants."
            },
            {
                "day": "Vegetative Growth",
                "task": "Provide balanced nutrients, pruning and suitable shade management."
            },
            {
                "day": "Flowering",
                "task": "Monitor flowering and maintain suitable moisture conditions."
            },
            {
                "day": "Berry Development",
                "task": "Protect developing berries from pests and diseases and maintain nutrition."
            },
            {
                "day": "Harvesting",
                "task": "Harvest ripe coffee cherries selectively to maintain bean quality."
            }
        ],

        "Wheat": [
            {
                "day": "Land Preparation",
                "task": "Prepare a fine, level seedbed with suitable soil moisture."
            },
            {
                "day": "Sowing",
                "task": "Sow certified wheat seed at recommended depth and spacing."
            },
            {
                "day": "Germination",
                "task": "Monitor emergence and control early weeds."
            },
            {
                "day": "Tillering",
                "task": "Maintain appropriate irrigation and provide nutrients required for tiller development."
            },
            {
                "day": "Flowering",
                "task": "Maintain suitable moisture and monitor the crop for diseases."
            },
            {
                "day": "Grain Filling",
                "task": "Protect the crop from pests and maintain suitable field conditions."
            },
            {
                "day": "Harvesting",
                "task": "Harvest when grains are mature and the crop reaches appropriate dryness."
            }
        ],

        "Tomato": [
            {
                "day": "Nursery Preparation",
                "task": "Raise healthy tomato seedlings using quality seed and suitable nursery conditions."
            },
            {
                "day": "Transplanting",
                "task": "Transplant healthy seedlings into prepared soil at recommended spacing."
            },
            {
                "day": "Vegetative Growth",
                "task": "Maintain irrigation, control weeds and provide balanced nutrients."
            },
            {
                "day": "Flowering",
                "task": "Monitor flowering plants and inspect regularly for pests and diseases."
            },
            {
                "day": "Fruit Formation",
                "task": "Maintain consistent irrigation and support plants where required."
            },
            {
                "day": "Fruit Development",
                "task": "Monitor fruit quality and protect plants from disease and insect damage."
            },
            {
                "day": "Harvesting",
                "task": "Harvest fruits according to the required maturity stage and market destination."
            }
        ]
    }


    farming_tips = {

        "Rice":
            "Maintain proper water management and monitor the crop closely during tillering, flowering and grain filling.",

        "Maize":
            "Maize is sensitive to moisture stress around tasseling and silking, so maintain adequate irrigation during these stages.",

        "Chickpea":
            "Avoid excessive irrigation and regularly monitor the crop for pod borer and fungal diseases.",

        "Kidney Beans":
            "Maintain good drainage because prolonged waterlogging can damage bean roots.",

        "Pigeon Peas":
            "Monitor flowering and pod development carefully for insect pests.",

        "Moth Beans":
            "Avoid excessive irrigation and maintain good weed management during early crop growth.",

        "Mung Bean":
            "Timely weed and pest management is important because mung bean has a relatively short crop cycle.",

        "Black Gram":
            "Maintain balanced moisture and monitor flowering and pod formation for pest attacks.",

        "Lentil":
            "Avoid excessive moisture near maturity and monitor the crop for fungal diseases.",

        "Pomegranate":
            "Pruning, irrigation management and regular pest monitoring are important for fruit quality.",

        "Banana":
            "Banana requires regular moisture and balanced nutrition throughout active growth and fruit development.",

        "Mango":
            "Proper pruning, flowering management and pest monitoring are important for consistent fruit production.",

        "Grapes":
            "Canopy management and disease monitoring are especially important because excessive humidity can increase fungal problems.",

        "Watermelon":
            "Maintain consistent soil moisture during fruit development while avoiding waterlogging.",

        "Muskmelon":
            "Monitor fruit development closely and avoid irregular irrigation near maturity.",

        "Apple":
            "Apple cultivation depends strongly on suitable climatic conditions, variety selection and proper pruning.",

        "Orange":
            "Maintain balanced nutrition and irrigation while monitoring citrus plants for pests and diseases.",

        "Papaya":
            "Good drainage is important because prolonged waterlogging can cause root problems.",

        "Coconut":
            "Regular nutrient management, irrigation during dry periods and pest monitoring support healthy palms.",

        "Cotton":
            "Regular scouting for sucking pests and bollworms is important throughout flowering and boll development.",

        "Jute":
            "Timely thinning and weed management help maintain a healthy plant population and fibre quality.",

        "Coffee":
            "Shade management, soil moisture, pruning and selective harvesting are important for maintaining coffee quality.",

        "Wheat":
            "Irrigation at important growth stages such as tillering and grain filling can strongly influence productivity.",

        "Tomato":
            "Regular pest and disease monitoring is important because tomato is susceptible to several insect and fungal problems."
    }


    if request.method == "POST":

        crop = request.form.get(
            "crop",
            ""
        ).strip()

        if crop in farming_schedules:

            schedule = farming_schedules[crop]

            tips = farming_tips.get(
                crop,
                "Monitor soil moisture, nutrients, pests and diseases regularly."
            )

        else:

            crop = ""

            schedule = None

            tips = None


    return render_template(
        "farming_schedule.html",

        crop=crop,

        schedule=schedule,

        tips=tips,

        farmer_name=session.get("farmer_name"),

        active="farming_schedule"
    )
# ============================================================
# YIELD PREDICTION - MACHINE LEARNING
# ============================================================

@app.route(
    "/yield-prediction",
    methods=["GET", "POST"]
)
@login_required
def yield_prediction():

    prediction = None
    total_production = None

    crop = request.args.get(
        "crop",
        ""
    ).strip()

    # The crop recommended on the Crop Selection page flows into this page.
    # The two datasets name crops differently, so translate it.
    recommended = request.args.get("crop", "").strip() or \
        session.get("dashboard_crop", {}).get("recommended_crop", "")

    if recommended and request.method == "GET":

        matched_crop = _yield_crop_for(recommended, YIELD_CROPS)

        if matched_crop:

            crop = matched_crop

        elif request.args.get("crop"):

            flash(
                f"Yield data is not available for {recommended} in the "
                "dataset. Please choose a crop from the list."
            )

            crop = ""

    crop_year = ""
    season = ""
    state = ""

    # FARM AREA NOW COMES FROM CROP SELECTION
    farm_area = request.args.get(
        "farm_area",
        ""
    ).strip()

    rainfall = ""
    fertilizer = ""
    pesticide = ""

    if request.method == "POST":

        crop = request.form.get(
            "crop",
            ""
        ).strip()

        crop_year = request.form.get(
            "crop_year",
            ""
        ).strip()

        season = request.form.get(
            "season",
            ""
        ).strip()

        state = request.form.get(
            "state",
            ""
        ).strip()

        farm_area = request.form.get(
            "farm_area",
            ""
        ).strip()

        rainfall = request.form.get(
            "rainfall",
            ""
        ).strip()

        fertilizer = request.form.get(
            "fertilizer",
            ""
        ).strip()

        pesticide = request.form.get(
            "pesticide",
            ""
        ).strip()

        try:

            crop_year_value = int(
                crop_year
            )

            farm_area_value = float(
                farm_area
            )

            rainfall_value = float(
                rainfall
            )

            fertilizer_value = float(
                fertilizer
            )

            pesticide_value = float(
                pesticide
            )

            # Reject values outside the ranges the model was trained on
            check_yield_inputs(
                crop_year_value,
                farm_area_value,
                rainfall_value,
                fertilizer_value,
                pesticide_value
            )


            input_data = pd.DataFrame([
                {
                    "Crop": crop,
                    "Crop_Year": crop_year_value,
                    "Season": season,
                    "State": state,
                    "Area": farm_area_value,
                    "Annual_Rainfall": rainfall_value,
                    "Fertilizer": fertilizer_value,
                    "Pesticide": pesticide_value
                }
            ])

            predicted_yield = yield_model.predict(
                input_data
            )[0]

            prediction = round(
                float(predicted_yield),
                2
            )

            total_production = round(
                prediction * farm_area_value,
                2
            )

            # Remember this result so the dashboard can display it
            session["dashboard_yield"] = {
                "crop": crop,
                "predicted_yield": prediction,
                "total_production": total_production
            }

        except InputRangeError as range_error:

            flash(str(range_error))

        except (
            ValueError,
            TypeError,
            KeyError
        ):

            flash(
                "Please enter valid values for all fields."
            )

    return render_template(
        "yield_prediction.html",

        prediction=prediction,
        total_production=total_production,

        crop=crop,
        crop_year=crop_year,
        season=season,
        state=state,
        farm_area=farm_area,
        rainfall=rainfall,
        fertilizer=fertilizer,
        pesticide=pesticide,

        # These MUST match yield_prediction.html
        yield_crops=YIELD_CROPS,
        yield_states=YIELD_STATES,
        yield_seasons=YIELD_SEASONS,

        farmer_name=session.get("farmer_name"),

        active="yield_prediction"
    )


# ============================================================
# CHATBOT PAGE
# ============================================================

# ============================================================
# PROJECT OVERVIEW
# ============================================================

@app.context_processor
def inject_input_limits():
    return {
        "limits": INPUT_LIMITS,
        "yield_crop_for": lambda name: _yield_crop_for(name, YIELD_CROPS)
    }


@app.route("/project-overview")
@login_required
def project_overview():

    overview = build_overview(
        crop_model,
        yield_data,
        ML_CROPS,
        app.root_path,
        len([
            rule for rule in app.url_map.iter_rules()
            if rule.endpoint != "static"
        ])
    )

    return render_template(
        "project_overview.html",
        overview=overview,
        farmer_name=session.get("farmer_name"),
        active="project_overview"
    )


# ============================================================
# MODEL PERFORMANCE
# ============================================================

@app.route("/model-performance")
@login_required
def model_performance():

    return render_template(
        "model_performance.html",
        results=load_comparison(app.root_path),
        farmer_name=session.get("farmer_name"),
        active="model_performance"
    )


@app.route("/chatbot")
@login_required
def chatbot_page():

    return render_template(
        "chatbot.html",
        farmer_name=session.get("farmer_name"),
        active="chatbot"
    )


# ============================================================
# CHATBOT API
# ============================================================

# ============================================================
# ADVANCED CHATBOT API
# ============================================================
@app.route(
    "/chatbot/message",
    methods=["POST"]
)
@login_required
def chatbot_message():
    data = request.get_json(
        silent=True
    ) or {}
    original_message = data.get(
        "message",
        ""
    ).strip()
    message = original_message.lower()
    if not message:
        return jsonify({
            "reply": "Please enter a question and I’ll help you with farming, crops, yield prediction or contracts."
        })
    # ========================================================
    # CROP DETECTION
    # ========================================================
    detected_crop = None
    for crop in ML_CROPS:
        if crop.lower() in message:
            detected_crop = crop
            break
    # ========================================================
    # USE PREVIOUSLY RECOMMENDED CROP
    # ========================================================
    session_crop = session.get(
        "recommended_crop"
    )
    if not detected_crop and session_crop:
        detected_crop = session_crop
    # ========================================================
    # GREETING
    # ========================================================
    greeting_words = [
        "hello",
        "hi",
        "hey",
        "namaste",
        "good morning",
        "good afternoon",
        "good evening"
    ]
    if any(
        word in message
        for word in greeting_words
    ):
        response = (
            "Hello! 🌱 I’m your Assured Farming Assistant.\n\n"
            "I can help you with crop recommendation, "
            "yield prediction, irrigation, fertilizer, "
            "soil management, farming schedules, technical "
            "guidelines and contract farming.\n\n"
            "You can also ask me about a specific crop such as "
            "Rice, Wheat, Tomato, Maize or Cotton."
        )
    # ========================================================
    # CROP RECOMMENDATION
    # ========================================================
    elif (
        "crop recommendation" in message
        or "crop selection" in message
        or "recommend a crop" in message
        or "recommend crop" in message
        or "which crop" in message
        or "what crop" in message
        or "suitable crop" in message
    ):
        response = (
            "🌱 Crop Recommendation\n\n"
            "The Crop Selection module uses Machine Learning "
            "to recommend a suitable crop based on:\n\n"
            "• Nitrogen (N)\n"
            "• Phosphorus (P)\n"
            "• Potassium (K)\n"
            "• Temperature\n"
            "• Humidity\n"
            "• Soil pH\n"
            "• Rainfall\n\n"
            "Enter these values in Crop Selection to obtain "
            "a data-driven crop recommendation."
        )
    # ========================================================
    # YIELD PREDICTION
    # ========================================================
    elif (
        "yield" in message
        or "production" in message
        or "predict yield" in message
        or "yield prediction" in message
        or "how much will i produce" in message
    ):
        response = (
            "📈 Yield Prediction\n\n"
            "Your Yield Prediction module uses a trained "
            "Machine Learning model with:\n\n"
            "• Crop\n"
            "• Crop year\n"
            "• Season\n"
            "• State\n"
            "• Farm area\n"
            "• Annual rainfall\n"
            "• Fertilizer usage\n"
            "• Pesticide usage\n\n"
            "The model estimates crop yield, and the platform "
            "can use the predicted yield together with farm area "
            "to estimate total production."
        )
    # ========================================================
    # ML EXPLANATION
    # ========================================================
    elif (
        "machine learning" in message
        or "ml model" in message
        or "how does the model work" in message
        or "how does ml work" in message
        or "how is prediction done" in message
    ):
        response = (
            "🤖 Machine Learning in this platform\n\n"
            "The system contains two main ML functions.\n\n"
            "1. Crop Recommendation\n"
            "Uses soil and environmental parameters to "
            "recommend a suitable crop.\n\n"
            "2. Yield Prediction\n"
            "Uses crop, location, season, farm and agricultural "
            "inputs to estimate expected crop yield.\n\n"
            "This allows the farmer to make decisions using "
            "data instead of relying only on guesswork."
        )
    # ========================================================
    # CROP-SPECIFIC GUIDANCE
    # ========================================================
    elif detected_crop and (
        "about" in message
        or "information" in message
        or "guide" in message
        or "guidance" in message
        or "grow" in message
        or "requirement" in message
        or "requirements" in message
    ):
        response = (
            f"🌱 {detected_crop} Guidance\n\n"
            f"{detected_crop} can be managed through the "
            "following major stages:\n\n"
            "• Land and soil preparation\n"
            "• Suitable sowing or planting\n"
            "• Irrigation management\n"
            "• Nutrient and fertilizer management\n"
            "• Pest and disease monitoring\n"
            "• Crop growth monitoring\n"
            "• Harvesting at the appropriate stage\n\n"
            f"For detailed {detected_crop}-specific information, "
            "open the Technical Guidelines module."
        )
    # ========================================================
    # IRRIGATION
    # ========================================================
    elif (
        "irrigation" in message
        or "water" in message
        or "watering" in message
        or "how often should i water" in message
    ):
        if detected_crop:
            response = (
                f"💧 Irrigation Guidance for {detected_crop}\n\n"
                f"{detected_crop} requires appropriate water "
                "management throughout its growth cycle. "
                "Irrigation should consider soil moisture, "
                "rainfall, crop growth stage and local weather "
                "conditions.\n\n"
                "Avoid both prolonged water stress and "
                "unnecessary over-irrigation."
            )
        else:
            response = (
                "💧 Irrigation Guidance\n\n"
                "Irrigation requirements depend on the crop, "
                "soil type, rainfall, weather and crop growth "
                "stage.\n\n"
                "Use the Farming Schedule and Technical Guidelines "
                "modules for crop-specific water management."
            )
    # ========================================================
    # FERTILIZER / NUTRIENTS
    # ========================================================
    elif (
        "fertilizer" in message
        or "fertiliser" in message
        or "nutrient" in message
        or "nitrogen" in message
        or "phosphorus" in message
        or "potassium" in message
        or "npk" in message
    ):
        response = (
            "🌾 Fertilizer & Nutrient Guidance\n\n"
            "The platform considers Nitrogen (N), Phosphorus (P) "
            "and Potassium (K) as important crop-selection "
            "parameters.\n\n"
            "Fertilizer decisions should be based on crop "
            "requirements, soil condition and recommended "
            "agricultural practice rather than applying the same "
            "quantity to every crop.\n\n"
            "Check Technical Guidelines for crop-specific advice."
        )
    # ========================================================
    # SOIL
    # ========================================================
    elif (
        "soil" in message
        or "ph" in message
        or "soil type" in message
    ):
        response = (
            "🌱 Soil Guidance\n\n"
            "Soil characteristics influence crop suitability, "
            "nutrient availability and water management.\n\n"
            "Your Crop Selection model uses soil pH together "
            "with N, P, K, temperature, humidity and rainfall "
            "to recommend a suitable crop."
        )
    # ========================================================
    # PEST / DISEASE
    # ========================================================
    elif (
        "pest" in message
        or "pests" in message
        or "disease" in message
        or "insect" in message
        or "insects" in message
    ):
        response = (
            "🐛 Pest & Disease Management\n\n"
            "Regular crop monitoring is important for detecting "
            "pest or disease problems early.\n\n"
            "Monitor leaves, stems, fruits and overall crop "
            "growth, and follow crop-specific integrated pest "
            "management practices.\n\n"
            "Use Technical Guidelines for the crop-specific "
            "management information available in the platform."
        )
    # ========================================================
    # FARMING SCHEDULE
    # ========================================================
    elif (
        "schedule" in message
        or "farming schedule" in message
        or "farm schedule" in message
        or "stages" in message
        or "growth stages" in message
    ):
        response = (
            "📅 Farming Schedule\n\n"
            "The Farming Schedule module organizes crop "
            "management into major stages such as:\n\n"
            "1. Land preparation\n"
            "2. Sowing or planting\n"
            "3. Vegetative growth\n"
            "4. Flowering or reproductive stage\n"
            "5. Crop development\n"
            "6. Harvesting\n\n"
            "Select a crop in the Farming Schedule module "
            "to view its stage-wise activities."
        )
    # ========================================================
    # CONTRACT FARMING
    # ========================================================
    elif (
        "contract farming" in message
        or "what is contract farming" in message
        or "contract" in message
        or "buyer" in message
        or "buyers" in message
    ):
        response = (
            "🤝 Contract Farming\n\n"
            "Contract farming connects farmers with buyers "
            "through predefined crop, location and pricing "
            "conditions.\n\n"
            "In this platform, you can use Search & Apply "
            "to find available contracts and submit an "
            "application."
        )
    # ========================================================
    # SEARCH CONTRACTS
    # ========================================================
    elif (
        "find contract" in message
        or "search contract" in message
        or "available contract" in message
        or "available contracts" in message
        or "where can i apply" in message
    ):
        contracts = Contract.query.all()
        if contracts:
            crop_names = sorted(
                set(
                    contract.crop
                    for contract in contracts
                )
            )
            response = (
                "🤝 Available Contract Opportunities\n\n"
                f"The system currently contains {len(contracts)} "
                "contract opportunities covering "
                f"{', '.join(crop_names)}.\n\n"
                "Open Search & Apply to filter contracts by "
                "crop and location and submit an application."
            )
        else:
            response = (
                "There are currently no contracts available "
                "in the database. Please check Search & Apply "
                "again later."
            )
    # ========================================================
    # APPLICATION STATUS
    # ========================================================
    elif (
        "application status" in message
        or "my application" in message
        or "applied contract" in message
        or "application" in message
    ):
        farmer_id = session.get(
            "farmer_id"
        )
        applications = []
        if farmer_id:
            applications = ContractApplication.query.filter_by(
                farmer_id=farmer_id
            ).all()
        if applications:
            latest = applications[-1]
            response = (
                "📋 Application Status\n\n"
                f"You have submitted {len(applications)} "
                "contract application(s).\n\n"
                f"Latest application status: "
                f"{latest.status}\n\n"
                "You can view your complete application "
                "information from the Dashboard."
            )
        else:
            response = (
                "You have not submitted a contract application "
                "yet.\n\n"
                "Open Search & Apply to find a suitable contract "
                "and submit your application."
            )
    # ========================================================
    # DASHBOARD
    # ========================================================
    elif (
        "dashboard" in message
        or "my profile" in message
        or "my account" in message
    ):
        response = (
            "📊 Dashboard\n\n"
            "Your Dashboard provides a central view of your "
            "farming information and contract applications.\n\n"
            "You can use it to review your saved information "
            "and track submitted contract applications."
        )
    # ========================================================
    # HELP
    # ========================================================
    elif (
        "help" in message
        or "what can you do" in message
        or "what do you know" in message
    ):
        response = (
            "🌱 I can help you with:\n\n"
            "• Crop recommendation\n"
            "• Yield prediction\n"
            "• ML model explanation\n"
            "• Irrigation\n"
            "• Fertilizer and nutrients\n"
            "• Soil management\n"
            "• Pest management\n"
            "• Farming schedules\n"
            "• Technical guidelines\n"
            "• Contract farming\n"
            "• Contract search\n"
            "• Application status\n\n"
            "You can also mention a specific crop, such as "
            "Rice, Wheat, Maize, Tomato or Cotton."
        )
    # ========================================================
    # FALLBACK
    # ========================================================
    else:
        if detected_crop:
            response = (
                f"I recognized {detected_crop} in your question. 🌱\n\n"
                "I can provide guidance related to its "
                "irrigation, fertilizer, soil, pests, farming "
                "schedule, harvesting or technical guidelines.\n\n"
                "Try asking something more specific, for example:\n"
                f"• How should I manage {detected_crop} irrigation?\n"
                f"• What fertilizer information is available for {detected_crop}?\n"
                f"• Give me the {detected_crop} farming schedule."
            )
        else:
            response = (
                "I’m designed to assist with your farming "
                "decision platform. 🌱\n\n"
                "Try asking about:\n"
                "• Crop recommendation\n"
                "• Yield prediction\n"
                "• Irrigation\n"
                "• Fertilizer\n"
                "• Soil\n"
                "• Pest management\n"
                "• Farming schedules\n"
                "• Technical guidelines\n"
                "• Contract farming\n"
                "• Application status"
            )
    # ========================================================
    # RETURN RESPONSE
    # ========================================================
    return jsonify({
        "reply": response
    })

# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )