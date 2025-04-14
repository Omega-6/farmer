import os
import uuid
import random
import pandas as pd
import requests
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
# Set your secret key (ideally via an environment variable)
app.secret_key = os.environ.get('SECRET_KEY', 'a_default_secret_key')

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///farmdata.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model to store farmer data, including personalized suggestions
class FarmData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36))
    soil_type = db.Column(db.String(50))
    soil_ph = db.Column(db.Float)
    soil_moisture = db.Column(db.Float)
    temperature = db.Column(db.Float)  # Stored in Fahrenheit
    rainfall = db.Column(db.Float)
    crop_history = db.Column(db.Text)
    fertilizer_usage = db.Column(db.Text)
    pest_issues = db.Column(db.Text)
    city = db.Column(db.String(100))
    suggestions = db.Column(db.Text)  # Personalized crop suggestions (comma-separated)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<FarmData {self.id} for user {self.user_id}>'

# Before each request, ensure tables exist and track user via session
@app.before_request
def before_request():
    db.create_all()
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())

# --------------------------
# Helper Function: Personalize Government Aid Info
# --------------------------
def personalize_subsidy_info(data):
    messages = []
    if data.city:
        messages.append(f"Explore loan programs available in {data.city}.")
    if data.soil_type:
        messages.append(f"Your {data.soil_type} soil may qualify for cover crop grants to boost sustainability.")
    if data.crop_history:
        crop = data.crop_history.split(',')[0].strip()
        messages.append(f"Since you grow {crop}, you might be eligible for specialty crop aid programs.")
    if data.fertilizer_usage:
        messages.append("Fertilizer usage noted—check out EQIP for funding to reduce runoff.")
    if data.pest_issues:
        messages.append("Pest issues reported—explore pest control subsidies and training in your area.")
    if data.rainfall is None or data.rainfall == 0:
        messages.append("If your farm is mainly rain-fed, consider drought assistance programs.")
    return "<ul>" + "".join(f"<li>{msg}</li>" for msg in messages) + "</ul>"

# --------------------------
# Static Extra Info and Data
# --------------------------
basic_crop_recommendation_info = {
    "soil_types": {
        "Sandy": "Recommended Crop: Carrot, due to good drainage and nutrient requirements.",
        "Loamy": "Recommended Crop: Wheat, as loamy soil is ideal for balanced moisture.",
        "Clay": "Recommended Crop: Rice, because clay holds water well for paddy fields."
    },
    "weather_conditions": {
        "Sunny": "Recommended Crop: Corn, which thrives in full sun.",
        "Rainy": "Recommended Crop: Rice, which benefits from abundant water.",
        "Humid": "Recommended Crop: Soybean, suited for humid climates."
    },
    "monthly_suggestions": {
        "January": "Plant winter-hardy crops like Kale or Cabbage.",
        "February": "Begin early sowing of Spinach and other leafy greens.",
        "March": "Start planting spring vegetables such as Lettuce.",
        "April": "Ideal time for warm-season crops like Tomatoes and Peppers.",
        "May": "Plant summer crops such as Corn or Beans.",
        "June": "Ensure proper irrigation for high-demand crops like Cucumbers.",
        "July": "Monitor for pests and rotate crops if needed.",
        "August": "Prepare for harvest; consider quick-growing vegetables.",
        "September": "Start planting fall crops like Broccoli and Cauliflower.",
        "October": "Adjust for cooler temperatures; plant root vegetables.",
        "November": "Sow cover crops to improve soil fertility during winter.",
        "December": "Rest the soil and plan for the next season."
    },
    "crop_schedule": [
        {
            "Temperature": "Cool",
            "First Date": "Mid March",
            "Last Date": "Mid April",
            "Plants": "Peas, Fava Beans, Onions, Leeks, Garlic, Greens, Turnips, White Potatoes, Cabbage"
        },
        {
            "Temperature": "Cool",
            "First Date": "Late March",
            "Last Date": "Mid May",
            "Plants": "Lettuce*, Radishes*, Beets*, Carrots*"
        },
        {
            "Temperature": "Cool",
            "First Date": "Late March",
            "Last Date": "Late April",
            "Plants": "Shallots, Spinach*, Bok Choy, Parsley; Cabbage Family, Leeks, Onions"
        }
    ],
    "nutrient_recommendations": [
        {
            "Crop": "Peas",
            "N Low": 30,
            "N High": 50,
            "P Low": 20,
            "P High": 40,
            "K Low": 40,
            "K High": 60,
            "Other": "Prefers slightly acidic to neutral soil (pH 6.0-7.0)."
        },
        {
            "Crop": "Fava Beans",
            "N Low": 30,
            "N High": 50,
            "P Low": 20,
            "P High": 40,
            "K Low": 40,
            "K High": 60,
            "Other": "Well-drained soil, neutral to slightly alkaline pH."
        }
    ]
}

