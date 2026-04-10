   # ============================================
# Telegram Alert System
# Attack detect hone pe phone pe message aayega
# ============================================

import requests
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_alert(alert_type, details, lat=None, lng=None):
    # ============================================
    # Location link banao — Google Maps ka
    # ============================================
    if lat and lng:
        maps_link = f"https://www.google.com/maps?q={lat},{lng}"
        location_text = f"📍 *Location:* [{lat}, {lng}]({maps_link})"
    else:
        location_text = "📍 *Location:* Unknown"

    # ============================================
    # Message format
    # ============================================
    message = f"""
🚨 *VEHICLE TRACKER ALERT*

⚠️ *Type:* {alert_type}
📋 *Details:* {details}
{location_text}
🕐 *Time:* {datetime.now().strftime('%H:%M:%S')}

*Immediate action required!*
    """

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    response = requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    })

    if response.status_code == 200:
        print("✅ Telegram alert sent!")
    else:
        print(f"❌ Alert failed: {response.text}")

# Test
if __name__ == '__main__':
    send_alert(
        "GPS SPOOFING DETECTED",
        "Speed: 916906 km/h — physically impossible",
        lat=28.6139,
        lng=77.2090
    )