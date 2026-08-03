from flask import (
    Flask, request, jsonify, render_template,
    make_response
)
import pickle
import numpy as np
import mysql.connector
import csv
import io

from config import DB_CONFIG

# ── Flask App ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

# ── ML Model ──────────────────────────────────────────────────────────────────
# Load the pre-trained placement prediction model once at startup.
model = pickle.load(open("placement_model.pkl", "rb"))


# ── Database Helper ───────────────────────────────────────────────────────────
def get_db_connection():
    """
    Attempt to open a MySQL connection using DB_CONFIG.

    Returns:
        mysql.connector.connection  on success
        None                        on any error (logs details to console)

    All callers must check for None and degrade gracefully — the app must
    never crash just because the database is temporarily unavailable.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        # Log the real error server-side; surface only a friendly message to UI
        print("[DB ERROR] Could not connect to MySQL:", e)
        return None


# ── Home Route ────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    """Render the main prediction form. No DB interaction needed here."""
    return render_template("index.html")


# ── JSON API Prediction Route ─────────────────────────────────────────────────
@app.route("/predict", methods=["POST"])
def predict():
    """
    REST API endpoint — accepts JSON, returns prediction.
    Also persists the result to MySQL when the DB is available.
    """
    data = request.json

    # Build feature array for the model
    features = np.array([[
        data["CGPA"],
        data["Internships"],
        data["Projects"],
        data["Workshops"],
        data["Certifications"],
        data["AptitudeScore"],
        data["SoftSkillsRating"]
    ]])

    # ML inference (untouched logic)
    prediction            = model.predict(features)
    probability           = model.predict_proba(features)
    placement_probability = float(probability[0][1]) * 100
    result                = "Placed" if prediction[0] == 1 else "Not Placed"

    # Persist to MySQL — if DB is down, API still responds normally
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO predictions
                   (cgpa, internships, projects, workshops, certifications,
                    aptitude_score, soft_skills_rating, prediction, probability)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    float(data["CGPA"]),
                    int(data["Internships"]),
                    int(data["Projects"]),
                    int(data["Workshops"]),
                    int(data["Certifications"]),
                    int(data["AptitudeScore"]),
                    int(data["SoftSkillsRating"]),
                    result,
                    placement_probability
                )
            )
            conn.commit()
        except mysql.connector.Error as e:
            print("[DB ERROR] Failed to save API prediction:", e)
        finally:
            if conn.is_connected():
                conn.close()
    else:
        print("[DB WARNING] API prediction not persisted — MySQL unavailable.")

    return jsonify({"prediction": result})


# ── HTML Form Prediction Route ────────────────────────────────────────────────
@app.route("/predict_form", methods=["POST"])
def predict_form():
    """
    Handles the HTML form submission.
    Parses inputs → validates → runs ML inference → saves to MySQL → renders result.

    IMPORTANT: form field names (CGPA, Internships, etc.) must not change —
    they are bound to the HTML <input name="..."> attributes.
    """

    # ── Field definitions: (form_name, type_fn, min, max, display_label) ─────
    FIELDS = [
        ("CGPA",            float, 0.0,  10.0, "CGPA (0 – 10)"),
        ("Internships",     int,   0,    50,   "Internships"),
        ("Projects",        int,   0,    50,   "Projects"),
        ("Workshops",       int,   0,    50,   "Workshops"),
        ("Certifications",  int,   0,    50,   "Certifications"),
        ("AptitudeScore",   int,   0,    100,  "Aptitude Score (0 – 100)"),
        ("SoftSkillsRating",int,   1,    10,   "Soft Skills Rating (1 – 10)"),
    ]

    # ── Server-side validation ─────────────────────────────────────────────
    # Catches: empty fields, non-numeric input, and out-of-range values.
    # HTML `required` is client-side only — this is the authoritative check.
    parsed = {}
    try:
        for field, type_fn, lo, hi, label in FIELDS:
            raw = request.form.get(field, "").strip()
            if raw == "":
                raise ValueError(f"'{label}' is required and cannot be empty.")
            val = type_fn(raw)
            if not (lo <= val <= hi):
                raise ValueError(
                    f"'{label}' must be between {lo} and {hi}. Got: {val}"
                )
            parsed[field] = val
    except ValueError as e:
        print(f"[VALIDATION ERROR] {e}")
        return render_template(
            "index.html",
            prediction_text=f"⚠️ Input Error: {e}"
        )

    # ── Unpack validated values ────────────────────────────────────────────
    cgpa           = parsed["CGPA"]
    internships    = parsed["Internships"]
    projects       = parsed["Projects"]
    workshops      = parsed["Workshops"]
    certifications = parsed["Certifications"]
    aptitude       = parsed["AptitudeScore"]
    softskills     = parsed["SoftSkillsRating"]

    # ── Build feature array ──────────────────────────────────────────────────
    features = np.array([[
        cgpa, internships, projects,
        workshops, certifications,
        aptitude, softskills
    ]])

    # ── ML Inference (original logic — do not modify) ────────────────────────
    prediction            = model.predict(features)
    probability           = model.predict_proba(features)
    placement_probability = float(probability[0][1]) * 100
    result                = "Placed ✅" if prediction[0] == 1 else "Not Placed ❌"

    # ── Persist to MySQL ─────────────────────────────────────────────────────
    # If MySQL is down, the prediction result is still shown to the user.
    # A warning is logged server-side; the homepage never crashes.
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO predictions
                   (cgpa, internships, projects, workshops, certifications,
                    aptitude_score, soft_skills_rating, prediction, probability)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    cgpa, internships, projects, workshops, certifications,
                    aptitude, softskills, result, placement_probability
                )
            )
            conn.commit()
            print("[DB INFO] Prediction saved to MySQL.")
        except mysql.connector.Error as e:
            print("[DB ERROR] Failed to save prediction:", e)
        finally:
            if conn.is_connected():
                conn.close()
    else:
        # Log, but do NOT disrupt the user experience
        print("[DB WARNING] Prediction made but not persisted — MySQL unavailable.")

    # ── Render result (Jinja variable preserved exactly) ─────────────────────
    return render_template(
        "index.html",
        prediction_text=f"""
