import time
from pymodbus.server.sync import StartSerialServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification
import threading

# Initial inverter registers: V, A, W, Status
hr_values = [230, 12, 2760, 1]

store = ModbusSlaveContext(
    hr=ModbusSequentialDataBlock(0, hr_values.copy()),
    ir=ModbusSequentialDataBlock(0, [0]*100)
)
context = ModbusServerContext(slaves=store, single=True)

identity = ModbusDeviceIdentification()
identity.VendorName = 'MVP-InverterSim'
identity.ProductName = 'Virtual-Modbus-Inverter'

# Background thread to update registers
def update_registers():
    while True:
        hr_values[2] += 10
        if hr_values[2] > 5000:
            hr_values[2] = 1000
        context[0x00].setValues(3, 0, hr_values)  # 3 = holding registers
        time.sleep(1)

if __name__ == "__main__":
    print("Starting virtual Modbus RTU Slave on /tmp/ttyACM0...")
    threading.Thread(target=update_registers, daemon=True).start()
    StartSerialServer(
        context,
        identity=identity,
        port='/tmp/ttyACM0',
        baudrate=9600,
        stopbits=1,
        bytesize=8,
        parity='N',
        timeout=5
    )
