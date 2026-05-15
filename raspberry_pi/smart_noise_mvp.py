import subprocess
import math
import time
import smbus
import json
import socket
import numpy as np
import paho.mqtt.client as mqtt
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from gpiozero import Button, Buzzer

# ============================================================
# SMART NOISE MONITOR MVP + MQTT
#
# Hardware:
# - USB microphone
# - PiicoDev OLED SSD1306
# - Green button = manual event marker
# - Red button = mute / acknowledge alert
# - 5V buzzer connected directly as advised by lab facilitator
# - MQTT publishes JSON readings to smart_noise/readings
# - MQTT subscribes to smart_noise/mode for dashboard mode changes
# ============================================================


# -----------------------------
# Microphone settings
# -----------------------------
MIC_DEVICE = "plughw:2,0"   # USB microphone from arecord -l
SAMPLE_RATE = 16000
DURATION = 1                # seconds per audio sample


# -----------------------------
# OLED settings
# -----------------------------
OLED_ADDR = 0x3D            # OLED address from i2cdetect -y 1
I2C_BUS = 1
WIDTH = 128
HEIGHT = 64


# -----------------------------
# GPIO settings
# Use the printed GPIO labels on the Pi case
# -----------------------------
GREEN_BUTTON_GPIO = 17      # Green button: GPIO17 + ground symbol
RED_BUTTON_GPIO = 27        # Red button: GPIO27 + ground symbol
BUZZER_GPIO = 22            # Buzzer + to GPIO22, buzzer - to ground symbol


# -----------------------------
# Noise logic settings
# -----------------------------
current_mode = "Study"

THRESHOLDS = {
    "Study": 50,
    "Normal": 70,
    "Event": 85
}

CALIBRATION_OFFSET = 90     # Keep this if quiet room reads around 35-45 dB
MUTE_SECONDS = 10           # Red button mutes alert buzzer for 10 seconds


# -----------------------------
# MQTT settings
# -----------------------------
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_READING_TOPIC = "smart_noise/readings"
MQTT_MODE_TOPIC = "smart_noise/mode"

LOCATION = "Sheltered campus area"


# -----------------------------
# Hardware setup
# -----------------------------
bus = smbus.SMBus(I2C_BUS)

green_button = Button(GREEN_BUTTON_GPIO, pull_up=True, bounce_time=0.1)
red_button = Button(RED_BUTTON_GPIO, pull_up=True, bounce_time=0.1)
buzzer = Buzzer(BUZZER_GPIO)

muted_until = 0


# ============================================================
# MQTT FUNCTIONS
# ============================================================

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"MQTT connected: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"Publishing to topic: {MQTT_READING_TOPIC}")

        client.subscribe(MQTT_MODE_TOPIC)
        print(f"Subscribed to mode topic: {MQTT_MODE_TOPIC}")

    else:
        print(f"MQTT connection failed with return code: {rc}")


def on_message(client, userdata, msg):
    global current_mode

    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        mode = payload.get("mode")

        if mode in THRESHOLDS:
            current_mode = mode
            print(
                f"Mode updated from dashboard: {current_mode} | "
                f"Threshold: {THRESHOLDS[current_mode]} dB"
            )
        else:
            print(f"Invalid mode received: {mode}")

    except Exception as error:
        print(f"Failed to process mode message: {error}")


def setup_mqtt():
    try:
        client = mqtt.Client()

        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()

        return client

    except Exception as error:
        print("MQTT connection failed.")
        print(f"Reason: {error}")
        print("The local hardware MVP will still run, but MQTT messages will not publish.")
        return None


def publish_mqtt(client, payload):
    if client is None:
        return False

    try:
        client.publish(MQTT_READING_TOPIC, json.dumps(payload))
        return True

    except Exception as error:
        print(f"MQTT publish failed: {error}")
        return False


def get_device_ip():
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)

    except Exception:
        return "unknown"


# ============================================================
# OLED FUNCTIONS
# ============================================================

def command(cmd):
    bus.write_byte_data(OLED_ADDR, 0x00, cmd)


def send_data(data):
    for i in range(0, len(data), 16):
        bus.write_i2c_block_data(OLED_ADDR, 0x40, data[i:i + 16])


def init_display():
    commands = [
        0xAE,
        0xD5, 0x80,
        0xA8, 0x3F,
        0xD3, 0x00,
        0x40,
        0x8D, 0x14,
        0x20, 0x00,
        0xA1,
        0xC8,
        0xDA, 0x12,
        0x81, 0xCF,
        0xD9, 0xF1,
        0xDB, 0x40,
        0xA4,
        0xA6,
        0xAF
    ]

    for cmd in commands:
        command(cmd)


