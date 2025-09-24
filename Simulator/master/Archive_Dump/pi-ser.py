import serial
ser = serial.Serial('/dev/ttyGS0', 9600, timeout=1)
ser.write(b'hello')
print(ser.read(10))
