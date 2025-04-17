
import os
import uuid

import pandas as pd
import requests
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'a_default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///farmdata.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class FarmData(db.Model):
    __tablename__ = "farmdata"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), nullable=False)
    soil_type = db.Column(db.String(50), nullable=True)
    soil_ph = db.Column(db.Float, nullable=True)
    soil_moisture = db.Column(db.Float, nullable=True)
    temperature = db.Column(db.Float, nullable=True)  # Fahrenheit
    rainfall = db.Column(db.Float, nullable=True)
    crop_history = db.Column(db.Text, nullable=True)
    fertilizer_usage = db.Column(db.Text, nullable=True)
    pest_issues = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    suggestions = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<FarmData id={self.id} user_id={self.user_id}>"

@app.before_request
def before_request():
    db.create_all()
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())

def personalize_subsidy_info(data):
    msgs = []
    if data.city:
        msgs.append(f"Explore loan programs available in {data.city}.")
    if data.soil_type:
        msgs.append(f"Your {data.soil_type} soil may qualify for cover crop grants.")
    if data.crop_history:
        crop = data.crop_history.split(',')[0].strip()
        msgs.append(f"Since you grow {crop}, you might be eligible for specialty crop aid.")
    if data.fertilizer_usage:
        msgs.append("Fertilizer usage noted—check out EQIP for funding.")
    if data.pest_issues:
        msgs.append("Pest issues reported—explore pest control subsidies.")
    if data.rainfall is None or data.rainfall == 0:
        msgs.append("If your farm is mainly rain-fed, consider drought assistance.")
    return "<ul>" + "".join(f"<li>{m}</li>" for m in msgs) + "</ul>"

# Basic static data
basic_crop_recommendation_info = {
    "soil_types": {
        "Sandy": "Recommended Crop: Carrot, due to good drainage.",
        "Loamy": "Recommended Crop: Wheat, as loamy soil is ideal.",
        "Clay": "Recommended Crop: Rice, because clay holds water well."
    },
    "weather_conditions": {
        "Sunny": "Recommended Crop: Corn.",
        "Rainy": "Recommended Crop: Rice.",
        "Humid": "Recommended Crop: Soybean."
    },
    "monthly_suggestions": {
        "January": "Plant winter-hardy crops like Kale or Cabbage.",
        "February": "Begin early sowing of Spinach.",
        "March": "Start planting spring vegetables such as Lettuce.",
        "April": "Ideal time for warm-season crops like Tomatoes and Peppers.",
        "May": "Plant summer crops such as Corn or Beans.",
        "June": "Ensure proper irrigation for high-demand crops like Cucumbers.",
        "July": "Monitor for pests and rotate crops if needed.",
        "August": "Prepare for harvest; consider quick-growing vegetables.",
        "September": "Start planting fall crops like Broccoli.",
        "October": "Plant root vegetables for cooler temperatures.",
        "November": "Sow cover crops to improve soil fertility.",
        "December": "Rest the soil and plan for next season."
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
            "Plants": "Shallots, Spinach*, Bok Choy, Parsley; Cabbage, Leeks, Onions"
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
            "Other": "Well-drained soil, neutral to slightly alkaline."
        }
    ]
}

