import json
# import meshtastic.serial_interface
from modbus_master import connect_modbus, read_inverter_metrics
# In future: from sensor_x import read_sensor_data
from sensor_modules import BH1750, DS18B20, ACS712
import time

def send_cosem_objects(iface, cosem_data):
    """
    Accepts either a single COSEM dict or a list of dicts,
    normalizes to a list, then sends each as JSON over LoRa.
    """
    if isinstance(cosem_data, dict):
        cosem_data = [cosem_data]  # wrap single object in list

    for obj in cosem_data:
        print(obj)
        # payload = json.dumps(obj)
        # iface.sendText(payload)
        # print("✅ Sent:", payload)

def main(poll_interval=1):
    # Connect LoRa interface
    # iface = meshtastic.serial_interface.SerialInterface()

    # Connect Modbus (example)
    try:
        modbus_client = connect_modbus(ip="127.0.0.1", port=1502)
        print("✅ Modbus connected")
    except Exception as e:
        print(f"⚠ Could not connect Modbus slave: {e}")
        modbus_client = None
        exit(1)

    # List of data source functions
    # Each function returns either a dict or a list of COSEM objects
    data_sources = [
        lambda: read_slave_metrics(modbus_client) if modbus_client else None,
        # read_ldr,
        # read_ct,
        # Add more sensor functions here
    ]

    print("🔄 Starting main loop...")
    try:
        while True:
            for func in data_sources:
                try:
                    result = func()
                    if result:
                        send_cosem_objects(0, result)
                except Exception as e:
                    print(f"⚠ Error in data source {func.__name__ if hasattr(func, '__name__') else func}: {e}")

            time.sleep(poll_interval)

    except KeyboardInterrupt:
        print("\n⏹ Stopping client...")
    finally:
        if modbus_client:
            modbus_client.close()

if __name__ == "__main__":
    main()
