import time
import json
import paho.mqtt.client as mqtt
from sensor_classes import BH1750, DS18B20, ESP32Voltage

# ===================== Configuration =====================
BROKER_IP = "192.168.1.10"
BROKER_PORT = 1883
TOPIC = "rtu/rtu_01/telemetry"
PUBLISH_INTERVAL = 5  # seconds
CLIENT_ID = "rtu_01"

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
    client = mqtt.Client(client_id=CLIENT_ID)
    
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

# ===================== Read Sensors =====================
def read_sensors(sensors):
    data = {
        "timestamp": int(time.time()),
        "sensors": {}
    }
    
    # Read BH1750 (Lux)
    if sensors['bh1750']:
        try:
            data['sensors']['lux'] = sensors['bh1750'].read()
        except Exception as e:
            print(f"[ERROR] BH1750 read failed: {e}")
            data['sensors']['lux'] = None
    
    # Read DS18B20 (Temperature)
    if sensors['ds18b20']:
        try:
            data['sensors']['temperature_c'] = sensors['ds18b20'].read()
        except Exception as e:
            print(f"[ERROR] DS18B20 read failed: {e}")
            data['sensors']['temperature_c'] = None
    
    # Read ESP32 (Voltage)
    if sensors['esp32']:
        try:
            data['sensors']['voltage'] = sensors['esp32'].read()
        except Exception as e:
            print(f"[ERROR] ESP32 read failed: {e}")
            data['sensors']['voltage'] = None
    
    return data

# ===================== Main Loop =====================
def main():
    print("=" * 50)
    print("MQTT Telemetry Publisher - Sensor Data")
    print("=" * 50)
    
    # Initialize sensors
    sensors = initialize_sensors()
    print(read_sensors(sensors))
    
    # Setup MQTT
    mqtt_client = setup_mqtt()
    if not mqtt_client:
        print("[FATAL] Cannot start without MQTT connection")
        return
    
    print(f"\n[INFO] Publishing to {TOPIC} every {PUBLISH_INTERVAL} seconds")
    print("[INFO] Press Ctrl+C to stop\n")
    
    try:
        while True:
            # Read all sensors
            payload_dict = read_sensors(sensors)
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