# Define a default dictionary for fertilizer & water usage recommendations
fertilizer_water_data = {
    "Peas": {"NPK": "10-20-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Water regularly during flowering."},
    "Fava Beans": {"NPK": "10-20-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Keep soil moist but not waterlogged."},
    # Add additional crop data here as needed...
}

# Default market prices for "Market Price Alerts (Static Data)"
default_market_prices = {
    "Peas": 2.50,
    "Fava Beans": 2.80,
    "Onions": 1.20,
    "Leeks": 1.50,
    "Garlic": 4.00,
    "Greens (Collards, Kale, Mustard, Turnip, Etc.)": 1.10,
    "Turnips": 0.90,
    "White Potatoes": 0.75,
    "Cabbage": 1.00,
    "Lettuce": 1.20,
    "Radishes": 1.10,
    "Beets": 1.50,
    "Carrots": 1.30,
    "Shallots": 3.00,
    "Spinach": 1.40,
    "Bok Choy": 1.60,
    "Parsley": 2.00,
    "Swiss Chard": 1.50,
    "Celery": 1.30,
    "Watermelons": 0.50,
    "Winter Squash": 0.80,
    "Melons": 0.70,
    "Summer Squash": 0.60,
    "Cucumbers": 0.90,
    "Pumpkins": 0.80,
    "Sweet Potato": 1.00,
    "Okra": 2.50,
    "Chinese Cabbage": 1.10,
    "Sweet Corn": 3.25,
    "Peanuts": 2.20,
    "Lima Beans": 2.80,
    "Beans (Bush, Pole, Shell, Dried)": 2.50,
    "Black-Eyed Peas": 2.30,
    "Eggplant": 1.50,
    "Peppers": 2.00,
    "Tomato": 1.80,
    "Basil": 3.00,
    "Gandules (Pigeon Peas)": 2.50,
    "Collards (Cabbage Family)": 1.20
}

# Features that remain after removing unwanted capabilities
features = [
    {"name": "Basic Crop Recommendation", 
     "description": "Suggests the best crop based on soil type, weather, and month.",
     "benefit": "Helps farmers choose the right crop for higher yield & profit.", 
     "image": "basic_crop.png"},
    {"name": "Government Aid & Subsidy Info", 
     "description": "Provides a list of available farming subsidies based on region.",
     "benefit": "Helps farmers access financial support for seeds, fertilizers, or technology.", 
     "image": "gov_aid.png"},
    {"name": "Soil Health Monitoring", 
     "description": "Allows farmers to input soil fertility levels and suggests ways to improve soil.",
     "benefit": "Prevents soil degradation and boosts long-term productivity.", 
     "image": "soil_health.png"},
    {"name": "Market Price Alerts (Static Data)", 
     "description": "Displays current crop prices from a stored dataset.",
     "benefit": "Helps farmers decide when to sell crops for maximum profit.", 
     "image": "market_price_static.png"},
    {"name": "Crop Rotation Planning", 
     "description": "Suggests a rotation schedule to improve soil fertility & reduce pests.",
     "benefit": "Prevents soil depletion and increases productivity.", 
     "image": "crop_rotation.png"},
    {"name": "Real-Time Weather API Integration", 
     "description": "Fetch live weather data from OpenWeatherMap API.",
     "benefit": "Provides accurate climate data for better crop selection.", 
     "image": "weather_api.png"},
    {"name": "Fertilizer & Water Usage Recommendations", 
     "description": "Suggests the best fertilizer & irrigation methods for each crop.",
     "benefit": "Saves money & resources while ensuring healthy crops.", 
     "image": "fertilizer_water.png"},
    {"name": "Harvest Time Optimization", 
     "description": "Recommends best harvesting time based on weather & market trends.",
     "benefit": "Maximizes profit & crop quality.", 
     "image": "harvest_optimization.png"},
    {"name": "Supply & Demand Analysis", 
     "description": "Shows which crops are in high demand in different regions.",
     "benefit": "Prevents overproduction of low-demand crops & reduces waste.", 
     "image": "supply_demand.png"},
    {"name": "AI-Based Yield Prediction", 
     "description": "Uses machine learning to predict crop yield based on weather, soil, and planting time.",
     "benefit": "Helps farmers make data-driven decisions to improve productivity.", 
     "image": "ai_yield.png"}
]