fertilizer_water_data = {
    "Peas": {"NPK": "10-20-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Water regularly during flowering."},
    "Fava Beans": {"NPK": "10-20-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Keep soil moist but not waterlogged."},
    "Onions": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Low", "tips": "Consistent moisture is key."},
    "Leeks": {"NPK": "12-12-12", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Steady moisture for good growth."},
    "Garlic": {"NPK": "15-10-10", "irrigation": "Drip", "water_needs": "Low", "tips": "Water sparingly after planting."},
    "Greens (Collards,Kale,Mustard)": {"NPK": "10-15-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Light, frequent watering."},
    "Turnips": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Low", "tips": "Keep soil evenly moist."},
    "White Potatoes": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "High", "tips": "Deep irrigation supports tubers."},
    "Cabbage": {"NPK": "10-15-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Consistent moisture for head development."},
    "Lettuce": {"NPK": "10-10-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Frequent watering for crisp leaves."},
    "Radishes": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Low", "tips": "Keep soil moist for quick growth."},
    "Beets": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Even moisture helps root swelling."},
    "Carrots": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Water steadily for uniform growth."},
    "Shallots": {"NPK": "12-12-12", "irrigation": "Drip", "water_needs": "Low", "tips": "Ensure good drainage."},
    "Spinach": {"NPK": "15-10-10", "irrigation": "Sprinkler", "water_needs": "High", "tips": "Regular, careful watering."},
    "Bok Choy": {"NPK": "10-15-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Steady moisture for tender leaves."},
    "Parsley": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Moderate water, well-drained soil."},
    "Swiss Chard": {"NPK": "10-15-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Prevent tip burn with even watering."},
    "Celery": {"NPK": "12-12-12", "irrigation": "Drip", "water_needs": "High", "tips": "Needs frequent water for crisp stalks."},
    "Watermelons": {"NPK": "8-10-10", "irrigation": "Drip", "water_needs": "High", "tips": "Deep watering after establishment."},
    "Winter Squash": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "High", "tips": "Consistent moisture during fruiting."},
    "Melons": {"NPK": "8-10-10", "irrigation": "Drip", "water_needs": "High", "tips": "Deep watering for large fruits."},
    "Summer Squash": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Avoid overwatering to prevent rot."},
    "Cucumbers": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "High", "tips": "Moist soil yields juicy cucumbers."},
    "Pumpkins": {"NPK": "10-10-10", "irrigation": "Sprinkler", "water_needs": "High", "tips": "Deep, infrequent watering for big fruits."},
    "Sweet Potatoes": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Keep moisture even for tuber growth."},
    "Okra": {"NPK": "10-10-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Moderate water prevents rot."},
    "Chinese Cabbage": {"NPK": "10-15-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Keep uniform moisture to avoid bitterness."},
    "Sweet Corn": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "High", "tips": "Deep watering minimizes kernel cracking."},
    "Peanuts": {"NPK": "10-20-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Good drainage is essential."},
    "Lima Beans": {"NPK": "10-20-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Keep soil consistently moist."},
    "Beans (Bush, Pole, Shell, Dried)": {"NPK": "10-20-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Avoid overwatering to prevent root rot."},
    "Black-Eyed Peas": {"NPK": "10-20-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Ensure good drainage."},
    "Eggplant": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Consistent moisture supports fruiting."},
    "Peppers": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Don't overwater to preserve flavor."},
    "Tomato": {"NPK": "10-10-10", "irrigation": "Drip", "water_needs": "High", "tips": "Deep, regular watering prevents cracking."},
    "Basil": {"NPK": "10-10-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Frequent watering and pruning."},
    "Gandules (Pigeon Peas)": {"NPK": "10-20-10", "irrigation": "Drip", "water_needs": "Moderate", "tips": "Maintain even soil moisture."},
    "Collards (Cabbage Family)": {"NPK": "10-15-10", "irrigation": "Sprinkler", "water_needs": "Moderate", "tips": "Consistent moisture supports leafy greens."}
}

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

features = [
    {"name": "Crop Recommendation", "description": "Suggests the best crop based on soil type, weather, and month.", "benefit": "Helps farmers choose the right crop for higher yield & profit.", "image": "basic_crop.png"},
    {"name": "Government Aid & Subsidy Info", "description": "Provides a list of available farming subsidies based on region.", "benefit": "Helps farmers access financial support for seeds, fertilizers, or technology.", "image": "gov_aid.png"},
    {"name": "Soil Health Monitoring", "description": "Allows farmers to input soil fertility levels and suggests ways to improve soil.", "benefit": "Prevents soil degradation and boosts long-term productivity.", "image": "soil_health.png"},
    {"name": "Market Price Alerts", "description": "Displays current crop prices from a stored dataset.", "benefit": "Helps farmers decide when to sell crops for maximum profit.", "image": "market_price_static.png"},
    {"name": "Crop Rotation Planning", "description": "Suggests a rotation schedule to improve soil fertility & reduce pests.", "benefit": "Prevents soil depletion and increases productivity.", "image": "crop_rotation.png"},
    {"name": "Real-Time Weather ", "description": "Fetch live weather data from OpenWeatherMap.", "benefit": "Provides accurate climate data for better crop selection.", "image": "weather_api.png"},
    {"name": "Fertilizer & Water Usage Recommendations", "description": "Suggests the best fertilizer & irrigation methods for each crop.", "benefit": "Saves money & resources while ensuring healthy crops.", "image": "fertilizer_water.png"},
    {"name": "Harvest Optimization", "description": "Utilizes live weather data and current market trends to pinpoint the ideal harvest window for your crops.", "benefit": "Maximizes profit & crop quality.", "image": "harvest_optimization.png"},
    {"name": "AI-Based Yield Prediction", "description": "Uses machine learning to predict crop yield based on weather, soil, and planting time.", "benefit": "Helps farmers make data-driven decisions to improve productivity.", "image": "ai_yield.png"}
]

@app.route("/")
def home():
    latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
    if latest_data:
        info = {
            "greeting": f"Hello farmer from {latest_data.city}!",
            "soil": latest_data.soil_type,
            "soil_ph": latest_data.soil_ph,
            "temperature": latest_data.temperature,
            "rainfall": latest_data.rainfall,
            "suggestions": latest_data.suggestions.split(",") if latest_data.suggestions else []
        }
    else:
        info = {
            "greeting": "Hello Farmer!",
            "soil": "Loamy",
            "soil_ph": 6.5,
            "temperature": 68,
            "rainfall": 100,
            "suggestions": []
        }
    return render_template("index.html", features=features, personalized_info=info)

