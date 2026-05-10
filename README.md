# SmartNoise Monitor

> **Real-time IoT noise pollution monitoring for urban environments**  
> CITS5506 Internet of Things — Group 18 | University of Western Australia

## Overview

**SmartNoise Monitor** is a low-cost IoT noise monitoring system that captures, processes, and visualises ambient noise levels in real time.

The system uses a **Raspberry Pi 3B+** with a **USB microphone** to collect live sound data. The Raspberry Pi estimates the current noise level in decibels, publishes the readings through **MQTT**, and sends them to a **Flask-based dashboard** for real-time display.

The project also includes interactive components such as:

- A green button for manual event marking
- A red button for mute / alert acknowledgement
- A buzzer alert when the noise level exceeds the threshold
- A web dashboard with mode selection for different environments

The current working integration supports the following real-time data flow:

```text
Raspberry Pi USB microphone
→ Raspberry Pi noise monitoring script
→ Mosquitto MQTT broker
→ smart_noise/readings MQTT topic
→ Flask backend MQTT subscriber
→ /api/live REST API
→ Web dashboard real-time display
```

---

## Features

- Real-time dB monitoring from a Raspberry Pi USB microphone
- MQTT publishing from Raspberry Pi to `smart_noise/readings`
- Flask backend subscribing to live MQTT data
- `/api/live` endpoint returning the latest Raspberry Pi reading
- Web dashboard displaying live noise levels
- Interactive mode selection: Study / Normal / Event
- Dynamic threshold checking based on selected mode
- Alert status when the live dB value exceeds the threshold
- Green button for manual event marker
- Red button for mute / alert acknowledgement
- Buzzer feedback when alert status is triggered
- Local Raspberry Pi terminal output for live monitoring and debugging
- Integration testing notes included in `INTEGRATION_TESTING.md`

---

## System Architecture

```text
┌─────────────────────────────────────────────┐
│              SENSOR NODE                     │
│                                              │
│  [USB Microphone]                            │
│       │                                      │
│       ▼                                      │
│  [Raspberry Pi 3B+]                          │
│   ├── Audio sampling                         │
│   ├── dB estimation                          │
│   ├── Green Button → EVENT marker            │
│   ├── Red Button   → MUTE / acknowledge      │
│   ├── Buzzer       → ALERT feedback          │
│   └── MQTT publish → smart_noise/readings    │
└─────────────────────┬───────────────────────┘
                      │ Wi-Fi / MQTT
                      ▼
             ┌────────────────┐
             │  MQTT Broker   │
             │  Mosquitto     │
             └───────┬────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │     Flask Backend      │
        │  ├── MQTT subscriber   │
        │  ├── Latest data store │
        │  ├── Mode threshold    │
        │  └── /api/live API     │
        └───────────┬────────────┘
                    │
                    ▼
        ┌────────────────────────┐
        │    Web Dashboard       │
        │  ├── Live dB display   │
        │  ├── Status display    │
        │  ├── Mode selection UI │
        │  └── Alert indication  │
        └────────────────────────┘
```

---

## Hardware

| Component | Model / Type | Purpose |
|---|---|---|
| Microcontroller | Raspberry Pi 3B+ | Main edge processing device |
| Microphone | USB Microphone | Ambient sound capture |
| Button | Green Button | Manual event marker |
| Button | Red Button | Mute / alert acknowledgement |
| Buzzer | Piezo Buzzer | Audio feedback when alert is triggered |
| Network | Wi-Fi / Hotspot | Communication between Raspberry Pi and laptop |
| Laptop | macOS laptop | Runs Flask dashboard during local testing |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Edge Processing | Python 3 |
| Communication | MQTT, Mosquitto, paho-mqtt |
| Backend | Flask, Python |
| Dashboard | Flask templates, HTML, CSS, JavaScript |
| API | REST endpoint `/api/live` |
| Remote Access | SSH |
| Version Control | Git, GitHub |

---

## Project Structure

```text
Smart_Noise_Monitor/
│
├── app.py                         # Flask dashboard backend and MQTT subscriber
├── README.md                      # Project documentation
├── INTEGRATION_TESTING.md         # Integration testing notes
│
├── templates/
│   └── dashboard.html             # Web dashboard page
│
├── static/
│   └── ...                        # Frontend static files
│
└── raspberry_pi/
    ├── smart_noise_mvp.py         # Raspberry Pi noise monitoring script
    ├── requirements.txt           # Raspberry Pi dependencies
    └── backend/                   # Raspberry Pi backend-related files
```

---

## Getting Started

### Prerequisites

Before running the project, make sure the following requirements are met:

