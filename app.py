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
    temperature = db.Column(db.Float)  # Now stores Fahrenheit
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

# Static extra info for "Basic Crop Recommendation" (mock data)
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

# Static dictionary for Fertilizer & Water Usage Recommendations
fertilizer_water_data = {
    "Peas": {"NPK": "10-20-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Water regularly during flowering."},
    "Fava Beans": {"NPK": "10-20-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Keep soil moist but not waterlogged."},
    "Onions": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Low", "tips": "Avoid overwatering to prevent bulb rot."},
    "Leeks": {"NPK": "12-12-12", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Ensure consistent moisture for uniform growth."},
    "Garlic": {"NPK": "15-10-10", "irrigation": "Drip", "water_needs": "Low", "tips": "Provide well-draining soil and moderate irrigation."},
    "Greens (Collards, Kale, Mustard, Turnip, Etc.)": {"NPK": "10-15-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Ensure even watering to prevent bolting."},
    "Turnips": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Low", "tips": "Keep soil evenly moist for best root development."},
    "White Potatoes": {"NPK": "10-10-10", "irrigation": "Sprinkler", "water_needs": "High", "tips": "Irrigate deeply to encourage tuber formation."},
    "Cabbage": {"NPK": "10-15-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Keep soil consistently moist to prevent splitting."},
    "Lettuce": {"NPK": "10-10-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Frequent light watering to keep leaves tender."},
    "Radishes": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Low", "tips": "Water consistently but avoid overwatering."},
    "Beets": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Ensure even moisture for root swelling."},
    "Carrots": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Water consistently for uniform root development."},
    "Shallots": {"NPK": "12-12-12", "irrigation": "Drip", "water_needs": "Low", "tips": "Provide well-drained soil and moderate watering."},
    "Spinach": {"NPK": "15-10-10", "irrigation": "Sprinkler", "water_needs": "High", "tips": "Needs consistent watering; avoid drought stress."},
    "Bok Choy": {"NPK": "10-15-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Maintain moisture levels for crisp leaves."},
    "Parsley": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Keep soil moist and provide partial shade."},
    "Swiss Chard": {"NPK": "10-15-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Water evenly to prevent tip burn."},
    "Celery": {"NPK": "12-12-12", "irrigation": "Drip", "water_needs": "High", "tips": "Celery needs lots of water to develop properly."},
    "Watermelons": {"NPK": "8-10-10", "irrigation": "Drip", "water_needs": "High", "tips": "Irrigate deeply but infrequently once established."},
    "Winter Squash": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "High", "tips": "Water deeply and regularly during fruiting."},
    "Melons": {"NPK": "8-10-10", "irrigation": "Drip", "water_needs": "High", "tips": "Ensure deep watering to support large fruits."},
    "Summer Squash": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Maintain consistent moisture for best yield."},
    "Cucumbers": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "High", "tips": "Regular watering ensures crisp, healthy cucumbers."},
    "Pumpkins": {"NPK": "10-10-10", "irrigation": "Sprinkler", "water_needs": "High", "tips": "Deep, infrequent watering helps form large pumpkins."},
    "Sweet Potatoes": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Consistent moisture supports tuber development."},
    "Okra": {"NPK": "10-10-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Regular watering is key during the growing season."},
    "Chinese Cabbage": {"NPK": "10-15-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Keep soil moist to avoid bitterness."},
    "Sweet Corn": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "High", "tips": "Deep watering helps prevent cracking."},
    "Peanuts": {"NPK": "10-20-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Ensure proper drainage to prevent waterlogging."},
    "Lima Beans": {"NPK": "10-20-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Maintain even moisture during flowering."},
    "Beans (Bush, Pole, Shell, Dried)": {"NPK": "10-20-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Avoid overwatering to prevent root rot."},
    "Black-Eyed Peas": {"NPK": "10-20-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Good drainage is key for healthy growth."},
    "Eggplant": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Consistent moisture supports robust fruiting."},
    "Peppers": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Avoid over-fertilizing to maintain flavor."},
    "Tomato": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "High", "tips": "Deep watering helps prevent cracking."},
    "Basil": {"NPK": "10-10-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Regular watering and pruning keeps basil thriving."},
    "Gandules (Pigeon Peas)": {"NPK": "10-20-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Good drainage and moderate watering recommended."},
    "Collards (Cabbage Family)": {"NPK": "10-15-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Consistent moisture helps maintain leafy greens."}
}

