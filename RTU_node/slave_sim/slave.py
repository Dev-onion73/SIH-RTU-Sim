from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification
from threading import Thread
import time
import random

def run_slave():
    # Initial values: Voltage(V), Current(A), Power(W), Status(Code)
    hr_values = [230, 12, 2760, 1]

    store = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(0, hr_values.copy()),
        ir=ModbusSequentialDataBlock(0, [0]*100)
    )
    context = ModbusServerContext(slaves=store, single=True)

    identity = ModbusDeviceIdentification()
    identity.VendorName = "MVP-InverterSim"
    identity.ProductName = "TCP-Modbus-Inverter"

    def update_values():
        status_codes = [1, 2, 3, 4]  # 1=OK, 2=Warning, 3=Fault, 4=Maintenance
        while True:
            # Simulate dynamic Voltage, Current, Power
            hr_values[0] = 220 + random.randint(-5,5)  # Voltage
            hr_values[1] = 10 + random.randint(0,5)    # Current
            hr_values[2] = hr_values[0] * hr_values[1]  # Power = V * I

            # Update status code randomly for demonstration
            hr_values[3] = random.choice(status_codes)

            # Write updated values to holding registers
            context[0x00].setValues(3, 0, hr_values)
            time.sleep(1)  # Update every second

    # Start background thread to update values
    Thread(target=update_values, daemon=True).start()

    print("✅ Modbus TCP Slave running on 0.0.0.0:1502 (Unit ID=1)")
    StartTcpServer(
        context,
        identity=identity,
        address=("0.0.0.0", 1502)  # Listen on all interfaces, port 1502
    )

if __name__ == "__main__":
    run_slave()