- Raspberry Pi 3B+ is powered on
- Raspberry Pi and laptop are connected to the same Wi-Fi / hotspot
- USB microphone is connected to the Raspberry Pi
- Mosquitto MQTT broker is installed and running on the Raspberry Pi
- Python 3 is installed on both Raspberry Pi and laptop
- Flask and paho-mqtt are installed in the laptop virtual environment

---

## 1. Clone the Repository

On the laptop:

```bash
git clone https://github.com/Aksa-23/Smart_Noise_Monitor.git
cd Smart_Noise_Monitor
```

---

## 2. Set Up the Flask Environment on the Laptop

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install required Python packages:

```bash
pip install flask paho-mqtt
```

---

## 3. Connect to the Raspberry Pi

SSH into the Raspberry Pi:

```bash
ssh csseiot@172.20.10.2
```

Both the laptop and Raspberry Pi must be connected to the same network.

---

## 4. Start the Raspberry Pi Noise Monitoring Script

On the Raspberry Pi:

```bash
cd /home/csseiot
python3 smart_noise_mvp.py
```

If the script is running correctly, the terminal should show output similar to:

```text
MQTT connected: localhost:1883
Publishing to topic: smart_noise/readings
Smart Noise Monitor MVP started.
Hardware included: USB mic, OLED, green button, red button, buzzer
MQTT publishing enabled if broker is running.
Green button = manual event marker
Red button = mute / acknowledge alert
Buzzer = beeps when status is ALERT
Press Ctrl + C to stop.
dB: 38.64 | Status: NORMAL | Green: NONE | Red: NONE | Buzzer: OFF | MQTT: OK
```

Keep this terminal running while using the dashboard.

---

## 5. Start the Flask Dashboard on the Laptop

Open a new terminal on the laptop:

```bash
cd ~/Desktop/Smart_Noise_Monitor
source venv/bin/activate
python app.py
```

If the Flask backend successfully connects to the Raspberry Pi MQTT broker, the terminal should show:

```text
Connected to Raspberry Pi MQTT broker
Subscribed to topic: smart_noise/readings
Received MQTT data: 38.64 dB | Status: NORMAL
```

---

## 6. Open the Dashboard

Open the following URL in a browser:

```text
http://127.0.0.1:5000
```

The dashboard should display real-time noise readings from the Raspberry Pi.

---

## 7. Test the Live API

To verify that Flask is receiving live Raspberry Pi MQTT data, run:

```bash
curl http://127.0.0.1:5000/api/live
```

Example response:

```json
{
  "alert": false,
  "buzzer": false,
  "data_source": "Raspberry Pi MQTT",
  "db": 38.64,
  "device_id": "rpi-008",
  "device_ip": "127.0.1.1",
  "event": false,
  "location": "Sheltered campus area",
  "mode": "Study",
  "mute": false,
  "status": "NORMAL",
  "threshold": 50,
  "timestamp": "2026-05-10T14:48:20",
  "uptime": "Live"
}
```

If `"data_source"` is `"Raspberry Pi MQTT"`, the Flask backend is receiving live data from the Raspberry Pi.

---

## MQTT Configuration

The Flask backend connects to the Raspberry Pi MQTT broker using:

```python
MQTT_BROKER = "172.20.10.2"
MQTT_PORT = 1883
MQTT_TOPIC = "smart_noise/readings"
```

The Raspberry Pi Mosquitto broker must allow external connections from the laptop.

During local testing, Mosquitto was configured with:

```conf
listener 1883 0.0.0.0
allow_anonymous true
```

After changing Mosquitto configuration, restart the broker:

```bash
sudo systemctl restart mosquitto
```

Check broker status:

```bash
sudo systemctl status mosquitto
```

The expected status is:

```text
Active: active (running)
```

---

## MQTT Payload Format

The Raspberry Pi publishes live noise readings to the MQTT topic:

```text
smart_noise/readings
```

The current payload format is:

```json
{
  "timestamp": "2026-05-10T14:25:15",
  "device_id": "rpi-008",
  "device_ip": "127.0.1.1",
  "location": "Sheltered campus area",
  "estimated_db": 39.14,
  "threshold_db": 70,
  "status": "NORMAL",
  "green_button": "NONE",
  "red_button": "NONE",
  "buzzer": "OFF"
}
```

### Payload Fields

| Field | Meaning |
|---|---|
| `timestamp` | Time when the reading was generated |
| `device_id` | Raspberry Pi device identifier |
| `device_ip` | IP address reported by the Raspberry Pi |
| `location` | Monitoring location |
| `estimated_db` | Estimated live noise level in dB |
| `threshold_db` | Threshold used by the Raspberry Pi script |
| `status` | Current noise status, such as `NORMAL` or `ALERT` |
| `green_button` | Manual event marker button state |
| `red_button` | Mute / alert acknowledgement button state |
| `buzzer` | Buzzer state, such as `OFF` or `BEEP` |

---

