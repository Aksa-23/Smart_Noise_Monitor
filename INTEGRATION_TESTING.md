# Integration Testing Notes

## Completed

The Flask dashboard has been connected to the Raspberry Pi MQTT data pipeline.

## Data Flow

Raspberry Pi USB microphone  
→ Raspberry Pi noise monitoring script  
→ Mosquitto MQTT broker  
→ `smart_noise/readings` topic  
→ Flask backend MQTT subscriber  
→ `/api/live` API  
→ Dashboard real-time display

## Tested

- Raspberry Pi publishes live dB readings through MQTT.
- Flask backend connects to the Raspberry Pi MQTT broker.
- Flask subscribes to `smart_noise/readings`.
- `/api/live` returns real Raspberry Pi MQTT data.
- Dashboard displays real-time dB values.
- Mode thresholds can be changed through `/api/mode`.
- Alert status updates when dB exceeds the selected threshold.

## Example API Response

```json
{
  "data_source": "Raspberry Pi MQTT",
  "db": 38.64,
  "status": "NORMAL",
  "mode": "Study",
  "threshold": 50,
  "timestamp": "2026-05-10T14:48:20"
}