import time
import math
from pymodbus.client.sync import ModbusTcpClient

# -------------------
# Slave configurations
# -------------------
SLAVES = {
    "inverter": {"ip": "127.0.0.1", "port": 1502, "unit_id": 1, "num_regs": 4},
    "bms": {"ip": "127.0.0.1", "port": 1503, "unit_id": 10, "num_regs": 5}
}

# -------------------
# Slave state for energy or delta calculations
# -------------------
_slave_state = {
    "inverter": {"_total_energy_wh": 0, "_last_time": time.time()},
    "bms": {"_last_time": time.time()}
}

# -------------------
# Connect to Modbus TCP slave
# -------------------
def connect_modbus(ip, port):
    client = ModbusTcpClient(ip, port=port)
    if not client.connect():
        raise ConnectionError(f"❌ Could not connect to Modbus slave {ip}:{port}")
    return client

# -------------------
# Read metrics per slave
# -------------------
def read_slave_metrics(client, slave_name, unit_id, num_registers):
    state = _slave_state[slave_name]
    rr = client.read_holding_registers(0, num_registers, unit=unit_id)
    if rr.isError():
        raise RuntimeError(f"Error reading {slave_name} registers: {rr}")

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    cosem_objects = []

    if slave_name == "inverter":
        voltage, current, power, status = rr.registers
        # Energy calculation
        now = time.time()
        delta_hours = (now - state["_last_time"]) / 3600
        state["_last_time"] = now
        state["_total_energy_wh"] += power * delta_hours
        total_energy_kwh = round(state["_total_energy_wh"] / 1000, 4)

        # Apparent & Reactive power
        S = voltage * current
        Q = round(math.sqrt(max(0, S**2 - power**2)), 2)
        PF = round(power / S if S != 0 else 0, 3)

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

    elif slave_name == "bms":
        pack_voltage, pack_current, soc, temp, status = rr.registers
        metrics = [
            ("1-0:32.7.0", "PackVoltage", pack_voltage),
            ("1-0:31.7.0", "PackCurrent", pack_current),
            ("1-0:51.7.0", "SOC", soc),
            ("1-0:52.7.0", "Temperature", temp),
            ("0-0:96.7.9", "Status", status)
        ]

    # Convert to COSEM-style dicts
    for obis, metric, value in metrics:
        cosem_objects.append({
            "timestamp": timestamp,
            "obis_code": obis,
            "sensor": slave_name.capitalize(),
            "metric": metric,
            "value": value
        })

    return cosem_objects

# -------------------
# Main loop
# -------------------
if __name__ == "__main__":
    clients = {}
    try:
        # Connect all slaves
        for name, cfg in SLAVES.items():
            clients[name] = connect_modbus(cfg["ip"], cfg["port"])
            print(f"✅ Connected to {name} at {cfg['ip']}:{cfg['port']} (Unit ID={cfg['unit_id']})")

        while True:
            for name, cfg in SLAVES.items():
                try:
                    data = read_slave_metrics(
                        clients[name],
                        slave_name=name,
                        unit_id=cfg["unit_id"],
                        num_registers=cfg["num_regs"]
                    )
                    for obj in data:
                        print(obj)
                except Exception as e:
                    print(f"⚠ Error reading {name}: {e}")

            time.sleep(1)  # Poll interval

    except KeyboardInterrupt:
        print("\n⏹ Stopping master...")
    finally:
        for c in clients.values():
            c.close()
