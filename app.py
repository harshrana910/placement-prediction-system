from flask import Flask, request, jsonify, render_template
import pickle
import numpy as np
import mysql.connector

#Create Flask app
app = Flask(__name__)

#Load Model
model = pickle.load(open("placement_model.pkl","rb"))

#mysql connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="placement"
)

cursor = db.cursor()

#Home route
@app.route("/")
def home():
    return "Placement Prediction API Running..."

#Test route
@app.route("/test")
def test():
    sample_data = np.array([[8.7, 2, 4, 1, 3, 85, 8]])

    prediction = model.predict(sample_data)

    result = "Placed" if prediction[0] == 1 else "Not Placed"
    
    return jsonify({
        "prediction": result
    })

#Frontend form route
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

#HTML form prediction route
@app.route("/predict_form", methods=["POST"])
def predict_form():

    features = np.array([[

        float(request.form["CGPA"]),
        int(request.form["Internships"]),
        int(request.form["Projects"]),
        int(request.form["Workshops"]),
        int(request.form["Certifications"]),
        int(request.form["AptitudeScore"]),
        int(request.form["SoftSkillsRating"])

    ]])

    # Prediction
    prediction = model.predict(features)

    # Probability
    probability = model.predict_proba(features)

    placement_probability = float(probability[0][1]) * 100

    # Result
    result = "Placed ✅" if prediction[0] == 1 else "Not Placed ❌"

    # -----------------------------------
    # SAVE DATA INTO MYSQL
    # -----------------------------------

    sql = """
    INSERT INTO predictions (
        cgpa,
        internships,
        projects,
        workshops,
        certifications,
        aptitude_score,
        soft_skills_rating,
        prediction,
        probability
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        float(request.form["CGPA"]),
        int(request.form["Internships"]),
        int(request.form["Projects"]),
        int(request.form["Workshops"]),
        int(request.form["Certifications"]),
        int(request.form["AptitudeScore"]),
        int(request.form["SoftSkillsRating"]),
        result,
        placement_probability
    )

    cursor.execute(sql, values)

    db.commit()

    # -----------------------------------
    # RETURN RESULT TO HTML
    # -----------------------------------

    return render_template(
        "index.html",
        prediction_text=f"""
    Prediction Result: {result}

    Placement Probability: {placement_probability:.2f}%
    """
    )

@app.route("/dashboard")
def dashboard():
    cursor.execute("SELECT * FROM predictions")
    rows = cursor.fetchall()

    placed_count = 0
    not_placed_count = 0

    for row in rows:
        if "Placed" in row[8] and "Not" not in row[8]:
            placed_count += 1
        else:
            not_placed_count += 1
    total_predictions = len(rows)

    return render_template(
        "dashboard.html",
        rows=rows,
        placed_count=placed_count,
        not_placed_count=not_placed_count,
        total_predictions=total_predictions
    )

#Run server
if __name__ == "__main__":
    app.run(debug=True)


