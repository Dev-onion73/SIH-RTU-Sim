from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.server.sync import StartSerialServer

SLAVE_ID = 1  # Must match master

store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, [0]*100),
    co=ModbusSequentialDataBlock(0, [0]*100),
    hr=ModbusSequentialDataBlock(0, [11,22,33,44,55]),
    ir=ModbusSequentialDataBlock(0, [0]*100)
)

context = ModbusServerContext(slaves={SLAVE_ID: store}, single=False)

print(f"Starting Modbus RTU slave with ID {SLAVE_ID} on /dev/ttyACM0 ...")
StartSerialServer(
    context=context,
    port="/dev/ttyACM0",
    baudrate=9600,
    stopbits=1,
    bytesize=8,
    parity='N'
)
