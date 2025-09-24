import time
import math
from pymodbus.client.sync import ModbusTcpClient

# -------------------
# Master polling config (default args can be overridden)
# -------------------
DEFAULT_SLAVE_IP = "127.0.0.1"
DEFAULT_SLAVE_PORT = 1502
UNIT_ID = 1

# -------------------
# Energy calculation state
# -------------------
_total_energy_wh = 0
_last_time = time.time()

def connect_modbus(ip=DEFAULT_SLAVE_IP, port=DEFAULT_SLAVE_PORT):
    """Connect to Modbus TCP slave and return client object"""
    client = ModbusTcpClient(ip, port=port)
    if not client.connect():
        raise ConnectionError(f"❌ Could not connect to Modbus slave {ip}:{port}")
        exit(1) 
    return client

def read_inverter_metrics(client, unit_id=UNIT_ID):
    """
    Reads raw registers from Modbus, derives metrics,
    and returns a list of COSEM objects (dicts).
    """
    global _last_time, _total_energy_wh

    rr = client.read_holding_registers(0, 4, unit=unit_id)
    if rr.isError():
        raise RuntimeError(f"Error reading registers: {rr}")

    voltage, current, power, status = rr.registers

    # Derived metrics
    now = time.time()
    delta_hours = (now - _last_time) / 3600
    _last_time = now
    _total_energy_wh += power * delta_hours
    total_energy_kwh = round(_total_energy_wh / 1000, 4)

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

    # Build list of COSEM objects
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

    cosem_objects = []
    for obis, metric, value in metrics:
        entry = {
            "timestamp": timestamp,
            "obis_code": obis,
            "sensor": "Inverter",
            "metric": metric,
            "value": value
        }
        cosem_objects.append(entry)

    return cosem_objects