# Static list of features (for navigation and display)
features = [
    {"name": "Basic Crop Recommendation", "description": "Suggests the best crop based on soil type, weather, and month.", "benefit": "Helps farmers choose the right crop for higher yield & profit.", "image": "basic_crop.png"},
    {"name": "Government Aid & Subsidy Info", "description": "Provides a list of available farming subsidies based on region.", "benefit": "Helps farmers access financial support for seeds, fertilizers, or technology.", "image": "gov_aid.png"},
    {"name": "Soil Health Monitoring", "description": "Allows farmers to input soil fertility levels and suggests ways to improve soil.", "benefit": "Prevents soil degradation and boosts long-term productivity.", "image": "soil_health.png"},
    {"name": "Market Price Alerts (Static Data)", "description": "Displays current crop prices from a stored dataset.", "benefit": "Helps farmers decide when to sell crops for maximum profit.", "image": "market_price_static.png"},
    {"name": "Crop Rotation Planning", "description": "Suggests a rotation schedule to improve soil fertility & reduce pests.", "benefit": "Prevents soil depletion and increases productivity.", "image": "crop_rotation.png"},
    {"name": "Real-Time Weather API Integration", "description": "Fetch live weather data from OpenWeatherMap API.", "benefit": "Provides accurate climate data for better crop selection.", "image": "weather_api.png"},
    {"name": "Rainfall & Temperature Prediction", "description": "Uses historical weather trends to estimate future rainfall & temperature.", "benefit": "Farmers can plan irrigation & planting effectively.", "image": "rainfall_temperature.png"},
    {"name": "Fertilizer & Water Usage Recommendations", "description": "Suggests the best fertilizer & irrigation methods for each crop.", "benefit": "Saves money & resources while ensuring healthy crops.", "image": "fertilizer_water.png"},
    {"name": "Pest & Disease Alerts (Based on Season & Location)", "description": "Notifies farmers of pest infestations & diseases in their region.", "benefit": "Reduces crop loss by taking preventive measures in advance.", "image": "pest_disease.png"},
    {"name": "Supply & Demand Analysis", "description": "Shows which crops are in high demand in different regions.", "benefit": "Prevents overproduction of low-demand crops & reduces waste.", "image": "supply_demand.png"},
    {"name": "Market Price Alerts (Real-Time API Integration)", "description": "Uses APIs like USDA to fetch live crop prices from markets.", "benefit": "Farmers can sell crops at the best price.", "image": "market_price_api.png"},
    {"name": "Harvest Time Optimization", "description": "Recommends best harvesting time based on weather & market trends.", "benefit": "Maximizes profit & crop quality.", "image": "harvest_optimization.png"},
    {"name": "Drought & Flood Warnings", "description": "Alerts farmers about climate risks like droughts or floods.", "benefit": "Allows early prevention & crop protection strategies.", "image": "drought_flood.png"},
    {"name": "Cooperative Farming Suggestions", "description": "Suggests nearby farmers growing similar crops for bulk selling.", "benefit": "Helps farmers negotiate better prices & reduce costs.", "image": "cooperative_farming.png"},
    {"name": "AI-Based Yield Prediction", "description": "Uses machine learning to predict crop yield based on weather, soil, and planting time.", "benefit": "Helps farmers make data-driven decisions to improve productivity.", "image": "ai_yield.png"},
    {"name": "Automated Crop Insurance Recommendations", "description": "Suggests insurance plans based on crop & risk factors.", "benefit": "Protects farmers from financial loss due to bad weather.", "image": "crop_insurance.png"},
    {"name": "Integration with IoT Sensors", "description": "Connects to soil moisture & temperature sensors for real-time data collection.", "benefit": "Helps in precision farming, reducing water & fertilizer wastage.", "image": "iot_sensors.png"}
]

# Home route: Display features and personalized greeting based on latest farm data for the current session
@app.route("/")
def home():
    latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
    if latest_data:
        personalized_info = {
            "greeting": f"Hello farmer from {latest_data.city}!",
            "soil": latest_data.soil_type,
            "soil_ph": latest_data.soil_ph,
            "temperature": latest_data.temperature,  # Fahrenheit value
            "rainfall": latest_data.rainfall,
            "suggestions": latest_data.suggestions.split(",") if latest_data.suggestions else []
        }
    else:
        personalized_info = {
            "greeting": "Hello Farmer!",
            "soil": "Loamy",
            "soil_ph": 6.5,
            "temperature": 68,  # Default 68°F (~20°C)
            "rainfall": 100,
            "suggestions": []
        }
    return render_template("index.html", features=features, personalized_info=personalized_info)

