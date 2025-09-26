from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification
from threading import Thread
import time
import random

def run_bms_slave(unit_id=5):  # <-- set your desired Unit ID here
    # Initial BMS values: Voltage(V*100), Current(A*100), SOC(%*100), Temp(°C*10), Status
    hr_values = [3600, 500, 8000, 250, 1]

    store = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(0, hr_values.copy()),
        ir=ModbusSequentialDataBlock(0, [0]*100)
    )
    
    # Context with custom Unit ID
    context = ModbusServerContext(slaves={unit_id: store}, single=False)

    identity = ModbusDeviceIdentification()
    identity.VendorName = "MVP-BMS-Sim"
    identity.ProductName = "TCP-Modbus-BMS"

    def update_values():
        status_codes = [1, 2, 3, 4]
        while True:
            voltage = 3600 + random.randint(-50, 50)
            current = 500 + random.randint(-50, 50)
            soc = max(0, min(10000, hr_values[2] + random.randint(-20, 20)))
            temp = 250 + random.randint(-5, 5)
            hr_values[0] = voltage
            hr_values[1] = current
            hr_values[2] = soc
            hr_values[3] = temp
            hr_values[4] = random.choice(status_codes)

            context[unit_id].setValues(3, 0, hr_values)
            time.sleep(1)

    Thread(target=update_values, daemon=True).start()

    print(f"✅ BMS Modbus TCP Slave running on 0.0.0.0:1502 (Unit ID={unit_id})")
    StartTcpServer(
        context,
        identity=identity,
        address=("0.0.0.0", 1502)
    )

if __name__ == "__main__":
    run_bms_slave(unit_id=10)  # <-- example: Unit ID = 10
