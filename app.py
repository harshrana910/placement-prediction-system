from flask import Flask, request, jsonify, render_template
import pickle
import numpy as np

# Create Flask app
app = Flask(__name__)

# Load Model
model = pickle.load(open("placement_model.pkl", "rb"))

# Temporary storage for dashboard
predictions_data = []

# Home route
@app.route("/")
def home():
    return "Placement Prediction API Running..."

# Test route
@app.route("/test")
def test():
    sample_data = np.array([[8.7, 2, 4, 1, 3, 85, 8]])

    prediction = model.predict(sample_data)

    result = "Placed" if prediction[0] == 1 else "Not Placed"

    return jsonify({
        "prediction": result
    })

# Frontend form route
@app.route("/form")
def form():
    return render_template("index.html")

# API Prediction Route
@app.route("/predict", methods=["POST"])
def predict():
    data = request.json

    features = np.array([[
        data["CGPA"],
        data["Internships"],
        data["Projects"],
        data["Workshops"],
        data["Certifications"],
        data["AptitudeScore"],
        data["SoftSkillsRating"]
    ]])

    prediction = model.predict(features)

    result = "Placed" if prediction[0] == 1 else "Not Placed"

    return jsonify({
        "prediction": result
    })

# HTML form prediction route
@app.route("/predict_form", methods=["POST"])
def predict_form():

    cgpa = float(request.form["CGPA"])
    internships = int(request.form["Internships"])
    projects = int(request.form["Projects"])
    workshops = int(request.form["Workshops"])
    certifications = int(request.form["Certifications"])
    aptitude = int(request.form["AptitudeScore"])
    softskills = int(request.form["SoftSkillsRating"])

    features = np.array([[

        cgpa,
        internships,
        projects,
        workshops,
        certifications,
        aptitude,
        softskills

    ]])

    # Prediction
    prediction = model.predict(features)

    # Probability
    probability = model.predict_proba(features)

    placement_probability = float(probability[0][1]) * 100

    # Result
    result = "Placed ✅" if prediction[0] == 1 else "Not Placed ❌"

    # Save into temporary list
    predictions_data.append({
        "cgpa": cgpa,
        "internships": internships,
        "projects": projects,
        "prediction": result,
        "probability": placement_probability
    })

    return render_template(
        "index.html",
        prediction_text=f"""
Prediction Result: {result}

Placement Probability: {placement_probability:.2f}%
"""
    )

# Dashboard route
@app.route("/dashboard")
def dashboard():

    placed_count = 0
    not_placed_count = 0

    for row in predictions_data:
        if "Placed" in row["prediction"] and "Not" not in row["prediction"]:
            placed_count += 1
        else:
            not_placed_count += 1

    total_predictions = len(predictions_data)

    return render_template(
        "dashboard.html",
        rows=predictions_data,
        placed_count=placed_count,
        not_placed_count=not_placed_count,
        total_predictions=total_predictions
    )

# Run server
if __name__ == "__main__":
    app.run(debug=True)