## Flask API Format

The Flask backend converts the Raspberry Pi MQTT payload into the dashboard API format.

The dashboard reads from:

```text
/api/live
```

The API response format is:

```json
{
  "db": 38.64,
  "status": "NORMAL",
  "mode": "Study",
  "threshold": 50,
  "alert": false,
  "event": false,
  "mute": false,
  "buzzer": false,
  "timestamp": "2026-05-10T14:48:20",
  "device_id": "rpi-008",
  "device_ip": "127.0.1.1",
  "location": "Sheltered campus area",
  "uptime": "Live",
  "data_source": "Raspberry Pi MQTT"
}
```

---

## Interaction Modes

The dashboard supports three monitoring modes. Each mode uses a different alert threshold.

| Mode | Threshold | Use Case |
|---|---:|---|
| Study | 50 dB | Library / study rooms |
| Normal | 70 dB | Standard campus outdoor areas |
| Event | 85 dB | Outdoor events / gatherings |

When the live dB value is greater than or equal to the selected threshold, the system status changes to:

```text
ALERT
```

Otherwise, the status remains:

```text
NORMAL
```

---

## Mode Switching API

The selected mode can be updated through the dashboard or by sending a POST request.

Example:

```bash
curl -X POST http://127.0.0.1:5000/api/mode \
-H "Content-Type: application/json" \
-d '{"mode":"Normal"}'
```

Expected response:

```json
{
  "success": true,
  "mode": "Normal",
  "threshold": 70
}
```

Invalid mode example:

```bash
curl -X POST http://127.0.0.1:5000/api/mode \
-H "Content-Type: application/json" \
-d '{"mode":"Wrong"}'
```

Expected response:

```json
{
  "success": false
}
```

---

## Real-Time Integration Testing

The real-time Raspberry Pi integration has been tested using the following data flow:

```text
Raspberry Pi USB microphone
→ Raspberry Pi noise monitoring script
→ Mosquitto MQTT broker
→ smart_noise/readings MQTT topic
→ Flask backend MQTT subscriber
→ /api/live REST API
→ Web dashboard real-time display
```

### Tested Items

- Raspberry Pi successfully publishes live dB readings through MQTT.
- Flask backend connects to the Raspberry Pi MQTT broker.
- Flask subscribes to the `smart_noise/readings` topic.
- `/api/live` returns real Raspberry Pi MQTT data.
- Dashboard displays real-time dB readings.
- Mode thresholds can be changed through `/api/mode`.
- Alert status updates when the live dB value exceeds the selected threshold.

### Example Flask Log

```text
Connected to Raspberry Pi MQTT broker
Subscribed to topic: smart_noise/readings
Received MQTT data: 38.64 dB | Status: NORMAL
```

### Example Raspberry Pi Log

```text
dB: 73.06 | Status: ALERT | Green: NONE | Red: NONE | Buzzer: BEEP | MQTT: OK
```

---

## Troubleshooting

### 1. Flask shows `MQTT connection error: [Errno 61] Connection refused`

This usually means the laptop cannot connect to the Raspberry Pi MQTT broker.

Check that Mosquitto is running on the Raspberry Pi:

```bash
sudo systemctl status mosquitto
```

If it is not running, restart it:

```bash
sudo systemctl restart mosquitto
```

Also check that Mosquitto allows external connections:

```conf
listener 1883 0.0.0.0
allow_anonymous true
```

---

### 2. Dashboard shows no live updates

Check the Raspberry Pi script is still running:

```bash
python3 smart_noise_mvp.py
```

Check Flask is receiving MQTT data:

```text
Received MQTT data: ... dB | Status: NORMAL
```

Check the live API:

```bash
curl http://127.0.0.1:5000/api/live
```

---

### 3. SSH does not connect to Raspberry Pi

Make sure both devices are on the same Wi-Fi or hotspot.

Check the Raspberry Pi IP address:

```bash
hostname -I
```

Then connect using:

```bash
ssh csseiot@<raspberry-pi-ip>
```

---

### 4. Flask receives duplicate MQTT messages

Flask debug mode can start the reloader and create duplicate MQTT subscriptions.

The project uses:

```python
app.run(debug=True, port=5000, use_reloader=False)
```

This prevents duplicate MQTT subscriptions during local testing.

---

## Team

| Name | Student ID |
|---|---|
| Aksa Benny | 24505099 |
| Shouvik Barua Pratik | 23869695 |
| Wenmin Luo | 24489475 |
| Xu Li | 24269773 |

---

## Acknowledgements

- Raspberry Pi Foundation
- Eclipse Mosquitto
- UWA CSSE Lab
- University of Western Australia
- CITS5506 Internet of Things teaching team

---

*University of Western Australia — CITS5506 Internet of Things — Semester 1, 2026*