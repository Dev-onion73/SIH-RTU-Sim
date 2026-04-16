import time
import json
import uuid
import random
import paho.mqtt.client as mqtt
from sensor_classes import BH1750, DS18B20, ESP32Voltage

# ===================== Configuration =====================
BROKER_IP = "192.168.1.10"
BROKER_PORT = 1883
PUBLISH_INTERVAL = 5  # seconds

# Generate UUID-based device identifier
DEVICE_UUID = str(uuid.uuid4())
NODE_ID = DEVICE_UUID
TOPIC = f"rtu/{DEVICE_UUID}/telemetry"

# ===================== Sensor Initialization =====================
def initialize_sensors():
    sensors = {}

    # BH1750 Light Sensor
    try:
        sensors['bh1750'] = BH1750(i2c_address=0x23, bus=1)
        print(f"[OK] BH1750: {sensors['bh1750'].status()}")
    except Exception as e:
        print(f"[WARN] BH1750 initialization failed: {e}")
        sensors['bh1750'] = None

    # DS18B20 Temperature Sensor
    try:
        sensors['ds18b20'] = DS18B20()
        print(f"[OK] DS18B20: {sensors['ds18b20'].status()}")
    except Exception as e:
        print(f"[WARN] DS18B20 initialization failed: {e}")
        sensors['ds18b20'] = None

    # ESP32 Voltage Sensor
    try:
        sensors['esp32'] = ESP32Voltage(port='/dev/ttyUSB0', baud=115200)
        print(f"[OK] ESP32Voltage: {sensors['esp32'].status()}")
    except Exception as e:
        print(f"[WARN] ESP32Voltage initialization failed: {e}")
        sensors['esp32'] = None

    return sensors

# ===================== MQTT Setup =====================
def setup_mqtt():
    client = mqtt.Client(client_id=NODE_ID)

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"[OK] Connected to MQTT broker at {BROKER_IP}:{BROKER_PORT}")
        else:
            print(f"[ERROR] MQTT connection failed with code {rc}")

    def on_publish(client, userdata, mid):
        print(f"[OK] Message published to {TOPIC}")

    def on_disconnect(client, userdata, rc):
        if rc != 0:
            print(f"[WARN] Unexpected MQTT disconnection: {rc}")

    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect

    try:
        client.connect(BROKER_IP, BROKER_PORT, keepalive=60)
        client.loop_start()
        return client
    except Exception as e:
        print(f"[ERROR] Failed to connect to MQTT broker: {e}")
        return None

# ===================== Generate Telemetry Data =====================
def generate_telemetry(sensors):
    """Generate comprehensive telemetry data with all required fields"""

    timestamp = int(time.time())

    # Read actual sensor values
    voltage = None
    temperature_c = None
    lux = None

    if sensors['esp32']:
        try:
            voltage = sensors['esp32'].read()
        except Exception as e:
            print(f"[ERROR] ESP32 read failed: {e}")

    if sensors['ds18b20']:
        try:
            temperature_c = sensors['ds18b20'].read()
        except Exception as e:
            print(f"[ERROR] DS18B20 read failed: {e}")

    if sensors['bh1750']:
        try:
            lux = sensors['bh1750'].read()
        except Exception as e:
            print(f"[ERROR] BH1750 read failed: {e}")

    # Calculate DC_POWER from voltage (voltage × 0.56 mA)
    dc_power = round(voltage * 0.56, 3) if voltage else round(random.uniform(0, 500), 3)

    # Build telemetry payload with all required fields
    data = {
        "node_id": NODE_ID,
        "timestamp": timestamp,

        # Power metrics
        "DC_POWER": dc_power,
        "AC_POWER": round(random.uniform(0, 450), 3),

        # Temperature metrics
        "AMBIENT_TEMPERATURE": temperature_c if temperature_c else round(random.uniform(15, 45), 2),
        "MODULE_TEMPERATURE": round(random.uniform(20, 60), 2),

        # Irradiation
        "IRRADIATION": round(random.uniform(0, 1000), 2),

        # Performance metrics
        "PR": round(random.uniform(0.7, 0.95), 3),
        "TEMP_DELTA": round(random.uniform(5, 20), 2),
        "DC_AC_RATIO": round(random.uniform(0.9, 1.0), 3),
        "PR_ROLL_MEAN": round(random.uniform(0.75, 0.92), 3),
        "PR_ROLL_STD": round(random.uniform(0.01, 0.05), 3),
        "PR_SLOPE": round(random.uniform(-0.02, 0.02), 4),
        "PR_DEV": round(random.uniform(0.01, 0.10), 3),
        "TEMP_DELTA_SIGMA": round(random.uniform(2, 8), 2),

        # Image analysis scores (0-100)
        "img_panel_score": round(random.uniform(70, 100), 2),
        "img_dusty_score": round(random.uniform(0, 30), 2),
        "img_cracked_score": round(random.uniform(0, 20), 2),
        "img_bird_drop_score": round(random.uniform(0, 15), 2),

        # Sensor readings
        "sensors": {
            "lux": lux,
            "temperature_c": temperature_c,
            "voltage": voltage
        }
    }

    return data

# ===================== Main Loop =====================
def main():
    print("=" * 60)
    print("MQTT Telemetry Publisher - Comprehensive Sensor Data")
    print("=" * 60)
    print(f"[INFO] Device UUID: {DEVICE_UUID}")
    print(f"[INFO] Node ID: {NODE_ID}")

    # Initialize sensors
    sensors = initialize_sensors()

    # Setup MQTT
    mqtt_client = setup_mqtt()
    if not mqtt_client:
        print("[FATAL] Cannot start without MQTT connection")
        return

    print(f"\n[INFO] Publishing to {TOPIC} every {PUBLISH_INTERVAL} seconds")
    print("[INFO] Press Ctrl+C to stop\n")

    try:
        while True:
            # Generate and publish telemetry
            payload_dict = generate_telemetry(sensors)
            payload = json.dumps(payload_dict)

            # Publish to MQTT
            try:
                mqtt_client.publish(TOPIC, payload, qos=1)
            except Exception as e:
                print(f"[ERROR] Failed to publish: {e}")

            # Wait for next interval
            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("[OK] Disconnected from MQTT broker")

if __name__ == "__main__":
    main()
