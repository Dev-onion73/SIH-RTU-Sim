import smbus2
import time
import os
import glob
import Adafruit_ADS1x15  # For ACS712 analog reading

class BH1750:
    """Real implementation for BH1750 digital light sensor"""
    
    def __init__(self, i2c_address=0x23, bus=1):
        self.i2c_address = i2c_address
        self.bus = smbus2.SMBus(bus)
        self.is_connected = self._check_connection()
    
    def _check_connection(self):
        """Verify sensor is connected"""
        try:
            self.bus.read_byte(self.i2c_address)
            return True
        except OSError:
            return False
    
    def read(self):
        """Read light intensity in lux"""
        if not self.is_connected:
            raise RuntimeError("BH1750 not connected")
        
        # Send continuous high-res mode command
        self.bus.write_byte(self.i2c_address, 0x10)
        time.sleep(0.18)  # Wait for measurement (180ms)
        
        # Read 2 bytes
        data = self.bus.read_i2c_block_data(self.i2c_address, 0x00, 2)
        lux = (data[0] << 8 | data[1]) / 1.2
        return round(lux, 2)
    
    def status(self):
        """Check sensor status"""
        return {
            "connected": self.is_connected,
            "i2c_address": hex(self.i2c_address),
            "type": "BH1750 Light Sensor"
        }
    
    def power_down(self):
        """Put sensor in power-down mode"""
        if self.is_connected:
            self.bus.write_byte(self.i2c_address, 0x00)


class DS18B20:
    """Real implementation for DS18B20 temperature sensor"""
    
    def __init__(self, sensor_id=None):
        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')
        self.base_dir = '/sys/bus/w1/devices/'
        self.device_folder = self._find_sensor(sensor_id)
        self.is_connected = self.device_folder is not None
    
    def _find_sensor(self, sensor_id):
        """Find DS18B20 device folder"""
        device_folders = glob.glob(self.base_dir + '28*')
        if not device_folders:
            return None
        
        if sensor_id:
            # Look for specific sensor
            target = self.base_dir + sensor_id
            return target if target in device_folders else None
        else:
            # Use first available sensor
            return device_folders[0]
    
    def _read_raw(self):
        """Read raw sensor data"""
        with open(self.device_folder + '/w1_slave', 'r') as f:
            lines = f.readlines()
        return lines
    
    def read(self):
        """Read temperature in Celsius"""
        if not self.is_connected:
            raise RuntimeError("DS18B20 not connected")
        
        lines = self._read_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self._read_raw()
        
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            return round(temp_c, 2)
        else:
            raise RuntimeError("Invalid DS18B20 data")
    
    def status(self):
        """Check sensor status"""
        return {
            "connected": self.is_connected,
            "device_path": self.device_folder,
            "type": "DS18B20 Temperature Sensor"
        }


class ACS712:
    """Real implementation for ACS712 Hall Effect current sensor"""
    
    # Sensitivity values in mV/A for different models
    SENSITIVITY = {
        '05B': 185,  # ±5A
        '20A': 100,  # ±20A
        '30A': 66    # ±30A
    }
    
    def __init__(self, adc_channel=0, model='20A', adc_gain=1):
        """
        Initialize ACS712 sensor
        :param adc_channel: ADC channel (0-3 for ADS1115)
        :param model: '05B', '20A', or '30A'
        :param adc_gain: ADC gain (1 = ±4.096V)
        """
        if model not in self.SENSITIVITY:
            raise ValueError("Model must be '05B', '20A', or '30A'")
        
        self.adc_channel = adc_channel
        self.model = model
        self.sensitivity = self.SENSITIVITY[model]
        self.adc = Adafruit_ADS1x15.ADS1115()
        self.adc_gain = adc_gain
        self.is_connected = True  # ADC connection assumed
    
    def read(self):
        """Read current in Amperes"""
        # Read ADC value (16-bit signed)
        adc_value = self.adc.read_adc(self.adc_channel, gain=self.adc_gain)
        
        # Convert to voltage (ADS1115 default voltage range ±4.096V with gain=1)
        voltage = (adc_value * 4.096) / 32767.0
        
        # Calculate current (ACS712 outputs 2.5V at 0A)
        zero_voltage = 2.5
        current = (voltage - zero_voltage) * 1000 / self.sensitivity
        return round(current, 3)
    
    def status(self):
        """Check sensor status"""
        return {
            "connected": self.is_connected,
            "adc_channel": self.adc_channel,
            "model": self.model,
            "sensitivity_mV_per_A": self.sensitivity,
            "type": "ACS712 Current Sensor"
        }
    
    def calibrate_zero(self, samples=100):
        """Calibrate zero-point voltage (for no-load condition)"""
        total = 0
        for _ in range(samples):
            total += self.adc.read_adc(self.adc_channel, gain=self.adc_gain)
            time.sleep(0.01)
        avg_adc = total / samples
        self.zero_voltage = (avg_adc * 4.096) / 32767.0
        print(f"Calibrated zero voltage: {self.zero_voltage:.3f}V")


# # Example usage
# if __name__ == "__main__":
#     try:
#         # Initialize sensors
#         print("Initializing sensors...")
#         light_sensor = BH1750()
#         temp_sensor = DS18B20()
#         current_sensor = ACS712(model='20A')  # Using ±20A model
        
#         # Read all sensors
#         print("\n=== Sensor Readings ===")
#         print(f"Light: {light_sensor.read()} lux")
#         print(f"Temperature: {temp_sensor.read()} °C")
#         print(f"Current: {current_sensor.read()} A")
        
#         print("\n=== Sensor Status ===")
#         print("BH1750:", light_sensor.status())
#         print("DS18B20:", temp_sensor.status())
#         print("ACS712:", current_sensor.status())
        
#         # Optional: Calibrate current sensor (do this with no load)
#         # current_sensor.calibrate_zero()
        
#     except Exception as e:
#         print(f"Error: {e}")