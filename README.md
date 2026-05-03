# SmartNoise Monitor

> **Real-time IoT noise pollution monitoring for urban environments**  
> CITS5506 Internet of Things — Group 18 | University of Western Australia

## Overview

**SmartNoise Monitor** is a low-cost, continuously operating IoT system that captures, processes, and visualises ambient noise levels in real time. Deployed on a university campus, the system samples audio via a USB microphone on a Raspberry Pi 3B+, applies A-weighting filtering to compute accurate dB levels, and streams data via MQTT to a Flask-based web dashboard.

The system goes beyond passive monitoring — it features **physical human-computer interaction** through push-button controls and a **buzzer alert system**, alongside an **interactive mode selection dashboard** that dynamically adjusts detection thresholds based on the current environment.

---

## Features

- Real-time dB monitoring with A-weighting filter
- OLED local display showing live dB level and system status
- Green button — manual EVENT marker
- Red button — MUTE / alert acknowledgement
- Buzzer alert triggered on threshold breach
- MQTT publishing from Raspberry Pi to `smart_noise/readings`
- SQLite time-series database logging
- Flask web dashboard with live dB graph, historical heatmap, and forecast chart
- Interactive mode selection (Study / Normal / Event)
- 24-hour noise forecast model
- SSH remote access over shared Wi-Fi / hotspot
- Automated email alerts (reactive + proactive)

---

## System Architecture

```
┌─────────────────────────────────────────────┐
│              SENSOR NODE                     │
│                                              │
│  [USB Microphone]                            │
│       │                                      │
│       ▼                                      │
│  [Raspberry Pi 3B+]                          │
│   ├── pyaudio sampling                       │
│   ├── A-weighting + dB estimation            │
│   ├── Green Button → EVENT marker            │
│   ├── Red Button   → MUTE / acknowledge      │
│   ├── Buzzer       → ALERT feedback          │
│   ├── OLED Display → Live dB + status        │
│   └── MQTT publish → smart_noise/readings    │
└─────────────────────┬───────────────────────┘
                      │ Wi-Fi / MQTT
                      ▼
             ┌────────────────┐
             │  MQTT Broker   │
             │  (Mosquitto)   │
             └───────┬────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │     Python Backend     │
        │  ├── SQLite logging    │
        │  ├── Threshold detect  │
        │  ├── Alert engine      │
        │  └── Forecast model    │
        └───────────┬────────────┘
                    │
                    ▼
        ┌────────────────────────┐
        │    Flask Dashboard     │
        │  ├── Live dB graph     │
        │  ├── Historical heatmap│
        │  ├── Mode selection UI │
        │  └── Alert event log   │
        └────────────────────────┘
```

---

## Hardware

| Component | Model | Purpose |
|---|---|---|
| Microcontroller | Raspberry Pi 3B+ | Central processing unit |
| Microphone | USB Microphone | Ambient sound capture |
| Display | OLED 128x64 SSD1306 | Local real-time dB + status display |
| Button | Green SPST Momentary | Manual event marker |
| Button | Red SPST Momentary | Mute / alert acknowledgement |
| Buzzer | Piezo Buzzer 5V | Audio feedback on threshold breach |
| Breadboard | 830 Tie Point | Prototyping |
| Wires | M/F + F/F Jumper Wires | GPIO connections |
| Power | 5V Official RPi PSU | Stable power supply |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Edge Processing | Python 3, pyaudio, RPi.GPIO, scipy |
| Communication | MQTT, paho-mqtt, Mosquitto broker |
| Display | luma.oled, SSD1306 |
| Backend | Python, SQLite |
| Dashboard | Flask, Chart.js |
| Remote Access | SSH over Wi-Fi / hotspot |

---

## Getting Started

### Prerequisites
- Raspberry Pi 3B+ running Raspberry Pi OS
- Python 3.9+
- Mosquitto MQTT broker installed
- USB Microphone connected

### 1. Clone the repository
```bash
git clone https://github.com/your-org/smartnoise-monitor.git
cd smartnoise-monitor
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
# Fill in MQTT broker address, alert email credentials, and detection thresholds
```

### 4. Run the sensor node (on Raspberry Pi)
```bash
python sensor_read.py
```

### 5. Run the backend subscriber (on laptop or Pi)
```bash
python backend.py
```

### 6. Launch the dashboard
```bash
python dashboard/app.py
```

### 7. SSH into Raspberry Pi remotely
```bash
ssh pi@<raspberry-pi-ip>
# Both devices must be on the same Wi-Fi or hotspot
```

---

## MQTT Payload Format

Messages are published to topic `smart_noise/readings` in the following JSON format:

```json
{
  "avg_db": 65.2,
  "peak_db": 71.4,
  "status": "NORMAL",
  "mode": "Study",
  "event_marker": false,
  "muted": false,
  "timestamp": "2026-04-07T22:15:00"
}
```

### Status Values

| Status | Meaning |
|---|---|
| `NORMAL` | Below threshold — system nominal |
| `WARNING` | Approaching threshold |
| `ALERT` | Threshold exceeded — buzzer active |
| `MUTED` | Alert acknowledged by red button |
| `EVENT` | Manual event marked by green button |

---

## Interaction Modes

Users can select a monitoring profile via the web dashboard. Each mode dynamically adjusts the backend detection threshold in real time:

| Mode | Alert Threshold | Use Case |
|---|---|---|
| 🟢 Study Mode | 50 dB | Library, study rooms |
| 🟡 Normal Mode | 70 dB | Standard campus outdoor |
| 🔴 Event Mode | 85 dB | Outdoor events, gatherings |

---

## Project Structure

```
smartnoise-monitor/
│
├── sensor/
│   ├── sensor_read.py       # Audio sampling, dB estimation, MQTT publish
│   ├── display.py           # OLED display driver (luma.oled)
│   └── buttons.py           # GPIO button + buzzer handler
│
├── backend/
│   ├── backend.py           # MQTT subscriber + SQLite writer
│   ├── alerts.py            # Threshold detection + email alerts
│   └── forecast.py          # Moving average noise forecast model
│
├── dashboard/
│   ├── app.py               # Flask REST API
│   ├── templates/
│   │   └── dashboard.html   # Chart.js frontend
│   └── static/
│
├── tests/
│   └── test_subscriber.py   # MQTT subscriber integration test
│
├── .env.example             # Environment variable template
├── .gitignore
├── requirements.txt
└── README.md
```

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

- [Raspberry Pi Foundation](https://www.raspberrypi.org/)
- [Eclipse Mosquitto](https://mosquitto.org/)
- [Core Electronics](https://core-electronics.com.au/) — hardware supplier
- UWA CSSE Lab — hardware loan 
- City of Perth [Open Data Portal](https://data.perth.wa.gov.au/)
- WHO Environmental Noise Guidelines (2018)

---

*University of Western Australia — CITS5506 Internet of Things — Semester 1, 2026*
