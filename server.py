from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from datetime import datetime
import bcrypt
from dotenv import load_dotenv
import os

from crypto_utils import decrypt_data
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/location', methods=['GET'])
def get_location():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(location_data)
# ============================================
# ROUTE 6: Tamper & Accident Detection
# ESP32 vibration sensor trigger hone pe
# yahan call karega
# ============================================
@app.route('/tamper', methods=['POST'])
def tamper_detected():
    try:
        data = request.json
        
        # ESP32 se vibration intensity aur previous speed lo
        vibration_intensity = data.get('intensity', 0)
        previous_speed = data.get('previous_speed', 0)
        current_speed = location_data['speed']

        # ============================================
        # Case 1: Accident
        # Pehle chal rahi thi — achanak ruk gayi
        # ============================================
        if previous_speed > 20 and current_speed == 0 and vibration_intensity > 5:
            location_data['status'] = 'ACCIDENT DETECTED'
            print("🚨 Accident detected!")
            send_alert(
                "ACCIDENT DETECTED",
                f"Vehicle was at {previous_speed} km/h — sudden stop!",
                lat=location_data['lat'],
                lng=location_data['lng']
            )
            return jsonify({'status': 'accident alert sent'})

        # ============================================
        # Case 2: Tamper
        # Vehicle ruki hai + high vibration
        # ============================================
        elif current_speed == 0 and vibration_intensity > 5:
            location_data['status'] = 'TAMPER DETECTED'
            print("⚠️ Tamper detected!")
            send_alert(
                "PHYSICAL TAMPER DETECTED",
                "Vehicle stationary — possible theft attempt!",
                lat=location_data['lat'],
                lng=location_data['lng']
            )
            return jsonify({'status': 'tamper alert sent'})

        # ============================================
        # Case 3: Normal vibration — ignore
        # ============================================
        else:
            print("Normal vibration — ignored")
            return jsonify({'status': 'normal vibration ignored'})

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'status': 'error'}), 400

@app.route('/update', methods=['POST'])
def update_location():
    try:
        # Step 1: Encrypted data lo
        encrypted = request.json['data']

        # Step 2: Decrypt karo
        decrypted = decrypt_data(encrypted)
        lat, lng, speed = decrypted.split(',')
        lat, lng, speed = float(lat), float(lng), float(speed)

        # Step 3: Pehle previous location save karo
        prev = get_previous_location()
        safe_lat = prev['lat']
        safe_lng = prev['lng']

        # Ab spoofing check karo
        is_spoof, reason = check_spoofing(lat, lng)

        if is_spoof:
            location_data['status'] = 'SPOOFING DETECTED'
            print(f"🚨 {reason}")

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

        # Step 4: Safe hai — save karo
        location_data['lat'] = lat
        location_data['lng'] = lng
        location_data['speed'] = speed
        location_data['status'] = 'Safe'
        location_data['timestamp'] = datetime.now().strftime("%H:%M:%S")

        print(f"✅ Location saved: {lat}, {lng} | Speed: {speed} km/h")
        return jsonify({'status': 'ok'})

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'status': 'invalid data'}), 400

if __name__ == '__main__':
    app.run(debug=True)