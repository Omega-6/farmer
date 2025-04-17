import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib
import numpy as np

# -------------------------------
# Step 1: Create Sample Training Data with Rainfall in 30-50 Range
# -------------------------------
data = pd.DataFrame({
    'temperature': [68, 70, 75, 80, 65, 72, 78, 85, 69, 73, 77, 82],
    'rainfall':    [30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 35],
    'soil_ph':     [6.5, 6.7, 6.8, 6.9, 6.4, 6.6, 6.8, 7.0, 6.5, 6.8, 6.7, 6.9],
    'yield':       [30, 35, 40, 45, 28, 33, 38, 50, 32, 36, 39, 47]
})

print("Training Data:")
print(data)

# -------------------------------
# Step 2: Prepare Features and Target & Train the Model
# -------------------------------
X = data[['temperature', 'rainfall', 'soil_ph']]
y = data['yield']

model = LinearRegression()
model.fit(X, y)

print("\nModel Coefficients:", model.coef_)
print("Model Intercept:", model.intercept_)

# Save the trained model for future use
joblib.dump(model, 'yield_model.pkl')
print("\nModel saved as 'yield_model.pkl'.")

# -------------------------------
# Step 3: Generate New Prediction Data
# -------------------------------
# We create 20 equally spaced values from 40 to 90 for temperature,
# from 30 to 50 for rainfall, and a chosen range for soil_ph (e.g., 6.5 to 7.2).
temperatures = np.linspace(40, 90, 20)
rainfalls = np.linspace(30, 50, 20)  # Rainfall values in the 30-50 range
soil_ph_values = np.linspace(6.5, 7.2, 20)  # Some sample soil pH values

new_data = pd.DataFrame({
    'temperature': temperatures,
    'rainfall': rainfalls,
    'soil_ph': soil_ph_values
})

# -------------------------------
# Step 4: Predict Yields for the New Data
# -------------------------------
predicted_yields = model.predict(new_data)
new_data['predicted_yield'] = predicted_yields

print("\nNew Data with Predicted Yields:")
print(new_data)

# -------------------------------
# Step 5: Export the Predicted Yields to a CSV File
# -------------------------------
new_data.to_csv('predicted_yields.csv', index=False)
print("\nPredicted yields exported to 'predicted_yields.csv'.")
