
import json
import threading
import time

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, request
from flask_cors import CORS

from alerts import evaluate_noise
from database import init_db, insert_reading, get_latest_reading, get_latest_readings
from forecast import generate_forecast


# ============================================================
# MQTT settings
# ============================================================
BROKER = "localhost"
PORT = 1883
TOPIC = "smart_noise/readings"


# ============================================================
# Flask app setup
# ============================================================
app = Flask(__name__)
CORS(app)


# ============================================================
# Shared backend state
# ============================================================
start_time = time.time()

current_mode = "Study"

thresholds = {
    "Study": 50,
    "Normal": 70,
    "Event": 85,
}


def format_uptime():
    """
    Return backend API uptime as a readable string.
    """

    elapsed_seconds = int(time.time() - start_time)

    hours = elapsed_seconds // 3600
    minutes = (elapsed_seconds % 3600) // 60
    seconds = elapsed_seconds % 60

    return f"{hours}h {minutes}m {seconds}s"


# ============================================================
# MQTT callback functions
# ============================================================
def on_connect(client, userdata, flags, rc):
    """
    Subscribe to the sensor reading topic after connecting to the MQTT broker.
    """

    if rc == 0:
        print("Connected to MQTT Broker")
        client.subscribe(TOPIC)
        print(f"Subscribed to topic: {TOPIC}")
    else:
        print(f"Failed to connect to MQTT Broker. Return code: {rc}")


def on_message(client, userdata, msg):
    """
    Receive MQTT messages, evaluate noise status, and store readings in SQLite.
    """

    global current_mode

    print("Message received")

    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        print("Invalid JSON payload received")
        return

    print(payload)

    avg_db = payload.get("avg_db", payload.get("estimated_db", 0))

    # The selected mode is controlled by the frontend through /api/mode.
    # If the sensor payload contains a mode, we still prefer the current backend mode
    # because this is the central system state used by the dashboard.
    mode = current_mode
    threshold = thresholds[mode]

    calculated_status = evaluate_noise(
        avg_db=avg_db,
        mode=mode
    )

    print("Current mode:", mode)
    print("Calculated status:", calculated_status)

    insert_reading(
        avg_db=avg_db,
        peak_db=payload.get("peak_db", avg_db),
        status=calculated_status,
        event_type=payload.get("event_type", "NONE"),
        mode=mode,
        event_marker=payload.get("event_marker",
                                 payload.get("green_button") == "EVENT"),
        muted=payload.get("muted",
                           payload.get("red_button") == "MUTE"),
        timestamp=payload["timestamp"],
        device_id=payload.get("device_id"),
        device_ip=payload.get("device_ip"),
        location=payload.get("location"),
        threshold_db=threshold,
        buzzer=payload.get("buzzer")
    )


def start_mqtt_subscriber():
    """
    Start the MQTT subscriber in a background thread.
    """

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, 60)
    client.loop_forever()


# ============================================================
# API endpoints
# ============================================================
@app.route("/health", methods=["GET"])
def health_check():
    """
    Simple endpoint to check whether the backend API is running.
    """

    return jsonify({
        "status": "backend running",
        "mqtt_topic": TOPIC,
        "mode": current_mode,
        "uptime": format_uptime()
    })


@app.route("/api/live", methods=["GET"])
def api_live():
    """
    Return the latest noise reading in the format expected by the frontend dashboard.
    """

    row = get_latest_reading()
    threshold = thresholds[current_mode]

    if row is None:
        return jsonify({
            "db": None,
            "status": "NO_DATA",
            "mode": current_mode,
            "threshold": threshold,
            "alert": False,
            "event": False,
            "mute": False,
            "buzzer": False,
            "timestamp": None,
            "device_id": None,
            "device_ip": None,
            "location": None,
            "uptime": format_uptime(),
            "data_source": "No data available"
        })

    db_value = row[1]
    status = row[3]
    mode = row[4] if row[4] is not None else current_mode
    threshold = thresholds.get(mode, thresholds[current_mode])
    buzzer_state = row[12]

    return jsonify({
        "db": db_value,
        "status": status,
        "mode": mode,
        "threshold": threshold,
        "alert": status == "ALERT",
        "event": bool(row[5]),
        "mute": bool(row[6]),
        "buzzer": buzzer_state == "BEEP" or status == "ALERT",
        "timestamp": row[7],
        "device_id": row[8],
        "device_ip": row[9],
        "location": row[10],
        "uptime": format_uptime(),
        "data_source": "Raspberry Pi via SQLite"
    })


@app.route("/api/mode", methods=["POST"])
def api_mode():
    """
    Update the current frontend dashboard mode.
    """

    global current_mode

    request_data = request.get_json()

    if request_data is None or "mode" not in request_data:
        return jsonify({
            "success": False,
            "message": "Missing mode"
        }), 400

    mode = request_data["mode"]

    if mode not in thresholds:
        return jsonify({
            "success": False,
            "message": "Invalid mode"
        }), 400

    current_mode = mode

    return jsonify({
        "success": True,
        "mode": current_mode,
        "threshold": thresholds[current_mode]
    })


@app.route("/latest", methods=["GET"])
def latest_reading():
    """
    Return the latest noise reading from the SQLite database.
    """

    row = get_latest_reading()

    if row is None:
        return jsonify({
            "message": "No data found"
        })

    data = {
        "id": row[0],
        "avg_db": row[1],
        "peak_db": row[2],
        "status": row[3],
        "mode": row[4],
        "event_marker": bool(row[5]),
        "muted": bool(row[6]),
        "timestamp": row[7],
        "device_id": row[8],
        "device_ip": row[9],
        "location": row[10],
        "threshold_db": row[11],
        "buzzer": row[12]
    }

    return jsonify(data)


@app.route("/history", methods=["GET"])
def reading_history():
    """
    Return the latest noise readings from the SQLite database.
    """

    rows = get_latest_readings(limit=20)

    history = []

    for row in rows:
        history.append({
            "id": row[0],
            "avg_db": row[1],
            "peak_db": row[2],
            "status": row[3],
            "mode": row[4],
            "event_marker": bool(row[5]),
            "muted": bool(row[6]),
            "timestamp": row[7],
            "device_id": row[8],
            "device_ip": row[9],
            "location": row[10],
            "threshold_db": row[11],
            "buzzer": row[12]
        })

    return jsonify(history)


@app.route("/forecast", methods=["GET"])
def forecast_reading():
    """
    Return a simple moving-average forecast based on recent readings.
    """

    rows = get_latest_readings(limit=20)
    forecast_result = generate_forecast(rows)

    return jsonify(forecast_result)

@app.route("/api/events", methods=["GET"])
def api_events():

    rows = get_latest_readings(limit=50)

    important = []

    for row in rows:

        event_type = row[13] if len(row) > 13 else None

        if event_type in [
            "ALERT",
            "MUTED",
            "MANUAL_ALERT"
        ]:

            important.append({
                "timestamp": row[7],
                "db": row[1],
                "status": row[3],
                "event_type": event_type
            })

    return jsonify(important)


# ============================================================
# Main entry point
# ============================================================
if __name__ == "__main__":
    init_db()

    mqtt_thread = threading.Thread(target=start_mqtt_subscriber, daemon=True)
    mqtt_thread.start()

    print("Smart Noise Monitor backend started.")
    print("MQTT subscriber running in background.")
    print("Flask API running on http://127.0.0.1:5000")

    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)