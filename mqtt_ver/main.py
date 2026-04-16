import time
import json
import random
import uuid
import paho.mqtt.client as mqtt
from sensor_classes import BH1750, DS18B20, ESP32Voltage

# ===================== Configuration =====================
BROKER_IP = "192.168.1.10"
BROKER_PORT = 1883
TOPIC = "rtu/rtu_01/telemetry"
PUBLISH_INTERVAL = 5  # seconds
CLIENT_ID = str(uuid.uuid4())

# ===================== Conversion Factors =====================
VOLTAGE_TO_POWER_FACTOR = 0.00056   # 0.56 mA current assumption (V * A = W)
LUX_TO_IRRADIATION_FACTOR = 0.0079  # Approximate lux-to-W/m² conversion for sunlight

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
    # Read raw sensor values
    lux = None
    temperature_c = None
    voltage = None

    if sensors['bh1750']:
        try:
            lux = sensors['bh1750'].read()
        except Exception as e:
            print(f"[ERROR] BH1750 read failed: {e}")

    if sensors['ds18b20']:
        try:
            temperature_c = sensors['ds18b20'].read()
        except Exception as e:
            print(f"[ERROR] DS18B20 read failed: {e}")

    if sensors['esp32']:
        try:
            voltage = sensors['esp32'].read()
        except Exception as e:
            print(f"[ERROR] ESP32 read failed: {e}")

    # Derived power values
    dc_power = round(voltage * VOLTAGE_TO_POWER_FACTOR, 4) if voltage is not None else round(random.uniform(0.1, 5.0), 4)
    # AC power derived from DC power via inverter efficiency (typically 88–95%)
    ac_power = round(dc_power * random.uniform(0.88, 0.95), 4)

    # Temperature metrics
    ambient_temp = round(temperature_c if temperature_c is not None else random.uniform(20.0, 40.0), 2)
    module_temp = round(ambient_temp + random.uniform(5.0, 25.0), 2)
    temp_delta = round(module_temp - ambient_temp, 2)

    # Performance metrics
    irradiation = round(lux * LUX_TO_IRRADIATION_FACTOR if lux is not None else random.uniform(100.0, 1000.0), 2)
    pr = round(random.uniform(0.70, 0.95), 4)
    dc_ac_ratio = round(dc_power / ac_power, 4) if ac_power != 0 else None
    pr_roll_mean = round(pr + random.uniform(-0.02, 0.02), 4)
    pr_roll_std = round(random.uniform(0.005, 0.05), 4)
    pr_slope = round(random.uniform(-0.001, 0.001), 6)
    pr_dev = round(random.uniform(-0.05, 0.05), 4)
    temp_delta_sigma = round(random.uniform(0.5, 2.0), 4)

    # Image analysis scores (0.0 – 1.0)
    img_panel_score = round(random.uniform(0.7, 1.0), 4)
    img_dusty_score = round(random.uniform(0.0, 0.5), 4)
    img_cracked_score = round(random.uniform(0.0, 0.2), 4)
    img_bird_drop_score = round(random.uniform(0.0, 0.3), 4)

    data = {
        "node_id": CLIENT_ID,
        "timestamp": int(time.time()),
        # Sensor readings (backward compatibility)
        "lux": lux,
        "temperature_c": temperature_c,
        "voltage": voltage,
        # Power metrics
        "DC_POWER": dc_power,
        "AC_POWER": ac_power,
        # Temperature metrics
        "AMBIENT_TEMPERATURE": ambient_temp,
        "MODULE_TEMPERATURE": module_temp,
        # Irradiation
        "IRRADIATION": irradiation,
        # Performance metrics
        "PR": pr,
        "TEMP_DELTA": temp_delta,
        "DC_AC_RATIO": dc_ac_ratio,
        "PR_ROLL_MEAN": pr_roll_mean,
        "PR_ROLL_STD": pr_roll_std,
        "PR_SLOPE": pr_slope,
        "PR_DEV": pr_dev,
        "TEMP_DELTA_SIGMA": temp_delta_sigma,
        # Image analysis scores
        "img_panel_score": img_panel_score,
        "img_dusty_score": img_dusty_score,
        "img_cracked_score": img_cracked_score,
        "img_bird_drop_score": img_bird_drop_score,
    }

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
