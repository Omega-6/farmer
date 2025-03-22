from flask import Flask, render_template, url_for

app = Flask(__name__)

# Full list of features with static image filenames
features = [
    {
        "name": "Basic Crop Recommendation",
        "description": "Suggests the best crop based on soil type, weather, and month.",
        "benefit": "Helps farmers choose the right crop for higher yield & profit.",
        "complexity": "✅ Simple",
        "image": "basic_crop.png"
    },
    {
        "name": "Government Aid & Subsidy Info",
        "description": "Provides a list of available farming subsidies based on region.",
        "benefit": "Helps farmers access financial support for seeds, fertilizers, or technology.",
        "complexity": "✅ Simple",
        "image": "gov_aid.png"
    },
    {
        "name": "Soil Health Monitoring (Manual Input)",
        "description": "Allows farmers to input soil fertility levels and suggests ways to improve soil.",
        "benefit": "Prevents soil degradation and boosts long-term productivity.",
        "complexity": "✅ Simple",
        "image": "soil_health.png"
    },
    {
        "name": "Market Price Alerts (Static Data)",
        "description": "Displays current crop prices from a stored dataset.",
        "benefit": "Helps farmers decide when to sell crops for maximum profit.",
        "complexity": "✅ Simple",
        "image": "market_price_static.png"
    },
    {
        "name": "Crop Rotation Planning",
        "description": "Suggests a rotation schedule to improve soil fertility & reduce pests.",
        "benefit": "Prevents soil depletion and increases productivity.",
        "complexity": "✅ Medium",
        "image": "crop_rotation.png"
    },
    {
        "name": "Real-Time Weather API Integration",
        "description": "Fetch live weather data from OpenWeatherMap API.",
        "benefit": "Provides accurate climate data for better crop selection.",
        "complexity": "⚡ Medium",
        "image": "weather_api.png"
    },
    {
        "name": "Rainfall & Temperature Prediction",
        "description": "Uses historical weather trends to estimate future rainfall & temperature.",
        "benefit": "Farmers can plan irrigation & planting effectively.",
        "complexity": "⚡ Medium",
        "image": "rainfall_temperature.png"
    },
    {
        "name": "Fertilizer & Water Usage Recommendations",
        "description": "Suggests the best fertilizer & irrigation methods for each crop.",
        "benefit": "Saves money & resources while ensuring healthy crops.",
        "complexity": "⚡ Medium",
        "image": "fertilizer_water.png"
    },
    {
        "name": "Pest & Disease Alerts (Based on Season & Location)",
        "description": "Notifies farmers of pest infestations & diseases in their region.",
        "benefit": "Reduces crop loss by taking preventive measures in advance.",
        "complexity": "⚡ Medium",
        "image": "pest_disease.png"
    },
    {
        "name": "Supply & Demand Analysis",
        "description": "Shows which crops are in high demand in different regions.",
        "benefit": "Prevents overproduction of low-demand crops & reduces waste.",
        "complexity": "⚡ Medium",
        "image": "supply_demand.png"
    },
    {
        "name": "Market Price Alerts (Real-Time API Integration)",
        "description": "Uses APIs like USDA to fetch live crop prices from markets.",
        "benefit": "Farmers can sell crops at the best price.",
        "complexity": "🚀 Advanced",
        "image": "market_price_api.png"
    },
    {
        "name": "Harvest Time Optimization",
        "description": "Recommends best harvesting time based on weather & market trends.",
        "benefit": "Maximizes profit & crop quality.",
        "complexity": "🚀 Advanced",
        "image": "harvest_optimization.png"
    },
    {
        "name": "Drought & Flood Warnings",
        "description": "Alerts farmers about climate risks like droughts or floods.",
        "benefit": "Allows early prevention & crop protection strategies.",
        "complexity": "🚀 Advanced",
        "image": "drought_flood.png"
    },
    {
        "name": "Cooperative Farming Suggestions",
        "description": "Suggests nearby farmers growing similar crops for bulk selling.",
        "benefit": "Helps farmers negotiate better prices & reduce costs.",
        "complexity": "🚀 Advanced",
        "image": "cooperative_farming.png"
    },
    {
        "name": "AI-Based Yield Prediction",
        "description": "Uses machine learning to predict crop yield based on weather, soil, and planting time.",
        "benefit": "Helps farmers make data-driven decisions to improve productivity.",
        "complexity": "🚀 Complex",
        "image": "ai_yield.png"
    },
    {
        "name": "Automated Crop Insurance Recommendations",
        "description": "Suggests insurance plans based on crop & risk factors.",
        "benefit": "Protects farmers from financial loss due to bad weather.",
        "complexity": "🚀 Complex",
        "image": "crop_insurance.png"
    },
    {
        "name": "Integration with IoT Sensors",
        "description": "Connects to soil moisture & temperature sensors for real-time data collection.",
        "benefit": "Helps in precision farming, reducing water & fertilizer wastage.",
        "complexity": "🚀 Complex",
        "image": "iot_sensors.png"
    }
]

@app.route("/")
def home():
    return render_template("index.html", features=features)

@app.route("/feature/<name>")
def feature_details(name):
    feature = next((f for f in features if f['name'] == name), None)
    if feature:
        return render_template("feature.html", feature=feature)
    return "Feature not found", 404

if __name__ == "__main__":
    app.run(debug=True)