def display_image(image):
    image = image.convert("1")
    pixels = image.load()

    for page in range(HEIGHT // 8):
        command(0xB0 + page)
        command(0x00)
        command(0x10)

        page_data = []

        for x in range(WIDTH):
            byte = 0

            for bit in range(8):
                y = page * 8 + bit

                if pixels[x, y]:
                    byte |= (1 << bit)

            page_data.append(byte)

        send_data(page_data)


def show_oled(db_value, status, mode, green_state, red_state, buzzer_state, mqtt_state):
    image = Image.new("1", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    threshold = THRESHOLDS.get(mode, 70)

    draw.text((0, 0), "Smart Noise Monitor", font=font, fill=255)
    draw.text((0, 13), f"dB: {db_value} T:{threshold}", font=font, fill=255)
    draw.text((0, 26), f"{mode} | {status}", font=font, fill=255)
    draw.text((0, 39), f"G:{green_state} R:{red_state}", font=font, fill=255)
    draw.text((0, 52), f"B:{buzzer_state} M:{mqtt_state}", font=font, fill=255)

    display_image(image)


# ============================================================
# MICROPHONE FUNCTIONS
# ============================================================

def read_audio_chunk():
    cmd = [
        "arecord",
        "-D", MIC_DEVICE,
        "-f", "S16_LE",
        "-r", str(SAMPLE_RATE),
        "-c", "1",
        "-d", str(DURATION),
        "-q",
        "-t", "raw"
    ]

    raw_audio = subprocess.check_output(cmd)
    audio = np.frombuffer(raw_audio, dtype=np.int16)

    return audio


def calculate_db(audio):
    if len(audio) == 0:
        return 0.0

    rms = np.sqrt(np.mean(audio.astype(np.float64) ** 2))

    if rms <= 0:
        return 0.0

    dbfs = 20 * math.log10(rms / 32768.0)
    estimated_db = dbfs + CALIBRATION_OFFSET

    return round(estimated_db, 2)


# ============================================================
# BUZZER FUNCTION
# ============================================================

def handle_buzzer(status):
    if status in ["ALERT", "MANUAL_ALERT"]:
        buzzer.on()
        time.sleep(0.1)
        buzzer.off()
        return "BEEP"

    buzzer.off()
    return "OFF"


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():
    global muted_until

    mqtt_client = setup_mqtt()

    init_display()
    buzzer.off()

    show_oled("Ready", "START", current_mode, "NONE", "NONE", "OFF", "WAIT")

    print("Smart Noise Monitor MVP started.")
    print("Hardware included: USB mic, OLED, green button, red button, buzzer")
    print("MQTT publishing enabled if broker is running.")
    print("Green button = manual event marker")
    print("Red button = mute / acknowledge alert")
    print("Buzzer = beeps when status is ALERT")
    print("Mode-based thresholds:")
    print("Study = 50 dB")
    print("Normal = 70 dB")
    print("Event = 85 dB")
    print("Press Ctrl + C to stop.")

    try:
        while True:
            audio = read_audio_chunk()
            db_value = calculate_db(audio)
            current_time = time.time()

            # Get current threshold from current mode
            current_threshold = THRESHOLDS[current_mode]

            # Green button behaviour
            if green_button.is_pressed:
                green_state = "MANUAL_ALERT"
            else:
                green_state = "NONE"

            # Red button behaviour
            if red_button.is_pressed:
                muted_until = current_time + MUTE_SECONDS
                red_state = "MUTE"
            else:
                red_state = "NONE"

            # Status logic based on current mode threshold
            manual_alert = green_button.is_pressed

            if manual_alert:
                status = "MANUAL_ALERT"

            elif db_value >= current_threshold:
                if current_time < muted_until:
                    status = "MUTED"
                else:
                    status = "ALERT"

            else:
                status = "NORMAL"

            # Buzzer logic
            buzzer_state = handle_buzzer(status)

            # MQTT payload
            payload = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "device_id": "rpi-008",
                "device_ip": get_device_ip(),
                "location": LOCATION,
                "estimated_db": db_value,
                "mode": current_mode,
                "threshold_db": current_threshold,
                "status": status,
                "event_type": status,
                "green_button": green_state,
                "red_button": red_state,
                "buzzer": buzzer_state
            }

            mqtt_ok = publish_mqtt(mqtt_client, payload)
            mqtt_state = "OK" if mqtt_ok else "OFF"

            # OLED update
            show_oled(
                db_value,
                status,
                current_mode,
                green_state,
                red_state,
                buzzer_state,
                mqtt_state
            )

            # Terminal output
            print(
                f"dB: {db_value} | "
                f"Mode: {current_mode} | "
                f"Threshold: {current_threshold} | "
                f"Status: {status} | "
                f"Green: {green_state} | "
                f"Red: {red_state} | "
                f"Buzzer: {buzzer_state} | "
                f"MQTT: {mqtt_state}"
            )

            time.sleep(0.2)

    except KeyboardInterrupt:
        buzzer.off()
        show_oled("Stopped", "OFF", current_mode, "NONE", "NONE", "OFF", "OFF")
        print("Smart Noise Monitor stopped.")

    finally:
        buzzer.off()

        if mqtt_client is not None:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()


if __name__ == "__main__":
    main()