from flask import Flask, render_template, jsonify, request
from datetime import datetime
import json
import threading
import time
import paho.mqtt.client as mqtt

app = Flask(__name__)

# Raspberry Pi MQTT settings
MQTT_BROKER = "172.20.10.2"
MQTT_PORT = 1883
MQTT_READING_TOPIC = "smart_noise/readings"
MQTT_MODE_TOPIC = "smart_noise/mode"

current_mode = "Study"

thresholds = {
    "Study": 50,
    "Normal": 70,
    "Event": 85
}

# Hold button states for a few seconds so the dashboard does not miss short presses
BUTTON_HOLD_SECONDS = 3
mute_hold_until = 0
event_hold_until = 0

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


def is_active_button(value):
    return value not in ["NONE", None, ""]


def publish_mode_to_pi(mode):
    """
    Send the selected dashboard mode to Raspberry Pi through MQTT.
    Raspberry Pi will use this mode to decide the buzzer threshold.
    """
    mode_payload = {
        "mode": mode,
        "threshold": thresholds[mode]
    }

    try:
        mode_client = mqtt.Client()
        mode_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mode_client.publish(MQTT_MODE_TOPIC, json.dumps(mode_payload), retain=True)
        mode_client.disconnect()

        print(
            f"Published mode update: {mode} | "
            f"Threshold: {thresholds[mode]} dB"
        )

        return True

    except Exception as e:
        print(f"Failed to publish mode update: {e}")
        return False


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to Raspberry Pi MQTT broker")
        client.subscribe(MQTT_READING_TOPIC)
        print(f"Subscribed to topic: {MQTT_READING_TOPIC}")

        # Send the default mode when dashboard starts
        publish_mode_to_pi(current_mode)

    else:
        print(f"Failed to connect to MQTT broker. Return code: {rc}")


def on_message(client, userdata, msg):
    global latest_reading, mute_hold_until, event_hold_until

    try:
        payload = json.loads(msg.payload.decode("utf-8"))

        db = float(payload.get("estimated_db", 0))
        threshold = thresholds[current_mode]

        red_button = payload.get("red_button")
        green_button = payload.get("green_button")
        buzzer_state = payload.get("buzzer")
        pi_status = payload.get("status", "NORMAL")

        now = time.time()

        # If button is pressed, keep the state visible for a few seconds
        if is_active_button(red_button):
            mute_hold_until = now + BUTTON_HOLD_SECONDS

        if is_active_button(green_button) or pi_status == "MANUAL_ALERT":
            event_hold_until = now + BUTTON_HOLD_SECONDS

        mute_active = now < mute_hold_until
        event_active = now < event_hold_until

        # Preserve manual alert from Raspberry Pi.
        # Otherwise, calculate dashboard alert status using the selected mode threshold.
        if pi_status == "MANUAL_ALERT" or is_active_button(green_button):
            status = "MANUAL_ALERT"
        elif db >= threshold:
            status = "ALERT"
        else:
            status = "NORMAL"

        latest_reading = {
            "db": db,
            "status": status,
            "mode": current_mode,
            "threshold": threshold,
            "alert": status in ["ALERT", "MANUAL_ALERT"],
            "event": event_active or status == "MANUAL_ALERT",
            "mute": mute_active,
            "buzzer": buzzer_state in ["ON", "BEEP"],
            "timestamp": payload.get(
                "timestamp",
                datetime.now().strftime("%d %b %Y, %I:%M:%S %p")
            ),
            "device_id": payload.get("device_id", "rpi-008"),
            "device_ip": payload.get("device_ip", "172.20.10.2"),
            "location": payload.get("location", "Sheltered campus area"),
            "uptime": "Live",
            "data_source": "Raspberry Pi MQTT",

            # Raw values are useful for debugging
            "green_button_raw": green_button,
            "red_button_raw": red_button,
            "buzzer_raw": buzzer_state,

            # Pi-side values are useful for checking whether Pi received the mode
            "pi_status": pi_status,
            "pi_mode": payload.get("mode", "unknown"),
            "pi_threshold": payload.get("threshold_db", "unknown")
        }

        print(
            f"Received MQTT data: {db} dB | "
            f"Dashboard mode: {current_mode} | "
            f"Dashboard threshold: {threshold} | "
            f"Pi mode: {payload.get('mode', 'unknown')} | "
            f"Pi threshold: {payload.get('threshold_db', 'unknown')} | "
            f"Pi status: {pi_status} | "
            f"Dashboard status: {status} | "
            f"Red: {red_button} | "
            f"Green: {green_button} | "
            f"Buzzer: {buzzer_state}"
        )

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

    mqtt_sent = publish_mode_to_pi(current_mode)

    return jsonify({
        "success": True,
        "mode": current_mode,
        "threshold": thresholds[current_mode],
        "mqtt_sent": mqtt_sent
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000, use_reloader=False)