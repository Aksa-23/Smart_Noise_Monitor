from flask import Flask, render_template, jsonify, request
import random
from datetime import datetime

app = Flask(__name__)

current_mode = "Study"
thresholds = {"Study": 50, "Normal": 70, "Event": 85}

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/api/live")
def api_live():
    db = round(random.uniform(38, 88), 1)
    threshold = thresholds[current_mode]
    status = "ALERT" if db >= threshold else "NORMAL"
    return jsonify({
        "db": db,
        "status": status,
        "mode": current_mode,
        "threshold": threshold,
        "alert": status == "ALERT",
        "event": False,
        "mute": False,
        "buzzer": status == "ALERT",
        "timestamp": datetime.now().strftime("%d %b %Y, %I:%M:%S %p"),
        "device_id": "rpi-008",
        "device_ip": "192.168.1.105",
        "location": "Sheltered campus area",
        "uptime": "2h 15m 33s",
        "data_source": "Raspberry Pi"
    })

@app.route("/api/mode", methods=["POST"])
def api_mode():
    global current_mode
    mode = request.get_json().get("mode")
    if mode not in thresholds:
        return jsonify({"success": False}), 400
    current_mode = mode
    return jsonify({"success": True, "mode": current_mode, "threshold": thresholds[current_mode]})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