Prediction Result: {result}

Placement Probability: {placement_probability:.2f}%
"""
    )


# ── Dashboard Route ───────────────────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    """
    Reads all predictions from MySQL and renders the analytics dashboard.
    If the DB is unavailable, renders an empty dashboard with a friendly
    error banner — the page still loads cleanly.
    """

    # ── Graceful fallback when DB is unreachable ─────────────────────────────
    conn = get_db_connection()
    if conn is None:
        return render_template(
            "dashboard.html",
            rows=[],
            placed_count=0,
            not_placed_count=0,
            total_predictions=0,
            db_error=(
                "Could not connect to the database. "
                "Please ensure MySQL is running on localhost:3306."
            )
        )

    try:
        # Use dictionary cursor so Jinja can access row["cgpa"] etc. directly
        cursor = conn.cursor(dictionary=True)

        # Fetch all predictions, newest first
        cursor.execute("SELECT * FROM predictions ORDER BY created_at DESC")
        rows = cursor.fetchall()

        # Format timestamp into a human-readable string for display
        for row in rows:
            if row.get("created_at"):
                row["created_at"] = row["created_at"].strftime("%d %b %Y, %H:%M")

        # Compute stats in Python (avoids an extra SQL round-trip)
        placed_count      = sum(1 for r in rows if "Not" not in r["prediction"])
        not_placed_count  = sum(1 for r in rows if "Not" in r["prediction"])
        total_predictions = len(rows)

        return render_template(
            "dashboard.html",
            rows=rows,
            placed_count=placed_count,
            not_placed_count=not_placed_count,
            total_predictions=total_predictions,
            db_error=None
        )

    except mysql.connector.Error as e:
        print("[DB ERROR] Failed to fetch dashboard data:", e)
        return render_template(
            "dashboard.html",
            rows=[],
            placed_count=0,
            not_placed_count=0,
            total_predictions=0,
            db_error="Database error: Could not load prediction history. Check the server logs."
        )
    finally:
        if conn.is_connected():
            conn.close()


# ── Delete All — DISABLED FOR PRODUCTION ─────────────────────────────────────
@app.route("/delete_all", methods=["GET", "POST"])
def delete_all():
    """
    This route is intentionally disabled for public/production deployments.

    Accepting both GET and POST ensures that anyone who tries to call this
    endpoint — whether via the old form, a curl command, or a direct URL —
    always receives HTTP 403 Forbidden with a clear message.

    The 'Delete All' button has been removed from the dashboard UI.
    No database interaction is performed here.
    """
    return (
        "403 Forbidden: The delete-all operation has been disabled "
        "on this deployment.",
        403
    )


# ── Export CSV ────────────────────────────────────────────────────────────────
@app.route("/export_csv")
def export_csv():
    """
    Streams the full predictions table as a downloadable CSV file.
    Returns HTTP 503 if the DB is unreachable, 500 on a query error.
    """
    conn = get_db_connection()
    if conn is None:
        return "Database unavailable. Cannot export CSV at this time.", 503

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM predictions ORDER BY created_at DESC")
        rows = cursor.fetchall()

        # Build CSV content in memory
        output = io.StringIO()
        fieldnames = [
            "id", "cgpa", "internships", "projects", "workshops",
            "certifications", "aptitude_score", "soft_skills_rating",
            "prediction", "probability", "created_at"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

        # Return as a file download attachment
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = (
            "attachment; filename=placement_predictions.csv"
        )
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        return response

    except mysql.connector.Error as e:
        print("[DB ERROR] Failed to export CSV:", e)
        return "Database error: Could not export data.", 500
    finally:
        if conn.is_connected():
            conn.close()


# ── Run Server ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)