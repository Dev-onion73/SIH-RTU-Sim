from pymodbus.client.sync import ModbusSerialClient

client = ModbusSerialClient(
    method='rtu',
    port='/dev/ttyACM0',  # slave serial port
    baudrate=9600,
    stopbits=1,
    bytesize=8,
    parity='N',
    timeout=5,
    xonxoff=False,
    rtscts=False
)

client.connect()

rr = client.read_holding_registers(0, 4, unit=1)

if rr.isError():
    print("Error reading registers:", rr)
else:
    print("Registers:", rr.registers)

client.close()
