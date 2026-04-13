# ============================================
# Vehicle Tracker - Main Server
# Updated: Plain data accept karta hai
# Encryption baad me add karenge
# ============================================

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from datetime import datetime
import bcrypt
from dotenv import load_dotenv
import os

from spoofing_detection import check_spoofing, get_previous_location
from telegram_alert import send_alert

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

PASSWORD = os.getenv('ADMIN_PASSWORD')
HASHED_PASSWORD = bcrypt.hashpw(
    PASSWORD.encode('utf-8'),
    bcrypt.gensalt()
)

location_data = {
    "lat": 32.7266,
    "lng": 74.8570,
    "speed": 0,
    "status": "Safe",
    "timestamp": ""
}

# ============================================
# ROUTE 1: Login
# ============================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == os.getenv('ADMIN_USERNAME') and bcrypt.checkpw(
            password.encode('utf-8'),
            HASHED_PASSWORD
        ):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Galat username ya password")
    return render_template('login.html', error=None)

# ============================================
# ROUTE 2: Logout
# ============================================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ============================================
# ROUTE 3: Dashboard
# ============================================
@app.route('/')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# ============================================
# ROUTE 4: Location Data — Dashboard ke liye
# ============================================
@app.route('/location', methods=['GET'])
def get_location():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(location_data)

# ============================================
# ROUTE 5: ESP32 Location Update
# Plain JSON data accept karta hai
# Format: {"lat": 32.7266, "lng": 74.857, "speed": 60}
# ============================================
@app.route('/update', methods=['POST'])
def update_location():
    try:
        data = request.json

        # Direct data lo
        lat = float(data['lat'])
        lng = float(data['lng'])
        speed = float(data['speed'])

        # Previous location save karo
        prev = get_previous_location()
        safe_lat = prev['lat']
        safe_lng = prev['lng']

        # Spoofing check karo
        is_spoof, reason = check_spoofing(lat, lng)

        if is_spoof:
            location_data['status'] = 'SPOOFING DETECTED'
            print(f"Spoofing: {reason}")

            if safe_lat is not None:
                alert_lat = safe_lat
                alert_lng = safe_lng
            else:
                alert_lat = lat
                alert_lng = lng

            send_alert(
                "GPS SPOOFING DETECTED",
                reason,
                lat=alert_lat,
                lng=alert_lng
            )
            return jsonify({
                'status': 'spoofing detected',
                'reason': reason
            }), 400

        # Safe hai — save karo
        location_data['lat'] = lat
        location_data['lng'] = lng
        location_data['speed'] = speed
        location_data['status'] = 'Safe'
        location_data['timestamp'] = datetime.now().strftime("%H:%M:%S")

        print(f"Location saved: {lat}, {lng} | Speed: {speed}")
        return jsonify({'status': 'ok'})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error'}), 400

# ============================================
# ROUTE 6: Tamper & Accident Detection
# Format: {"intensity": 7, "previous_speed": 60}
# ============================================
@app.route('/tamper', methods=['POST'])
def tamper_detected():
    try:
        data = request.json
        vibration_intensity = data.get('intensity', 0)
        previous_speed = data.get('previous_speed', 0)
        current_speed = location_data['speed']

        # Accident Detection
        if previous_speed > 20 and current_speed == 0 and vibration_intensity > 5:
            location_data['status'] = 'ACCIDENT DETECTED'
            print("Accident detected!")
            send_alert(
                "ACCIDENT DETECTED",
                f"Vehicle was at {previous_speed} km/h — sudden stop!",
                lat=location_data['lat'],
                lng=location_data['lng']
            )
            return jsonify({'status': 'accident alert sent'})

        # Tamper Detection
        elif current_speed == 0 and vibration_intensity > 5:
            location_data['status'] = 'TAMPER DETECTED'
            print("Tamper detected!")
            send_alert(
                "PHYSICAL TAMPER DETECTED",
                "Vehicle stationary — possible theft attempt!",
                lat=location_data['lat'],
                lng=location_data['lng']
            )
            return jsonify({'status': 'tamper alert sent'})

        else:
            return jsonify({'status': 'normal vibration ignored'})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error'}), 400

# ============================================
# Server Start
# ============================================
if __name__ == '__main__':
    app.run(debug=True)