# --------------------------
# Routes
# --------------------------
@app.route("/")
def home():
    latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
    if latest_data:
        personalized_info = {
            "greeting": f"Hello farmer from {latest_data.city}!",
            "soil": latest_data.soil_type,
            "soil_ph": latest_data.soil_ph,
            "temperature": latest_data.temperature,
            "rainfall": latest_data.rainfall,
            "suggestions": latest_data.suggestions.split(",") if latest_data.suggestions else []
        }
    else:
        personalized_info = {
            "greeting": "Hello Farmer!",
            "soil": "Loamy",
            "soil_ph": 6.5,
            "temperature": 68,
            "rainfall": 100,
            "suggestions": []
        }
    return render_template("index.html", features=features, personalized_info=personalized_info)

@app.route("/feature/<name>", methods=["GET", "POST"])
def feature_details(name):
    feature = next((f for f in features if f['name'] == name), None)
    if not feature:
        return "Feature not found", 404

    extra_info = {}

    if feature['name'] == "Basic Crop Recommendation":
        extra_info = basic_crop_recommendation_info.copy()
        latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        if latest_data and latest_data.suggestions:
            extra_info["finalSuggestions"] = latest_data.suggestions.split(",")
    elif feature['name'] == "Government Aid & Subsidy Info":
        latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        static_info = """
            <h4>Government Aid & Subsidy Info in Pennsylvania</h4>
            <p>Pennsylvania offers a range of financial assistance programs aimed at strengthening agribusiness,
            supporting rural development, and modernizing farming operations. Through the PA Department of Agriculture’s
            Agricultural Business Development Center, farmers can access:</p>
            <ul>
                <li><strong>Direct Loan & Loan Guarantee Programs:</strong> Low‑interest loans for equipment upgrades and expansion.</li>
                <li><strong>Grant Programs & Financial Assistance:</strong> Competitive grants for business planning and infrastructure improvements.</li>
                <li><strong>Technical Assistance & Training:</strong> Expert guidance on financial management and best practices.</li>
                <li><strong>Disaster Assistance:</strong> Emergency support for severe weather or natural disasters.</li>
            </ul>
            <p>Additional resources:</p>
            <ul>
                <li><a href="https://www.pa.gov/agencies/pda/business-and-industry/agricultural-business-development-center/financial-assistance.html" target="_blank">PA Agricultural Business Development Center</a></li>
                <li><a href="https://www.fsa.usda.gov/" target="_blank">USDA Farm Service Agency</a></li>
                <li><a href="https://www.agriculture.pa.gov/" target="_blank">Pennsylvania Department of Agriculture</a></li>
            </ul>
        """
        if latest_data:
            personalized_messages = personalize_subsidy_info(latest_data)
            gov_info = static_info + "<hr><h5>Personalized Recommendations:</h5>" + personalized_messages
        else:
            gov_info = static_info
        extra_info = {"gov_info": gov_info}
    elif feature['name'] == "Soil Health Monitoring":
        latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        recommendations = []
        if latest_data:
            optimal_ph_range = (6.0, 7.0)
            optimal_moisture = 30
            if latest_data.soil_ph < optimal_ph_range[0]:
                recommendations.append("Soil pH is low (acidic). Consider applying lime. See <a href='https://www.nrcs.usda.gov/wps/portal/nrcs/main/soils/health/' target='_blank'>NRCS Soil Health Guidelines</a>.")
            elif latest_data.soil_ph > optimal_ph_range[1]:
                recommendations.append("Soil pH is high (alkaline). Add elemental sulfur or organic matter. Consult your local extension.")
            else:
                recommendations.append("Soil pH is within the optimal range.")
            if latest_data.soil_moisture < optimal_moisture:
                recommendations.append("Soil moisture is low. Increase irrigation or use cover crops.")
            elif latest_data.soil_moisture > optimal_moisture:
                recommendations.append("Soil moisture is high. Consider improved drainage options.")
            else:
                recommendations.append("Soil moisture is optimal.")
            recommendations.append("Regularly add compost to improve soil structure. See <a href='https://soilhealth.acs.edu/' target='_blank'>Soil Health Academy</a>.")
            recommendations.append("Use crop rotation to enhance soil fertility. Check out <a href='https://www.sare.org/' target='_blank'>SARE</a>.")
        else:
            recommendations.append("No soil data available. Please submit your farm data.")
        extra_info = {"recommendations": recommendations}
    elif feature['name'] == "Market Price Alerts (Static Data)":
        extra_info = {"market_prices": default_market_prices}
        personalized_suggestions = []
        latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        if latest_data and latest_data.crop_history:
            crops = [crop.strip().lower() for crop in latest_data.crop_history.split(",")]
            market_prices_lower = {key.lower(): value for key, value in default_market_prices.items()}
            for crop in crops:
                if crop in market_prices_lower:
                    price = market_prices_lower[crop]
                    suggestion = f"{crop.title()}: Current price ${price} per unit; keep monitoring."
                    personalized_suggestions.append(suggestion)
        extra_info["personalized_suggestions"] = personalized_suggestions
    elif feature['name'] == "Crop Rotation Planning":
        latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        if latest_data and latest_data.crop_history:
            rotation_schedule = (
                "Based on your crop history, we recommend planting <strong>Legumes (Nitrogen Fixers)</strong> next. "
                "Additionally, consider intercropping complementary crops to enhance pest control and nutrient utilization. "
                "Adjust your crop schedules based on local weather data and soil test results for optimal performance. "
                "For more detailed guidance, refer to <a href='https://www.nrcs.usda.gov/wps/portal/nrcs/main/national/' target='_blank'>USDA NRCS</a> "
                "or <a href='https://www.sare.org/' target='_blank'>SARE</a>."
            )
        else:
            rotation_schedule = "No crop history available. Please submit your farm data for personalized crop rotation recommendations."
        extra_info = {"rotation_schedule": rotation_schedule}
    elif feature['name'] == "Real-Time Weather API Integration":
        city = request.args.get("city")
        if not city:
            latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
            city = latest_data.city if (latest_data and latest_data.city) else "Chester Springs"
        api_key = "41634f4abed439fd5c63967222a91b8b"  # Replace with your API key
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"
        response = requests.get(weather_url)
        if response.status_code == 200:
            data = response.json()
            extra_info = {
                "city": city,
                "description": data["weather"][0]["description"].capitalize(),
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"]
            }
        else:
            extra_info = {"error": "Could not retrieve weather data"}
    elif feature['name'] == "Fertilizer & Water Usage Recommendations":
        latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        suggestions = []
        if latest_data and latest_data.suggestions:
            for crop in latest_data.suggestions.split(","):
                crop = crop.strip()
                if crop in fertilizer_water_data:
                    suggestions.append({ "crop": crop, **fertilizer_water_data[crop] })
        extra_info = {"recommendations": suggestions}
    elif feature['name'] == "Harvest Time Optimization":
        latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        if latest_data and latest_data.suggestions:
            suggested_crops = [crop.strip() for crop in latest_data.suggestions.split(",")]
            city = latest_data.city if latest_data.city else "Chester Springs"
            api_key = "41634f4abed439fd5c63967222a91b8b"  # Replace with your API key
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"
            response = requests.get(weather_url)
            if response.status_code == 200:
                weather_data = response.json()
                temperature = weather_data["main"]["temp"]
                weather_desc = weather_data["weather"][0]["description"].capitalize()
            else:
                temperature = None
                weather_desc = "Unavailable"
            market_prices = {
                "Peas": 2.50,
                "Fava Beans": 2.80,
                "Onions": 1.20,
                "Leeks": 1.50,
                "Garlic": 4.00,
                "Greens (Collards, Kale, Mustard, Turnip, Etc.)": 1.10,
                "Turnips": 0.90,
                "White Potatoes": 0.75,
                "Cabbage": 1.00,
                "Lettuce": 1.20,
                "Radishes": 1.10,
                "Beets": 1.50,
                "Carrots": 1.30,
                "Shallots": 3.00,
                "Spinach": 1.40,
                "Bok Choy": 1.60,
                "Parsley": 2.00,
                "Swiss Chard": 1.50,
                "Celery": 1.30,
                "Watermelons": 0.50,
                "Winter Squash": 0.80,
                "Melons": 0.70,
                "Summer Squash": 0.60,
                "Cucumbers": 0.90,
                "Pumpkins": 0.80,
                "Sweet Potato": 1.00,
                "Okra": 2.50,
                "Chinese Cabbage": 1.10,
                "Sweet Corn": 3.25,
                "Peanuts": 2.20,
                "Lima Beans": 2.80,
                "Beans (Bush, Pole, Shell, Dried)": 2.50,
                "Black-Eyed Peas": 2.30,
                "Eggplant": 1.50,
                "Peppers": 2.00,
                "Tomato": 1.80,
                "Basil": 3.00,
                "Gandules (Pigeon Peas)": 2.50,
                "Collards (Cabbage Family)": 1.20
            }
            recommended_crops = []
            if temperature is not None:
                for crop in suggested_crops:
                    if crop in market_prices:
                        price = market_prices[crop]
                        if temperature > 68 and price > 0.5:
                            recommended_crops.append(crop)
            if recommended_crops:
                recommendation = "Optimal harvest time for: " + ", ".join(recommended_crops)
            else:
                recommendation = "Conditions are not optimal for harvest of your suggested crops."
            extra_info = {
                "harvest_recommendation": recommendation,
                "city": city,
                "temperature": temperature,
                "weather_description": weather_desc,
                "recommended_crops": recommended_crops
            }
        else:
            extra_info = {"harvest_recommendation": "No personalized crop suggestions available. Please submit your farm data."}
    elif feature['name'] == "Supply & Demand Analysis":
        extra_info = {
            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            "supply": [100, 120, 130, 110, 150, 140, 160, 170, 180, 150, 140, 130],
            "demand": [90, 110, 120, 100, 140, 130, 150, 160, 170, 140, 130, 120]
        }
    elif feature['name'] == "AI-Based Yield Prediction":
        prediction = None
        prefill = {}
        latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        if latest_data:
            prefill = {
                "temperature": latest_data.temperature,
                "rainfall": latest_data.rainfall,
                "soil_ph": latest_data.soil_ph
            }
        if request.method == "POST":
            try:
                temperature = float(request.form.get("temperature"))
                rainfall = float(request.form.get("rainfall"))
                soil_ph = float(request.form.get("soil_ph"))
            except (ValueError, TypeError):
                prediction = "Invalid input. Please enter numeric values."
            else:
                pred_value = random.uniform(50, 150)  # Simulated yield prediction
                prediction = f"Predicted crop yield: {pred_value:.2f} units"
        extra_info = {"prefill": prefill, "prediction": prediction}

    # Patch: Ensure extra_info is a dictionary and that market_prices is defined
    if extra_info is None:
        extra_info = {}
    if "market_prices" not in extra_info:
        extra_info["market_prices"] = default_market_prices

    return render_template("feature.html", feature=feature, extra_info=extra_info)

