### 📋 **Requirements**

#### Hardware:
- **Raspberry Pi** (or compatible Linux SBC with I2C/1-Wire support)
- **BH1750** light sensor (I2C interface)
- **DS18B20** temperature sensor (1-Wire interface)
- **ACS712** current sensor (±5A, ±20A, or ±30A)  
  → **Must be connected to an ADC** (e.g., **ADS1115**) since Raspberry Pi has no analog inputs

#### Software:
```bash
# Enable interfaces
sudo raspi-config  # → Enable I2C and 1-Wire

# Install dependencies
pip install smbus2 adafruit-ads1x15

# Load kernel modules (usually automatic after enabling in raspi-config)
sudo modprobe w1-gpio w1-therm
```

---

### ⚙️ **Usage Notes**

#### 1. **BH1750 (Light Sensor)**
- Connect to I2C (SDA → GPIO2, SCL → GPIO3)
- Default I2C address: `0x23`
- No external components needed

#### 2. **DS18B20 (Temperature Sensor)**
- Connect data line to GPIO4 (default 1-Wire pin)
- Use a **4.7kΩ pull-up resistor** between data and 3.3V
- Multiple sensors supported—specify `sensor_id` if needed (e.g., `"28-000005d69d5f"`)

#### 3. **ACS712 (Current Sensor)**
- **Must use with ADS1115 ADC** (or similar)
- Power ACS712 with **5V** (not 3.3V)
- Connect ACS712 output → ADS1115 input (e.g., A0)
- Choose model in code: `'05B'`, `'20A'`, or `'30A'`
- **Calibrate at zero current** for best accuracy:
  ```python
  current_sensor.calibrate_zero()  # Run with no load
  ```

