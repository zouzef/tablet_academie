import requests
import serial
from datetime import datetime
import time

# ---------------------------
# Setup
# ---------------------------
calendarId = 691

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3NTY4OTc0NDYsImV4cCI6MTc1NzUwMjI0Niwicm9sZXMiOlsiUk9MRV9TTEMiXSwidXNlcm5hbWUiOiJmNDo0ZDozMDplZTpjOToxZCJ9.xZxW_hFPQqyVw0ATY2rGUXqifREJ0oL9IZg52993TVxPzD-R6HKlgb93i8HpUnG_90cII2pEPbl9O-ncxFSprNsmwYN_rGMxLvzImv5NMpo-3eS-WgInhLoyBdsVpqH81iOLwVrYFfJye---LlWpSfF5KXPsWg3HPIw6jRTkowY5qG4BiVQNbR-vYmrjMG_YD8vZS88KmgAGGx3Fs1FfZn20yX4ZwNv-rKcCyf3B-eFUUo6azvgUpZUHHutjw_8GdNj07Lh_Ef0QHyofSoVH2uVThWBxb6KF5zj_-jQat7zVk4x94tbB-n-BeE4zLCsO3PAcFfvZCPA5fOLfOI2bxw"

API_URL = f"https://www.unistudious.com/slc/get-next-attendance/{calendarId}"

SERIAL_PORT = "/dev/ttyUSB0"  # change for your system (Windows: "COM3")
BAUD_RATE = 9600

# connect to Arduino
arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)  # wait for Arduino reset

# ---------------------------
# Function to get next session
# ---------------------------
def get_next_session():
    resp = requests.get(API_URL, headers={"Authorization": f"Bearer {token}"})
    print("Status:", resp.status_code)

    if resp.status_code == 200:
        data = resp.json()
        print("API Response:", data)

        session_data = data.get("data")
        if session_data and "start" in session_data:
            next_time_str = session_data["start"]  # "2025-09-05 08:00:30"
            return datetime.strptime(next_time_str, "%Y-%m-%d %H:%M:%S")

    return None

# ---------------------------
# Main logic
# ---------------------------
current_session = datetime.now()
next_session = get_next_session()

if next_session:
    diff_hours = (next_session - current_session).total_seconds() / 3600
    print(f"Difference: {diff_hours:.2f} hours")

    if diff_hours >= 7:
        formatted_time = next_session.strftime("%H:%M:%S")
        print("Sending to Arduino:", formatted_time)
        arduino.write(formatted_time.encode())
    else:
        print("Difference < 7 hours, nothing sent")
else:
    print("No next session found")
