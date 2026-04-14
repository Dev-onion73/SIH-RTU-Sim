import smbus2
import time
import os
import glob
import serial

# ===================== BH1750 =====================
class BH1750:
    def __init__(self, i2c_address=0x23, bus=1):
        self.addr = i2c_address
        self.bus = smbus2.SMBus(bus)
        self.connected = self._check()

    def _check(self):
        try:
            self.bus.read_byte(self.addr)
            return True
        except:
            return False

    def read(self):
        if not self.connected:
            raise RuntimeError("BH1750 not connected")

        self.bus.write_byte(self.addr, 0x10)
        time.sleep(0.18)

        data = self.bus.read_i2c_block_data(self.addr, 0x00, 2)
        lux = (data[0] << 8 | data[1]) / 1.2
        return round(lux, 2)

    def status(self):
        return {
            "connected": self.connected,
            "i2c_address": hex(self.addr),
            "type": "BH1750 Light Sensor"
        }


# ===================== DS18B20 =====================
class DS18B20:
    def __init__(self, sensor_id=None):
        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')

        self.base_dir = '/sys/bus/w1/devices/'
        self.device = self._find(sensor_id)
        self.connected = self.device is not None

    def _find(self, sensor_id):
        devices = glob.glob(self.base_dir + '28*')
        if not devices:
            return None
        if sensor_id:
            target = self.base_dir + sensor_id
            return target if target in devices else None
        return devices[0]

    def _read_raw(self):
        with open(self.device + '/w1_slave', 'r') as f:
            return f.readlines()

    def read(self):
        if not self.connected:
            raise RuntimeError("DS18B20 not connected")

        lines = self._read_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self._read_raw()

        temp_pos = lines[1].find('t=')
        temp_c = float(lines[1][temp_pos+2:]) / 1000.0
        return round(temp_c, 2)

    def status(self):
        return {
            "connected": self.connected,
            "device": self.device,
            "type": "DS18B20 Temperature Sensor"
        }


# ===================== ESP32 Voltage =====================
class ESP32Voltage:
    def __init__(self, port='/dev/ttyUSB0', baud=115200):
        self.port = port
        self.baud = baud
        self.ser = None
        self.connected = self._connect()

    def _connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            time.sleep(2)  # allow ESP32 reset
            self.ser.reset_input_buffer()
            return True
        except:
            return False

    def read(self):
        if not self.connected:
            raise RuntimeError("ESP32 not connected")

        while True:
            raw = self.ser.readline()
            try:
                line = raw.decode('utf-8').strip()
            except:
                continue

            if line:
                try:
                    return round(float(line), 3)
                except:
                    continue

    def status(self):
        return {
            "connected": self.connected,
            "port": self.port,
            "type": "ESP32 Voltage Sensor"
        }