@app.route("/input", methods=["GET"])
def input_form():
    data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
    return render_template("input_form.html", data=data)

@app.route("/submit", methods=["POST"])
def submit():
    user_id = session.get('user_id')
    data = FarmData(
        user_id=user_id,
        soil_type=request.form.get("soil_type"),
        soil_ph=float(request.form.get("soil_ph") or 0),
        soil_moisture=float(request.form.get("soil_moisture") or 0),
        temperature=float(request.form.get("temperature") or 0),
        rainfall=float(request.form.get("rainfallAmount") or 0),
        crop_history=request.form.get("crop_history"),
        fertilizer_usage=request.form.get("fertilizer_usage"),
        pest_issues=request.form.get("pest_issues"),
        city=request.form.get("location")
    )
    db.session.add(data)
    db.session.commit()

    # Read Excel files from the 'data' folder
    timeToSowAndHarvest = pd.read_excel('data/timeToSowAndHarvest.xlsx', engine='openpyxl')
    waterToCrops = pd.read_excel('data/waterToCrops.xlsx', engine='openpyxl')
    phToCrops = pd.read_excel('data/phToCrops.xlsx', engine='openpyxl')
    nutrientsToCrops = pd.read_excel('data/nutrientsToCrops.xlsx', engine='openpyxl')
    cropRotationCycle = pd.read_excel('data/cropRotationCycle.xlsx', engine='openpyxl')
    
    wantedSow = request.form.get("wantedSow")
    wantedHarvest = request.form.get("wantedHarvest")
    soilPh = float(request.form.get("soilPh"))
    weather_input = float(request.form.get("weather"))
    previousPlantsInput = request.form.get("previousPlants")
    previousPlants = previousPlantsInput.split(", ")
    soilNit = int(request.form.get("soilNit"))
    soilPho = int(request.form.get("soilPho"))
    soilPot = int(request.form.get("soilPot"))
    waterLevel = int(request.form.get("waterLevel"))
    rainfall_input = request.form.get("rainfall")
    irrigated_input = request.form.get("irrigated")
    groundwater_input = request.form.get("groundwater")
    surfacewater_input = request.form.get("surfacewater")

    rainfall_bool = True if rainfall_input.lower() == "yes" else False
    irrigated = True if irrigated_input.lower() == "yes" else False
    groundwater = True if groundwater_input.lower() == "yes" else False
    surfacewater = True if surfacewater_input.lower() == "yes" else False

    plantPoints = {
        "Peas": 0, "Fava Beans": 0, "Onions": 0, "Leeks": 0, "Garlic": 0,
        "Greens (Collards, Kale, Mustard)": 0, "Turnips": 0, "White Potatoes": 0,
        "Cabbage": 0, "Lettuce": 0, "Radishes": 0, "Beets": 0, "Carrots": 0,
        "Shallots": 0, "Spinach": 0, "Bok Choy": 0, "Parsley": 0, "Swiss Chard": 0,
        "Celery": 0, "Watermelons": 0, "Winter Squash": 0, "Melons": 0,
        "Summer Squash": 0, "Cucumbers": 0, "Pumpkins": 0, "Sweet Potatoes": 0,
        "Okra": 0, "Chinese Cabbage": 0, "Sweet Corn": 0, "Peanuts": 0,
        "Lima Beans": 0, "Beans (Bush, Pole, Shell, Dried)": 0, "Black-Eyed Peas": 0,
        "Eggplant": 0, "Peppers": 0, "Tomato": 0, "Basil": 0, "Gandules (Pigeon Peas)": 0
    }

    phCrops = phToCrops[(phToCrops["Low pH Acceptable"] <= soilPh) & (phToCrops["High pH Acceptable"] >= soilPh)]
    for crop in phCrops['Crop'].tolist():
        if crop in plantPoints:
            plantPoints[crop] += 8

    nitCrops = nutrientsToCrops[(nutrientsToCrops["Nitrogen (N) Low"] <= soilNit) & (nutrientsToCrops["Nitrogen (N) High"] >= soilNit)]
    phoCrops = nutrientsToCrops[(nutrientsToCrops["Phosphorus (P) Low"] <= soilPho) & (nutrientsToCrops["Phosphorus (P) High"] >= soilPho)]
    potCrops = nutrientsToCrops[(nutrientsToCrops["Potassium (K) Low"] <= soilPot) & (nutrientsToCrops["Potassium (K) High"] >= soilPot)]
    for crop in nitCrops['Crop'].tolist():
        if crop in plantPoints:
            plantPoints[crop] += 10
    for crop in phoCrops['Crop'].tolist():
        if crop in plantPoints:
            plantPoints[crop] += 9
    for crop in potCrops['Crop'].tolist():
        if crop in plantPoints:
            plantPoints[crop] += 9

    waterAmountCrops = waterToCrops[(waterToCrops["Min Water (mm)"] <= waterLevel) & (waterToCrops["Max Water (mm)"] >= waterLevel)]
    for crop in waterAmountCrops['Crop'].tolist():
        if crop in plantPoints:
            plantPoints[crop] += 10

    rainTypeCrops = pd.concat([
        waterToCrops[waterToCrops["Rainfall"] == True] if rainfall_bool else pd.DataFrame(),
        waterToCrops[waterToCrops["Irrigated"] == True] if irrigated else pd.DataFrame(),
        waterToCrops[waterToCrops["Groundwater"] == True] if groundwater else pd.DataFrame(),
        waterToCrops[waterToCrops["Surface Water"] == True] if surfacewater else pd.DataFrame()
    ])
    rainTypeCrops = rainTypeCrops.drop_duplicates()
    for crop in rainTypeCrops['Crop'].tolist():
        if crop in plantPoints:
            plantPoints[crop] += 7

    listOfSow = wantedSow.split(", ")
    sowTimeCrops = pd.DataFrame()
    for sow in listOfSow:
        tempDF = timeToSowAndHarvest[timeToSowAndHarvest["Sowing Time"].str.contains(sow, case=False)]
        sowTimeCrops = pd.concat([sowTimeCrops, tempDF])
    sowTimeCrops = sowTimeCrops.drop_duplicates()
    for crop in sowTimeCrops['Crop Name'].tolist():
        if crop in plantPoints:
            plantPoints[crop] += 8

    listOfHarvest = wantedHarvest.split(", ")
    harvestTimeCrops = pd.DataFrame()
    for harv in listOfHarvest:
        tempDF = timeToSowAndHarvest[timeToSowAndHarvest["Harvest Time"].str.contains(harv, case=False)]
        harvestTimeCrops = pd.concat([harvestTimeCrops, tempDF])
    harvestTimeCrops = harvestTimeCrops.drop_duplicates()
    for crop in harvestTimeCrops['Crop Name'].tolist():
        if crop in plantPoints:
            plantPoints[crop] += 7

    cropRotationCycleCropsTemp = []
    for plant in previousPlants:
        df_temp = cropRotationCycle[cropRotationCycle["Crops to Plant"].str.contains(plant, case=False)]
        if not df_temp.empty:
            cropRotationCycleCropsTemp.append(df_temp.iloc[0, 0])
    counts = {"Year 1": 0, "Year 2": 0, "Year 3": 0, "Year 4": 0}
    for year in cropRotationCycleCropsTemp:
        if year in counts:
            counts[year] += 1
    if counts:
        max_year = max(counts, key=counts.get)
        selected_row = cropRotationCycle[cropRotationCycle["Year"] == max_year]
        if not selected_row.empty:
            crops_list = selected_row.iloc[0]["Crops to Plant"].split(", ")
            for crop in crops_list:
                if crop in plantPoints:
                    plantPoints[crop] += 10

    sortedCrops = sorted(plantPoints.items(), key=lambda item: item[1], reverse=True)
    finalSuggestions = [crop for crop, pts in sortedCrops][:7]
    print("Final Crop Suggestions:", finalSuggestions)
    data.suggestions = ",".join(finalSuggestions)
    db.session.commit()
    session["personalized_suggestions"] = finalSuggestions
    return redirect(url_for('feature_details', name="Basic Crop Recommendation"))

@app.route("/submission/<int:data_id>")
def submission(data_id):
    data = FarmData.query.get_or_404(data_id)
    return render_template("submission.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)
