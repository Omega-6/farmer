from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import random  # Used to simulate yield predictions

app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///farmdata.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define a model to store farmer data, including city
class FarmData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    soil_type = db.Column(db.String(50))
    soil_ph = db.Column(db.Float)
    soil_moisture = db.Column(db.Float)
    temperature = db.Column(db.Float)
    rainfall = db.Column(db.Float)
    crop_history = db.Column(db.Text)
    fertilizer_usage = db.Column(db.Text)
    pest_issues = db.Column(db.Text)
    city = db.Column(db.String(100))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<FarmData {self.id}>'

# Ensure tables are created before every request (for development use only)
@app.before_request
def create_tables():
    db.create_all()

# Static list of features (without complexity)
features = [
    {
        "name": "Basic Crop Recommendation",
        "description": "Suggests the best crop based on soil type, weather, and month.",
        "benefit": "Helps farmers choose the right crop for higher yield & profit.",
        "image": "basic_crop.png"
    },
    {
        "name": "Government Aid & Subsidy Info",
        "description": "Provides a list of available farming subsidies based on region.",
        "benefit": "Helps farmers access financial support for seeds, fertilizers, or technology.",
        "image": "gov_aid.png"
    },
    {
        "name": "Soil Health Monitoring (Manual Input)",
        "description": "Allows farmers to input soil fertility levels and suggests ways to improve soil.",
        "benefit": "Prevents soil degradation and boosts long-term productivity.",
        "image": "soil_health.png"
    },
    {
        "name": "Market Price Alerts (Static Data)",
        "description": "Displays current crop prices from a stored dataset.",
        "benefit": "Helps farmers decide when to sell crops for maximum profit.",
        "image": "market_price_static.png"
    },
    {
        "name": "Crop Rotation Planning",
        "description": "Suggests a rotation schedule to improve soil fertility & reduce pests.",
        "benefit": "Prevents soil depletion and increases productivity.",
        "image": "crop_rotation.png"
    },
    {
        "name": "Real-Time Weather API Integration",
        "description": "Fetch live weather data from OpenWeatherMap API.",
        "benefit": "Provides accurate climate data for better crop selection.",
        "image": "weather_api.png"
    },
    {
        "name": "Rainfall & Temperature Prediction",
        "description": "Uses historical weather trends to estimate future rainfall & temperature.",
        "benefit": "Farmers can plan irrigation & planting effectively.",
        "image": "rainfall_temperature.png"
    },
    {
        "name": "Fertilizer & Water Usage Recommendations",
        "description": "Suggests the best fertilizer & irrigation methods for each crop.",
        "benefit": "Saves money & resources while ensuring healthy crops.",
        "image": "fertilizer_water.png"
    },
    {
        "name": "Pest & Disease Alerts (Based on Season & Location)",
        "description": "Notifies farmers of pest infestations & diseases in their region.",
        "benefit": "Reduces crop loss by taking preventive measures in advance.",
        "image": "pest_disease.png"
    },
    {
        "name": "Supply & Demand Analysis",
        "description": "Shows which crops are in high demand in different regions.",
        "benefit": "Prevents overproduction of low-demand crops & reduces waste.",
        "image": "supply_demand.png"
    },
    {
        "name": "Market Price Alerts (Real-Time API Integration)",
        "description": "Uses APIs like USDA to fetch live crop prices from markets.",
        "benefit": "Farmers can sell crops at the best price.",
        "image": "market_price_api.png"
    },
    {
        "name": "Harvest Time Optimization",
        "description": "Recommends best harvesting time based on weather & market trends.",
        "benefit": "Maximizes profit & crop quality.",
        "image": "harvest_optimization.png"
    },
    {
        "name": "Drought & Flood Warnings",
        "description": "Alerts farmers about climate risks like droughts or floods.",
        "benefit": "Allows early prevention & crop protection strategies.",
        "image": "drought_flood.png"
    },
    {
        "name": "Cooperative Farming Suggestions",
        "description": "Suggests nearby farmers growing similar crops for bulk selling.",
        "benefit": "Helps farmers negotiate better prices & reduce costs.",
        "image": "cooperative_farming.png"
    },
    {
        "name": "AI-Based Yield Prediction",
        "description": "Uses machine learning to predict crop yield based on weather, soil, and planting time.",
        "benefit": "Helps farmers make data-driven decisions to improve productivity.",
        "image": "ai_yield.png"
    },
    {
        "name": "Automated Crop Insurance Recommendations",
        "description": "Suggests insurance plans based on crop & risk factors.",
        "benefit": "Protects farmers from financial loss due to bad weather.",
        "image": "crop_insurance.png"
    },
    {
        "name": "Integration with IoT Sensors",
        "description": "Connects to soil moisture & temperature sensors for real-time data collection.",
        "benefit": "Helps in precision farming, reducing water & fertilizer wastage.",
        "image": "iot_sensors.png"
    }
]

# Extra static info for "Basic Crop Recommendation"
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
    }
}

# Route: Home page
@app.route("/")
def home():
    return render_template("index.html", features=features)

# Route: Feature details page (supports GET and POST for yield prediction)
@app.route("/feature/<name>", methods=["GET", "POST"])
def feature_details(name):
    feature = next((f for f in features if f['name'] == name), None)
    if not feature:
        return "Feature not found", 404

    extra_info = None
    # Basic Crop Recommendation extra info
    if feature['name'] == "Basic Crop Recommendation":
        extra_info = basic_crop_recommendation_info

    # Real-Time Weather API Integration
    elif feature['name'] == "Real-Time Weather API Integration":
        city = request.args.get("city")
        if not city:
            latest_data = FarmData.query.order_by(FarmData.submitted_at.desc()).first()
            if latest_data and latest_data.city:
                city = latest_data.city
            else:
                city = "Chester Springs"
        api_key = "41634f4abed439fd5c63967222a91b8b"  # Your OpenWeatherMap API key
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
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

    # AI-Based Yield Prediction: Handle GET and POST in the same feature page
    elif feature['name'] == "AI-Based Yield Prediction":
        prediction = None
        prefill = {}
        latest_data = FarmData.query.order_by(FarmData.submitted_at.desc()).first()
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
                # Simulate prediction with a random value (replace with your model later)
                pred_value = random.uniform(50, 150)
                prediction = f"Predicted crop yield: {pred_value:.2f} units"
        extra_info = {"prefill": prefill, "prediction": prediction}

    return render_template("feature.html", feature=feature, extra_info=extra_info)

# Route: Input form for farmer data (includes city)
@app.route("/input", methods=["GET"])
def input_form():
    return render_template("input.html")

# Route: Process form submission and save data to the database
@app.route("/submit", methods=["POST"])
def submit():
    data = FarmData(
        soil_type = request.form.get("soil_type"),
        soil_ph = float(request.form.get("soil_ph") or 0),
        soil_moisture = float(request.form.get("soil_moisture") or 0),
        temperature = float(request.form.get("temperature") or 0),
        rainfall = float(request.form.get("rainfall") or 0),
        crop_history = request.form.get("crop_history"),
        fertilizer_usage = request.form.get("fertilizer_usage"),
        pest_issues = request.form.get("pest_issues"),
        city = request.form.get("city")
    )
    db.session.add(data)
    db.session.commit()
    return redirect(url_for('submission', data_id=data.id))

# Route: Display stored submission data
@app.route("/submission/<int:data_id>")
def submission(data_id):
    data = FarmData.query.get_or_404(data_id)
    return render_template("submission.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)
