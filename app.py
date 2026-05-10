from flask import Flask, render_template, jsonify, request
from datetime import datetime
import json
import threading
import paho.mqtt.client as mqtt

app = Flask(__name__)

# Raspberry Pi MQTT settings
MQTT_BROKER = "172.20.10.2"
MQTT_PORT = 1883
MQTT_TOPIC = "smart_noise/readings"

current_mode = "Study"
thresholds = {
    "Study": 50,
    "Normal": 70,
    "Event": 85
}

latest_reading = {
    "db": 0,
    "status": "WAITING",
    "mode": current_mode,
    "threshold": thresholds[current_mode],
    "alert": False,
    "event": False,
    "mute": False,
    "buzzer": False,
    "timestamp": "Waiting for Raspberry Pi data",
    "device_id": "rpi-008",
    "device_ip": "172.20.10.2",
    "location": "Sheltered campus area",
    "uptime": "N/A",
    "data_source": "Raspberry Pi MQTT"
}


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to Raspberry Pi MQTT broker")
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"Failed to connect to MQTT broker. Return code: {rc}")


def on_message(client, userdata, msg):
    global latest_reading

    try:
        payload = json.loads(msg.payload.decode("utf-8"))

        db = float(payload.get("estimated_db", 0))
        threshold = thresholds[current_mode]
        status = "ALERT" if db >= threshold else "NORMAL"

        latest_reading = {
            "db": db,
            "status": status,
            "mode": current_mode,
            "threshold": threshold,
            "alert": status == "ALERT",
            "event": payload.get("green_button") == "PRESSED",
            "mute": payload.get("red_button") == "PRESSED",
            "buzzer": payload.get("buzzer") == "ON",
            "timestamp": payload.get(
                "timestamp",
                datetime.now().strftime("%d %b %Y, %I:%M:%S %p")
            ),
            "device_id": payload.get("device_id", "rpi-008"),
            "device_ip": payload.get("device_ip", "172.20.10.2"),
            "location": payload.get("location", "Sheltered campus area"),
            "uptime": "Live",
            "data_source": "Raspberry Pi MQTT"
        }

        print(f"Received MQTT data: {db} dB | Status: {status}")

    except Exception as e:
        print(f"Error processing MQTT message: {e}")


def start_mqtt_client():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"MQTT connection error: {e}")


mqtt_thread = threading.Thread(target=start_mqtt_client)
mqtt_thread.daemon = True
mqtt_thread.start()


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/live")
def api_live():
    return jsonify(latest_reading)


@app.route("/api/mode", methods=["POST"])
def api_mode():
    global current_mode

    data = request.get_json()
    mode = data.get("mode")

    if mode not in thresholds:
        return jsonify({"success": False}), 400

    current_mode = mode

    latest_reading["mode"] = current_mode
    latest_reading["threshold"] = thresholds[current_mode]

    return jsonify({
        "success": True,
        "mode": current_mode,
        "threshold": thresholds[current_mode]
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000, use_reloader=False)