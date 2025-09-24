import smbus2
import time
import os
import glob
import Adafruit_ADS1x15
import math

class BH1750:
    """Digital light sensor BH1750"""
    
    def __init__(self, i2c_address=0x23, bus=1):
        self.i2c_address = i2c_address
        self.bus = smbus2.SMBus(bus)
        self.is_connected = self._check_connection()
    
    def _check_connection(self):
        try:
            self.bus.read_byte(self.i2c_address)
            return True
        except OSError:
            return False
    
    def read_cosem(self):
        """Return COSEM-style dict for LoRa client"""
        if not self.is_connected:
            raise RuntimeError("BH1750 not connected")
        
        self.bus.write_byte(self.i2c_address, 0x10)  # high-res mode
        time.sleep(0.18)
        data = self.bus.read_i2c_block_data(self.i2c_address, 0x00, 2)
        lux = (data[0] << 8 | data[1]) / 1.2
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "timestamp": timestamp,
            "obis_code": "1-0:99.99.2",  # Example OBIS for light
            "sensor": "BH1750",
            "metric": "Illuminance",
            "value": round(lux, 2)
        }

class DS18B20:
    """Temperature sensor"""
    
    def __init__(self, sensor_id=None):
        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')
        self.base_dir = '/sys/bus/w1/devices/'
        self.device_folder = self._find_sensor(sensor_id)
        self.is_connected = self.device_folder is not None
    
    def _find_sensor(self, sensor_id):
        folders = glob.glob(self.base_dir + '28*')
        if not folders:
            return None
        if sensor_id:
            target = self.base_dir + sensor_id
            return target if target in folders else None
        return folders[0]
    
    def _read_raw(self):
        with open(self.device_folder + '/w1_slave', 'r') as f:
            return f.readlines()
    
    def read_cosem(self):
        """Return COSEM-style dict for LoRa client"""
        if not self.is_connected:
            raise RuntimeError("DS18B20 not connected")
        lines = self._read_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self._read_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos == -1:
            raise RuntimeError("Invalid DS18B20 data")
        temp_c = float(lines[1][equals_pos+2:]) / 1000.0
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        return {
            "timestamp": timestamp,
            "obis_code": "1-0:99.99.3",  # Example OBIS for temperature
            "sensor": "DS18B20",
            "metric": "Temperature",
            "value": round(temp_c, 2)
        }

class ACS712:
    """Current sensor"""
    
    SENSITIVITY = {'05B': 185, '20A': 100, '30A': 66}
    
    def __init__(self, adc_channel=0, model='20A', adc_gain=1):
        if model not in self.SENSITIVITY:
            raise ValueError("Invalid model")
        self.adc_channel = adc_channel
        self.model = model
        self.sensitivity = self.SENSITIVITY[model]
        self.adc = Adafruit_ADS1x15.ADS1115()
        self.adc_gain = adc_gain
        self.is_connected = True
        self.zero_voltage = 2.5  # default zero voltage
    
    def read_cosem(self):
        adc_val = self.adc.read_adc(self.adc_channel, gain=self.adc_gain)
        voltage = (adc_val * 4.096) / 32767.0
        current = (voltage - self.zero_voltage) * 1000 / self.sensitivity
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        return {
            "timestamp": timestamp,
            "obis_code": "1-0:99.99.4",  # Example OBIS for current
            "sensor": "ACS712",
            "metric": "Current",
            "value": round(current, 3)
        }