@app.route("/feature/<name>", methods=["GET", "POST"])
def feature_details(name):
    feature = next((f for f in features if f['name'] == name), None)
    if not feature:
        return "Feature not found", 404
    extra_info = {}
    
    if feature['name'] == "Crop Recommendation":
        extra_info = basic_crop_recommendation_info.copy()
        latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        if latest_data and latest_data.suggestions:
            extra_info["finalSuggestions"] = latest_data.suggestions.split(",")
    elif feature['name'] == "Government Aid & Subsidy Info":
        latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        static_info = """
        <h4>Government Aid & Subsidy Info in Pennsylvania</h4>
        <p>Pennsylvania offers a range of financial assistance programs aimed at strengthening agribusiness, supporting rural development, and modernizing farming operations. Through the PA Department of Agriculture’s Agricultural Business Development Center, farmers can access:</p>
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
            pm = personalize_subsidy_info(latest_data)
            gov_info = static_info + "<hr><h5>Personalized Recommendations:</h5>" + pm
        else:
            gov_info = static_info
        extra_info = {"gov_info": gov_info}
    elif feature['name'] == "Soil Health Monitoring":
        latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        recs = []
        if latest_data:
            ph_range = (6.0, 7.0)
            moisture_optimal = 30
            if latest_data.soil_ph < ph_range[0]:
                recs.append("Soil pH is low; consider applying lime. (<a href='https://www.nrcs.usda.gov/wps/portal/nrcs/main/soils/health/' target='_blank'>NRCS Guidelines</a>)")
            elif latest_data.soil_ph > ph_range[1]:
                recs.append("Soil pH is high; add elemental sulfur or organic matter.")
            else:
                recs.append("Soil pH is optimal.")
            if latest_data.soil_moisture < moisture_optimal:
                recs.append("Soil moisture is low; increase irrigation or cover crops.")
            elif latest_data.soil_moisture > moisture_optimal:
                recs.append("Soil moisture is high; consider improved drainage.")
            else:
                recs.append("Soil moisture is optimal.")
            recs.append("Regularly add compost for better soil structure. (<a href='https://soilhealth.acs.edu/' target='_blank'>Soil Health Academy</a>)")
            recs.append("Utilize crop rotation. (<a href='https://www.sare.org/' target='_blank'>SARE</a>)")
        else:
            recs.append("No soil data available. Submit your farm data.")
        extra_info = {"recommendations": recs}
    elif feature['name'] == "Market Price Alerts":
        extra_info = {"market_prices": default_market_prices}
        ps = []
        latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        if latest_data and latest_data.crop_history:
            crops = [crop.strip().lower() for crop in latest_data.crop_history.split(",")]
            mp_lower = {k.lower(): v for k, v in default_market_prices.items()}
            for crop in crops:
                if crop in mp_lower:
                    price = mp_lower[crop]
                    ps.append(f"{crop.title()}: ${price} per unit; keep monitoring.")
        extra_info["personalized_suggestions"] = ps
    elif feature['name'] == "Crop Rotation Planning":
        latest_data = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        if latest_data and latest_data.crop_history:
            rotation_schedule = (
                "Based on your crop history, we recommend planting <strong>Legumes (Nitrogen Fixers)</strong> next. "
                "Also, consider intercropping complementary crops for better pest control and nutrient use. "
                "Adjust your schedules based on local weather and soil test results for best performance. "
                "See <a href='https://www.nrcs.usda.gov/wps/portal/nrcs/main/national/' target='_blank'>USDA NRCS</a> "
                "and <a href='https://www.sare.org/' target='_blank'>SARE</a> for guidance."
            )
        else:
            rotation_schedule = "No crop history available. Submit your farm data for crop rotation recommendations."
        extra_info = {"rotation_schedule": rotation_schedule}
    elif feature['name'] == "Real-Time Weather":
        city = request.args.get("city")
        if not city:
            latest = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
            city = latest.city if (latest and latest.city) else "Chester Springs"
        api_key = "41634f4abed439fd5c63967222a91b8b"
        w_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"
        r = requests.get(w_url)
        if r.status_code == 200:
            d = r.json()
            temp = d["main"]["temp"]
            w_desc = d["weather"][0]["description"].capitalize()
            extra_info = {
                "city": city,
                "description": w_desc,
                "temperature": temp,
                "humidity": d["main"]["humidity"],
                "wind_speed": d["wind"]["speed"]
            }
            latest = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
            recs = ""
            if latest:
                if latest.soil_moisture is not None and latest.soil_moisture < 90 and temp > 20:
                    recs += "Soil moisture is low and it's warm; consider extra irrigation. "
                if latest.rainfall is not None and latest.rainfall < 10:
                    recs += "Low rainfall detected—supplemental watering might be needed. "
            extra_info["personalized_recommendations"] = recs
        else:
            extra_info = {"error": "Could not retrieve weather data"}
    elif feature['name'] == "Fertilizer & Water Usage Recommendations":
        latest = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        rec_list = []
        if latest and latest.suggestions:
            for crop in latest.suggestions.split(","):
                crop = crop.strip()
                if crop in fertilizer_water_data:
                    rec_list.append({ "crop": crop, **fertilizer_water_data[crop] })
        extra_info = {"recommendations": rec_list}
    elif feature['name'] == "Harvest Optimization":
        latest = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        if latest and latest.suggestions:
            s_crops = [c.strip() for c in latest.suggestions.split(",")]
            city = latest.city if latest.city else "Chester Springs"
            api_key = "41634f4abed439fd5c63967222a91b8b"
            w_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"
            r = requests.get(w_url)
            if r.status_code == 200:
                w_data = r.json()
                temp = w_data["main"]["temp"]
                w_desc = w_data["weather"][0]["description"].capitalize()
            else:
                temp = None
                w_desc = "Unavailable"
            m_prices = {
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
            recs = []
            if temp is not None:
                for crop in s_crops:
                    if crop in m_prices:
                        price = m_prices[crop]
                        if temp > 20 and price > 0.5:
                            recs.append(crop)
            if recs:
                rec_text = "Optimal harvest time for: " + ", ".join(recs)
            else:
                rec_text = "Conditions are not optimal for harvest of your suggested crops."
            extra_info = {
                "harvest_recommendation": rec_text,
                "city": city,
                "temperature": temp,
                "weather_description": w_desc,
                "recommended_crops": recs
            }
        else:
            extra_info = {"harvest_recommendation": "No personalized crop suggestions available. Please submit your farm data."}
    elif feature['name'] == "AI-Based Yield Prediction":
        prediction = None
        prefill = {}
        latest = FarmData.query.filter_by(user_id=session.get('user_id')).order_by(FarmData.submitted_at.desc()).first()
        if latest:
            prefill = {
                "temperature": latest.temperature,
                "rainfall": latest.rainfall,
                "soil_ph": latest.soil_ph
            }
        if request.method == "POST":
            try:
                temp_in = float(request.form.get("temperature"))
                rain_in = float(request.form.get("rainfall"))
                ph_in = float(request.form.get("soil_ph"))
            except (ValueError, TypeError):
                prediction = "Invalid input. Please enter numeric values."
            else:
                pred_df = pd.read_csv('data/predicted_yields.csv')
                pred_df['distance'] = ((pred_df['temperature'] - temp_in) ** 2 +
                                       (pred_df['rainfall'] - rain_in) ** 2 +
                                       (pred_df['soil_ph'] - ph_in) ** 2) ** 0.5
                best_row = pred_df.loc[pred_df['distance'].idxmin()]
                yield_pred = best_row['predicted_yield']
                prediction = f"Predicted crop yield: {yield_pred:.2f} units"
        extra_info = {"prefill": prefill, "prediction": prediction}

    if extra_info is None:
        extra_info = {}
    if "market_prices" not in extra_info:
        extra_info["market_prices"] = default_market_prices

    print("Extra info for feature:", feature['name'], extra_info)
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
        soil_ph=float(request.form.get("soil_ph") or 6.5),
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
    print("Data saved:", data)

    timeToSowAndHarvest = pd.read_excel('data/timeToSowAndHarvest.xlsx', engine='openpyxl')
    waterToCrops = pd.read_excel('data/waterToCrops.xlsx', engine='openpyxl')
    phToCrops = pd.read_excel('data/phToCrops.xlsx', engine='openpyxl')
    nutrientsToCrops = pd.read_excel('data/nutrientsToCrops.xlsx', engine='openpyxl')
    cropRotationCycle = pd.read_excel('data/cropRotationCycle.xlsx', engine='openpyxl')
    
    wantedSow = request.form.get("wantedSow")
    wantedHarvest = request.form.get("wantedHarvest")
    soilPh = float(request.form.get("soil_ph") or 6.5)
    weather_input = float(request.form.get("weather"))
    previousPlantsInput = request.form.get("previousPlants")
    previousPlants = previousPlantsInput.split(", ") if previousPlantsInput else []
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
    return redirect(url_for('feature_details', name="Crop Recommendation"))

@app.route("/submission/<int:data_id>")
def submission(data_id):
    data = FarmData.query.get_or_404(data_id)
    return render_template("submission.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)
    