from pymodbus.client.sync import ModbusTcpClient
import time

# Replace with your PC's IP
PC_IP = "192.168.0.10"
PORT = 1502

client = ModbusTcpClient(PC_IP, port=PORT)

if not client.connect():
    print("❌ Failed to connect to Modbus TCP Slave")
    exit(1)

print("✅ Connected to Modbus Slave")

try:
    while True:
        rr = client.read_holding_registers(0, 4, unit=1)
        if rr.isError():
            print("❌ Error reading registers:", rr)
        else:
            voltage, current, power, status = rr.registers
            print(f"Voltage: {voltage} V | Current: {current} A | Power: {power} W | Status: {status}")
        time.sleep(1)
except KeyboardInterrupt:
    print("\n⏹ Stopping master...")
finally:
    client.close()

