import serial
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
while True:
    data = ser.read(10)
    if data:
        print("Received:", data)
        ser.write(data)  # echo back
