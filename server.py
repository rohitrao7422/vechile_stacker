from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from datetime import datetime
import bcrypt
from dotenv import load_dotenv
import os

from spoofing_detection import check_spoofing
from telegram_alert import send_alert

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# ============================================
# Admin Password
# ============================================
PASSWORD = os.getenv('ADMIN_PASSWORD')

HASHED_PASSWORD = bcrypt.hashpw(
    PASSWORD.encode('utf-8'),
    bcrypt.gensalt()
)

# ============================================
# Vehicle Data
# ============================================
location_data = {
    "lat": 0,
    "lng": 0,
    "speed": 0,
    "status": "Safe",
    "timestamp": ""
}

# ============================================
# Login
# ============================================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if (
            username == os.getenv('ADMIN_USERNAME')
            and bcrypt.checkpw(
                password.encode('utf-8'),
                HASHED_PASSWORD
            )
        ):

            session['logged_in'] = True

            return redirect(url_for('dashboard'))

        else:

            return render_template(
                'login.html',
                error="Invalid username or password"
            )

    return render_template(
        'login.html',
        error=None
    )

# ============================================
# Logout
# ============================================
@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login'))

# ============================================
# Dashboard
# ============================================
@app.route('/')
def dashboard():

    if not session.get('logged_in'):

        return redirect(url_for('login'))

    return render_template('dashboard.html')

# ============================================
# Location API
# ============================================
@app.route('/location', methods=['GET'])
def get_location():

    return jsonify(location_data)

# ============================================
# ESP32 UPDATE ROUTE
# ESP32 sends:
# {
#   "lat": 28.6139,
#   "lng": 77.2090,
#   "speed": 45
# }
# ============================================
@app.route('/update', methods=['POST'])
def update_location():

    try:

        data = request.json

        lat = float(data['lat'])
        lng = float(data['lng'])
        speed = float(data['speed'])

        # Save location
        location_data['lat'] = lat
        location_data['lng'] = lng
        location_data['speed'] = speed
        location_data['status'] = "Safe"
        location_data['timestamp'] = datetime.now().strftime("%H:%M:%S")

        print(f"✅ Location Updated: {lat}, {lng}")

        return jsonify({
            "status": "success"
        })

    except Exception as e:

        print(f"❌ Error: {e}")

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

# ============================================
# Tamper Detection
# ============================================
@app.route('/tamper', methods=['POST'])
def tamper_detected():

    try:

        data = request.json

        vibration_intensity = data.get('intensity', 0)

        if vibration_intensity > 5:

            location_data['status'] = "TAMPER DETECTED"

            print("⚠️ Tamper detected!")

            send_alert(
                "TAMPER DETECTED",
                "Possible theft attempt detected",
                lat=location_data['lat'],
                lng=location_data['lng']
            )

            return jsonify({
                "status": "tamper alert sent"
            })

        return jsonify({
            "status": "normal"
        })

    except Exception as e:

        print(f"❌ Error: {e}")

        return jsonify({
            "status": "error"
        }), 400

# ============================================
# Run Server
# ============================================
if __name__ == '__main__':

    app.run(debug=True)
    app.run(debug=True)
