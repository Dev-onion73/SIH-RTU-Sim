import time
import json
import os
import math
import random
import RPi.GPIO as GPIO
from pymodbus.client.sync import ModbusTcpClient

# -------------------
# GPIO Setup for LDR
# -------------------
LDR_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(LDR_PIN, GPIO.IN)

# -------------------
# JSON log file
# -------------------
LOG_FILE = "sensor_log.json"

def append_log(entry):
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    data.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=4)

# -------------------
# Master polling config
# -------------------
SLAVE_IP = "192.168.0.10"  # Replace with your slave IP
SLAVE_PORT = 1502
UNIT_ID = 1
POLL_INTERVAL = 1  # seconds

# -------------------
# Energy calculation
# -------------------
total_energy_wh = 0
last_time = time.time()

# -------------------
# Connect to Modbus TCP slave
# -------------------
client = ModbusTcpClient(SLAVE_IP, port=SLAVE_PORT)
if not client.connect():
    print("❌ Could not connect to slave")
    exit(1)
print("✅ Connected to Modbus TCP slave")

try:
    while True:
        rr = client.read_holding_registers(0, 4, unit=UNIT_ID)
        if rr.isError():
            print(f"Error reading registers: {rr}")
            time.sleep(POLL_INTERVAL)
            continue

        voltage, current, power, status = rr.registers

        # Derived metrics
        now = time.time()
        delta_hours = (now - last_time) / 3600
        last_time = now
        total_energy_wh += power * delta_hours
        total_energy_kwh = round(total_energy_wh / 1000, 4)

        # Apparent Power S
        S = voltage * current
        # Reactive Power Q
        if S >= power:
            Q = round(math.sqrt(S**2 - power**2), 2)
        else:
            Q = 0
        # Power Factor PF
        PF = round(power / S if S != 0 else 0, 3)

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Log inverter metrics as COSEM objects
        metrics = [
            ("1-0:32.7.0", "Voltage", voltage),
            ("1-0:31.7.0", "Current", current),
            ("1-0:21.7.0", "ActivePower", power),
            ("1-0:22.7.0", "ApparentPower", S),
            ("1-0:23.7.0", "ReactivePower", Q),
            ("1-0:25.7.0", "PowerFactor", PF),
            ("0-0:96.7.9", "Status", status),
            ("1-0:1.8.0", "Energy", total_energy_kwh)
        ]
        for obis, metric, value in metrics:
            entry = {
                "timestamp": timestamp,
                "obis_code": obis,
                "sensor": "Inverter",
                "metric": metric,
                "value": value
            }
            append_log(entry)
            print(f"[Inverter] {metric}: {value}")

        # LDR reading
        ldr_state = "Bright" if GPIO.input(LDR_PIN) == 0 else "Dark"
        ldr_entry = {
            "timestamp": timestamp,
            "obis_code": "1-0:99.99.1",
            "sensor": "LDR",
            "value": ldr_state
        }
        append_log(ldr_entry)
        print(f"[LDR] {ldr_state}")

        time.sleep(POLL_INTERVAL)

except KeyboardInterrupt:
    print("Stopping master...")
finally:
    client.close()
    GPIO.cleanup()
