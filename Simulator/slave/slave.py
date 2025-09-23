from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification
import time
from threading import Thread

def run_slave():
    # Initial values: Voltage, Current, Power, Status
    hr_values = [230, 12, 2760, 1]

    store = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(0, hr_values.copy()),
        ir=ModbusSequentialDataBlock(0, [0] * 100)
    )
    context = ModbusServerContext(slaves=store, single=True)

    identity = ModbusDeviceIdentification()
    identity.VendorName = "MVP-InverterSim"
    identity.ProductName = "TCP-Modbus-Inverter"

    def update_values():
        while True:
            # Simulate changing power
            hr_values[2] += 10
            if hr_values[2] > 5000:
                hr_values[2] = 1000
            # Write updated values
            context[0x00].setValues(3, 0, hr_values)
            time.sleep(1)

    Thread(target=update_values, daemon=True).start()

    print("✅ Modbus TCP Slave running on 0.0.0.0:1502 (Unit ID=1)")
    StartTcpServer(
        context,
        identity=identity,
        address=("0.0.0.0", 1502)  # Listen on all interfaces, port 1502
    )

if __name__ == "__main__":
    run_slave()
