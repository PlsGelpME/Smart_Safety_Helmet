# boot.py file Configuration

## Overview
Main hardware configuration and initialization file for a comprehensive multi-sensor emergency detection system. This file sets up all sensors and defines the complete hardware interface for environmental monitoring, health tracking, and emergency detection.

## System Features
- **Multi-sensor Integration**: Gyroscope, GPS, gas, temperature, and pulse oximetry
- **Power Management**: Intelligent power cycling for energy efficiency
- **Emergency Detection**: Free-fall, impact, temperature, and gas level monitoring
- **Health Monitoring**: Real-time heart rate and blood oxygen tracking
- **Wireless Communication**: MQTT integration for remote monitoring

## Hardware Setup

### Required Components
- ESP32 Development Board
- MPU6050 Gyroscope/Accelerometer
- Neo-6M GPS Module
- MQ2 Gas Sensor
- MAX30100 Pulse Oximeter
- NTC Thermistor (10kΩ)
- Force Sensor
- Buzzer
- Safety Switch

### Pin Assignment Guide

#### Analog Inputs
```python
temp_pin = ADC(0)    # NTC thermistor for temperature
gas_pin = ADC(0)     # MQ2 gas sensor analog output
```
**Important**: Pins 25, 26, 27 are unavailable when using WiFi

#### I2C Peripherals
```python
# I2C Channel 1 - Gyroscope
gyro_sda = Pin(0)    # MPU6050 data line
gyro_scl = Pin(0)    # MPU6050 clock line
gyro_int = Pin(0)    # Free-fall interrupt

# I2C Channel 2 - Pulse Oximeter
pulse_sda = Pin(0)   # MAX30100 data line
pulse_scl = Pin(0)   # MAX30100 clock line
```

#### UART Communication
```python
gps_rx = Pin(0)      # Receive data from GPS (GPS TX → ESP32 RX)
gps_tx = Pin(0)      # Transmit to GPS (optional configuration)
```

#### Power Control
```python
gas_pwr = Pin(0)     # Gas sensor power enable
gps_pwr = Pin(0)     # GPS module power enable
```

#### Digital I/O
```python
frc_pin = Pin(0)     # Force sensor input (impact detection)
belt_int = Pin(0)    # Safety belt interrupt switch
buzz_pin = Pin(0)    # Buzzer output for alerts
```

## Sensor Configuration

### MPU6050 Gyroscope
```python
gyro = GyroSetup(i2c_scl_pin=gyro_scl, i2c_sda_pin=gyro_sda, int_pin=gyro_int)
gyro.configure_freefall(threshold=0x10, duration=0x05)
```
- **Free-fall Sensitivity**: 0x10 threshold (~0.16g)
- **Detection Duration**: 0x05 (~5ms)
- **Interrupt**: Hardware-triggered on free-fall detection

### GPS Module
```python
gps = GPS(power_pin=gps_pwr, rx_pin=gps_rx, tx_pin=gps_tx, baudrate=9600)
```
- **Initial State**: Powered OFF for energy savings
- **Communication**: 9600 baud UART
- **Features**: Position caching and power management

### Gas Sensor (MQ2)
```python
gas_sensor = GasSensor(gas_adc_pin=gas_pin, power_pin=gas_pwr, sensor_type="MQ2")
gas_sensor.set_threshold(warning=1500, alarm=2500)
```
- **Detection**: Flammable gases and smoke
- **Warning Level**: ADC value 1500
- **Alarm Level**: ADC value 2500
- **Power Management**: Hourly monitoring cycles

### Temperature Sensor
```python
temp = Temp(pin=temp_pin, normal_temp=36)
```
- **Sensor**: NTC thermistor with Steinhart-Hart calculation
- **Alert Threshold**: 36°C (configurable)
- **Measurement**: Multi-sample averaging for accuracy

### Pulse Oximeter
```python
pulse = Pulse(sda_pin=pulse_sda, scl_pin=pulse_scl, sample_rate=100)
```
- **Sample Rate**: 100Hz for precise measurements
- **Data**: Heart rate (BPM) and blood oxygen (SpO2)
- **Calibration**: Configurable LED currents for different skin types

## System Initialization

### Memory Management
```python
esp.osdebug(None)    # Disable vendor debug messages
gc.collect()         # Clean memory before startup
gc.enable()          # Enable automatic garbage collection
```

### ADC Configuration
```python
temp_pin.atten(ADC.ATTN_11DB)  # Set 0-3.3V range for temperature
gas_pin.atten(ADC.ATTN_11DB)   # Set 0-3.3V range for gas sensor
```

## Emergency Detection Matrix

| Trigger | Sensor | Threshold | Response |
|---------|--------|-----------|----------|
| Free-fall | Gyroscope | 0.16g for 5ms | Emergency protocol |
| Impact | Force Sensor | Digital trigger | Emergency protocol |
| High Temp | Thermistor | >36°C | Warning alert |
| Gas Leak | MQ2 Sensor | >2500 ADC | Emergency protocol |
| Belt Removal | Safety Switch | Digital low | Warning alert |

## Power Management Strategy

### Sensor Power States
- **Always On**: Gyroscope (emergency detection)
- **Scheduled**: Gas sensor (hourly readings)
- **On-Demand**: GPS (position acquisition only)
- **Periodic**: Pulse oximeter (configurable intervals)

### Energy Optimization
- Automatic power cycling for high-consumption sensors
- Sleep modes between measurement cycles
- Cache-based position reuse for GPS

## Integration Notes

### I2C Bus Separation
- **Bus 1**: Gyroscope (high-priority interrupts)
- **Bus 2**: Pulse oximeter (continuous health monitoring)

### Interrupt Handling
- Hardware interrupts for immediate emergency response
- Debounced inputs for safety switches
- Priority-based emergency processing

### Data Flow
1. Sensor data acquisition
2. Threshold comparison
3. Emergency state determination
4. MQTT message generation
5. Remote notification

## Usage Examples

### Basic Monitoring Loop
```python
while True:
    # Check for emergency conditions
    if emergency_detected():
        execute_emergency_protocol()
    
    # Periodic sensor readings
    read_environmental_sensors()
    time.sleep(1)
```

### Emergency Response
```python
def execute_emergency_protocol():
    activate_buzzer()
    acquire_gps_location()
    transmit_vital_signs()
    send_emergency_alert()
```

## Troubleshooting

### Common Setup Issues
1. **I2C Communication**: Verify pull-up resistors and address conflicts
2. **GPS No Fix**: Ensure clear sky view and adequate timeout
3. **Sensor Readings**: Check power supply and reference voltages
4. **WiFi Conflicts**: Avoid ADC pins 25, 26, 27

### Diagnostic Commands
```python
gyro.verify_connection()      # Check gyroscope comms
gps.quick_status()           # Verify GPS functionality
pulse.get_sensor_info()      # Pulse oximeter status
```

## Application Scenarios

### Healthcare Monitoring
- Elderly fall detection
- Vital signs tracking
- Emergency location services

### Industrial Safety
- Worker safety monitoring
- Environmental hazard detection
- Emergency response coordination

### Personal Safety
- Adventure sports monitoring
- Remote location tracking
- Emergency alert systems

## Dependencies
- `__gyro__.py` - MPU6050 driver
- `__GPS__.py` - Neo-6M GPS driver  
- `__pulse__.py` - MAX30100 driver
- `__gas__.py` - MQ2 gas sensor driver
- `temp.py` - NTC temperature driver

## License
Emergency Detection System - Main Configuration File