
import pickle
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "smart_city_secret_key"

# ---------------- DATABASE CONNECTION ----------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Hari@2983",
        database="smart_city_db"
    )

# ---------------- TRAFFIC PREDICTION ----------------
def predict_volume_and_level(hour):
    if 0 <= hour <= 5:
        return 15000, "Low"
    elif 6 <= hour <= 8:
        return 26000, "Medium"
    elif 9 <= hour <= 11:
        return 38000, "High"
    elif 12 <= hour <= 16:
        return 26000, "Medium"
    elif 17 <= hour <= 20:
        return 40000, "High"
    else:
        return 22000, "Medium"

# ---------------- LOCATION ANALYSIS ----------------
def derive_location_insights(area, hour, traffic_level):

    area_profile = {
        "Whitefield": "IT / Commercial Zone",
        "Electronic City": "Industrial / IT Zone",
        "Koramangala": "Mixed Residential & Commercial Zone",
        "Indiranagar": "Mixed Residential & Commercial Zone",
        "Hebbal": "Transport Hub",
        "Jayanagar": "Residential Zone",
        "Yeshwanthpur": "Residential Zone",
        "M.G. Road": "Commercial Zone"
    }

    area_type = area_profile.get(area, "Urban Area")

    if 7 <= hour <= 10:
        peak_dependency = "Morning Peak"
    elif 17 <= hour <= 20:
        peak_dependency = "Evening Peak"
    else:
        peak_dependency = "Off-Peak"

    if traffic_level == "High":
        traffic_sensitivity = "High"
        reason = f"High congestion due to {peak_dependency.lower()} in a {area_type.lower()}"
    elif traffic_level == "Medium":
        traffic_sensitivity = "Medium"
        reason = "Moderate traffic influenced by area usage and time of travel"
    else:
        traffic_sensitivity = "Low"
        reason = "Low traffic due to off-peak hours and reduced vehicle movement"

    return {
        "area_type": area_type,
        "traffic_sensitivity": traffic_sensitivity,
        "peak_dependency": peak_dependency,
        "reason": reason
    }

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    name = request.args.get("name")
    city = request.args.get("city")

    if not name or not city:
        return redirect(url_for("login"))

    session["name"] = name
    session["city"] = city

    return render_template("dashboard.html", name=name, city=city)

@app.route("/predict", methods=["POST"])
def predict():
    if "name" not in session:
        return redirect(url_for("login"))

    area = request.form.get("area")
    date = request.form.get("date")
    time = request.form.get("time")

    if not area or not date or not time:
        return "Missing input values", 400

    hour = int(time.split(":")[0])

    # UI prediction
    volume, traffic_level = predict_volume_and_level(hour)
    insights = derive_location_insights(area, hour, traffic_level)

    # ---------------- YEAR EXTRACTION ----------------
    year = int(date.split("-")[0])

    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ TABLE NAME FIXED HERE
    cursor.execute("""
        SELECT COUNT(*)
        FROM prediction_month_all
        WHERE area=%s AND prediction_year=%s
    """, (area, year))

    exists = cursor.fetchone()[0]

    # Generate Jan–Dec ONLY if missing
    if exists == 0:
        for month in range(1, 13):
            pseudo_hour = (month * 2) % 24
            m_volume, m_level = predict_volume_and_level(pseudo_hour)

            cursor.execute("""
                INSERT INTO prediction_month_all
                (area, prediction_year, prediction_month, traffic_volume, traffic_level)
                VALUES (%s, %s, %s, %s, %s)
            """, (area, year, month, m_volume, m_level))

    conn.commit()
    cursor.close()
    conn.close()

    session["result"] = {
        "user_name": session.get("name"),
        "area": area,
        "date": date,
        "time": time,
        "traffic_level": traffic_level,
        "predicted_volume": volume,
        "area_type": insights["area_type"],
        "traffic_sensitivity": insights["traffic_sensitivity"],
        "peak_dependency": insights["peak_dependency"],
        "reason": insights["reason"]
    }

    return redirect(url_for("result"))

@app.route("/result")
def result():
    if "result" not in session:
        return redirect(url_for("dashboard"))

    return render_template("last.html", data=session["result"])

if __name__ == "__main__":
    app.run(debug=True)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

