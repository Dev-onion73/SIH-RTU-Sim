import json
import meshtastic.serial_interface
import time

iface = meshtastic.serial_interface.SerialInterface()

# Example JSON payload
data = {
    "id": 1,
    "temperature": 26.4,
    "status": "OK"
}

# Convert JSON to string
payload = json.dumps(data)

# Send message
iface.sendText(payload)

print("Sent:", payload)

time.sleep(2)