# Feature details route: Render specific feature page based on feature name
@app.route("/feature/<name>", methods=["GET", "POST"])
def feature_details(name):
    feature = next((f for f in features if f['name'] == name), None)
    if not feature:
        return "Feature not found", 404

    extra_info = None

    if feature['name'] == "Basic Crop Recommendation":
        extra_info = basic_crop_recommendation_info.copy()
        latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        if latest_data and latest_data.suggestions:
            extra_info["finalSuggestions"] = latest_data.suggestions.split(",")
    
    elif feature['name'] == "Real-Time Weather API Integration":
        city = request.args.get("city")
        if not city:
            latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
            city = latest_data.city if (latest_data and latest_data.city) else "Chester Springs"
        api_key = "41634f4abed439fd5c63967222a91b8b"  # Replace with your actual API key
        # Use imperial units to get Fahrenheit
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"
        response = requests.get(weather_url)
        if response.status_code == 200:
            data = response.json()
            extra_info = {
                "city": city,
                "description": data["weather"][0]["description"].capitalize(),
                "temperature": data["main"]["temp"],  # Fahrenheit
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
        # Harvest Time Optimization using personalized crop suggestions from the database
        latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        if latest_data and latest_data.suggestions:
            # Get personalized crop suggestions from the database
            suggested_crops = [crop.strip() for crop in latest_data.suggestions.split(",")]
            city = latest_data.city if latest_data.city else "Chester Springs"
            # Get current weather info in Fahrenheit from OpenWeatherMap API
            api_key = "41634f4abed439fd5c63967222a91b8b"  # Replace with your actual API key
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"
            response = requests.get(weather_url)
            if response.status_code == 200:
                weather_data = response.json()
                temperature = weather_data["main"]["temp"]  # Fahrenheit
                weather_desc = weather_data["weather"][0]["description"].capitalize()
            else:
                temperature = None
                weather_desc = "Unavailable"
            # Use a static dictionary of market prices for simulation (assumed in $ per unit)
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
            # Debug: print suggested crops for harvest
            print("Suggested crops from DB:", suggested_crops)
            if temperature is not None:
                # Change threshold: Temperature > 68°F (~20°C) now, adjust as needed
                for crop in suggested_crops:
                    if crop in market_prices:
                        price = market_prices[crop]
                        if temperature > 1 and price > .5:
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
    
    elif feature['name'] == "Government Aid & Subsidy Info":
        extra_info = {
            "gov_info": """
                <h4>Government Aid & Subsidy Info in Pennsylvania</h4>
                <p>Pennsylvania offers a range of financial assistance programs aimed at strengthening agribusiness, supporting rural development, and modernizing farming operations. Through the PA Department of Agriculture’s Agricultural Business Development Center, farmers can access:</p>
                <ul>
                    <li><strong>Direct Loan & Loan Guarantee Programs:</strong> Low‑interest loans to support equipment upgrades, production expansion, and risk mitigation.</li>
                    <li><strong>Grant Programs & Financial Assistance:</strong> Competitive grants for business planning, infrastructure improvements, and adopting sustainable practices.</li>
                    <li><strong>Technical Assistance & Training:</strong> Expert guidance on financial management, marketing, and best practices to boost productivity and profitability.</li>
                    <li><strong>Disaster Assistance:</strong> Emergency support programs for severe weather or natural disasters.</li>
                </ul>
                <p>Additional resources:</p>
                <ul>
                    <li><a href="https://www.pa.gov/agencies/pda/business-and-industry/agricultural-business-development-center/financial-assistance.html" target="_blank">PA Agricultural Business Development Center - Financial Assistance</a></li>
                    <li><a href="https://www.fsa.usda.gov/" target="_blank">USDA Farm Service Agency</a></li>
                    <li><a href="https://www.agriculture.pa.gov/" target="_blank">Pennsylvania Department of Agriculture</a></li>
                </ul>
            """
        }
    
    elif feature['name'] == "Soil Health Monitoring":
        latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        recommendations = []
        if latest_data:
            optimal_ph_range = (6.0, 7.0)
            optimal_moisture = 30  # percentage

            if latest_data.soil_ph < optimal_ph_range[0]:
                recommendations.append(
                    "Soil pH is low (acidic). Consider applying lime to raise the pH. For details, see the <a href='https://www.nrcs.usda.gov/wps/portal/nrcs/main/soils/health/' target='_blank'>NRCS Soil Health Guidelines</a>."
                )
            elif latest_data.soil_ph > optimal_ph_range[1]:
                recommendations.append(
                    "Soil pH is high (alkaline). Consider adding elemental sulfur or organic matter to lower the pH. Consult your local extension."
                )
            else:
                recommendations.append("Soil pH is within the optimal range.")

            if latest_data.soil_moisture < optimal_moisture:
                recommendations.append(
                    "Soil moisture is low. Increase irrigation, add organic mulches, or use cover crops to retain moisture. See USDA Soil Conservation resources."
                )
            elif latest_data.soil_moisture > optimal_moisture:
                recommendations.append(
                    "Soil moisture is high. Consider improved drainage, such as raised beds or drainage tiles."
                )
            else:
                recommendations.append("Soil moisture is optimal.")

            recommendations.append(
                "Regularly add compost or manure to improve soil structure and nutrient availability. Refer to the <a href='https://soilhealth.acs.edu/' target='_blank'>Soil Health Academy</a> for tips."
            )
            recommendations.append(
                "Plant cover crops and use crop rotation strategies to enhance soil fertility and reduce erosion. Check out <a href='https://www.sare.org/' target='_blank'>SARE</a> for guidelines."
            )
        else:
            recommendations.append("No soil data available. Please submit your farm data for personalized recommendations.")
        extra_info = {"recommendations": recommendations}
    
    elif feature['name'] == "Market Price Alerts (Static Data)":
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
        extra_info = {"market_prices": market_prices}
        personalized_suggestions = []
        latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        if latest_data and latest_data.crop_history:
            crops = [crop.strip() for crop in latest_data.crop_history.split(",")]
            for crop in crops:
                if crop in market_prices:
                    price = market_prices[crop]
                    if crop == "Sweet Corn" and price > 3.0:
                        personalized_suggestions.append(f"{crop}: Current price ${price} is above average; consider selling soon!")
                    elif crop == "Wheat" and price > 4.5:
                        personalized_suggestions.append(f"{crop}: Current price ${price} is attractive; consider selling.")
                    elif crop == "Soybean" and price > 8.0:
                        personalized_suggestions.append(f"{crop}: Current price ${price} is high; consider selling.")
                    elif crop == "Rice" and price > 1.0:
                        personalized_suggestions.append(f"{crop}: Current price ${price} is favorable; think about selling.")
                    else:
                        personalized_suggestions.append(f"{crop}: Current price ${price} is moderate; keep monitoring.")
        extra_info["personalized_suggestions"] = personalized_suggestions
    
    elif feature['name'] == "Crop Rotation Planning":
        latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        if latest_data and latest_data.crop_history:
            crops = [crop.strip() for crop in latest_data.crop_history.split(",")]
            legumes = {"Peas", "Fava Beans", "Black-Eyed Peas", "Peanuts", "Lima Beans", "Beans (Bush, Pole, Shell, Dried)"}
            heavy_feeders = {"Tomato", "Peppers", "Eggplant", "Sweet Corn", "Pumpkins", "Watermelons"}
            light_feeders = {"Lettuce", "Radishes", "Carrots", "Onions", "Garlic"}
            cover_crops = {"Cabbage", "Collards (Cabbage Family)", "Spinach", "Swiss Chard"}
            recent_legumes = any(crop in legumes for crop in crops)
            recent_heavy = any(crop in heavy_feeders for crop in crops)
            recent_light = any(crop in light_feeders for crop in crops)
            recent_cover = any(crop in cover_crops for crop in crops)
            if not (recent_legumes or recent_heavy or recent_light or recent_cover):
                rotation_schedule = "Default Rotation: Year 1 - Legumes; Year 2 - Heavy Feeders; Year 3 - Light Feeders; Year 4 - Cover Crops."
            else:
                if not recent_legumes:
                    next_group = "Legumes (Nitrogen Fixers)"
                elif not recent_heavy:
                    next_group = "Heavy Feeders"
                elif not recent_light:
                    next_group = "Light Feeders"
                elif not recent_cover:
                    next_group = "Cover Crops"
                else:
                    next_group = "Alternate crops for balanced soil health"
                rotation_schedule = f"Based on your crop history, we recommend planting {next_group} next."
        else:
            rotation_schedule = "No crop history available. Please submit your farm data to receive personalized crop rotation recommendations."
        extra_info = {"rotation_schedule": rotation_schedule}
    
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
        temperature=float(request.form.get("temperature") or 0),  # Now stored in Fahrenheit
        rainfall=float(request.form.get("rainfallAmount") or 0),
        crop_history=request.form.get("crop_history"),
        fertilizer_usage=request.form.get("fertilizer_usage"),
        pest_issues=request.form.get("pest_issues"),
        city=request.form.get("location")
    )
    db.session.add(data)
    db.session.commit()

    # Read Excel files from the 'data' folder (ensure these files exist)
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
