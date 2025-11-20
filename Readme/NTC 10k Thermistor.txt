# NTC Thermistor Temperature Sensor

## Overview
`temp.py` provides accurate temperature measurement using NTC thermistors with the Steinhart-Hart equation. Supports multiple temperature units and includes threshold-based alerting for monitoring applications.

## Features
- **Multi-unit Support**: Celsius, Fahrenheit, and Kelvin temperature scales
- **Noise Reduction**: 100-sample averaging for stable readings
- **NTC Calibration**: Configurable beta coefficient and resistor values
- **Threshold Alerts**: Programmable temperature limits for monitoring
- **Steinhart-Hart Equation**: Industry-standard thermistor linearization

## Hardware Requirements
- NTC Thermistor (10kΩ recommended)
- Fixed resistor (5.8kΩ default) for voltage divider
- ESP32 or compatible MicroPython board
- ADC pin for voltage measurement

## Installation
```python
from temp import Temp
```

## Quick Start
```python
# Initialize temperature sensor
temp_sensor = Temp(ADC(Pin(32)), normal_temp=39)

# Read temperature in Celsius
temperature = temp_sensor.getTemp(unit=1)
print(f"Temperature: {temperature:.1f}°C")

# Check if temperature exceeds threshold
if temp_sensor.istemp():
    print("High temperature alert!")
```

## API Reference

### Class: Temp

#### Constructor
```python
Temp(pin, normal_temp=39)
```
- `pin`: Pre-configured ADC object for thermistor reading
- `normal_temp`: Threshold temperature for alerts (default: 39°C)

#### Key Methods

##### `getTemp(unit=1)`
Reads and calculates temperature from NTC thermistor.
- `unit`: Temperature unit (0=Kelvin, 1=Celsius, 2=Fahrenheit)
- **Returns**: Temperature in requested unit

##### `istemp()`
Checks if current temperature exceeds threshold.
- **Returns**: `True` if temperature > threshold, `False` otherwise

##### `setThreshold(t)`
Sets temperature threshold for alerts.
- `t`: New threshold temperature value

##### `calibration(beta, R_fixed)`
Calibrates thermistor parameters.
- `beta`: Beta coefficient for specific NTC thermistor
- `R_fixed`: Fixed resistor value in voltage divider

## Default Configuration
- **Beta Coefficient**: 3950 (common for 10kΩ NTC thermistors)
- **Reference Resistance**: 10kΩ at 25°C
- **Fixed Resistor**: 5.8kΩ (voltage divider)
- **Reference Temperature**: 298.15K (25°C)
- **ADC Reference**: 3.3V, 12-bit (0-4095)

## Usage Examples

### Basic Temperature Reading
```python
temp_sensor = Temp(ADC(Pin(32)))

# Read in different units
celsius = temp_sensor.getTemp(1)      # Celsius
fahrenheit = temp_sensor.getTemp(2)   # Fahrenheit
kelvin = temp_sensor.getTemp(0)       # Kelvin

print(f"{celsius:.1f}°C = {fahrenheit:.1f}°F = {kelvin:.1f}K")
```

### Temperature Monitoring
```python
temp_sensor = Temp(ADC(Pin(32)), normal_temp=38.5)

while True:
    current_temp = temp_sensor.getTemp(1)
    
    if temp_sensor.istemp():
        print(f"ALERT: High temperature {current_temp:.1f}°C")
        trigger_cooling_system()
    
    time.sleep(60)  # Check every minute
```

### Custom Calibration
```python
# Calibrate for specific thermistor
temp_sensor = Temp(ADC(Pin(32)))
temp_sensor.calibration(beta=3977, R_fixed=5600)  # Custom values
temp_sensor.setThreshold(40.0)  # Set custom alert threshold
```

## Temperature Calculation

### Steinhart-Hart Equation
Uses simplified beta version:
```
1/T = 1/T0 + (1/β) × ln(R/R0)
```
Where:
- T = Current temperature (Kelvin)
- T0 = Reference temperature (298.15K)
- β = Beta coefficient (3950)
- R = Current thermistor resistance
- R0 = Reference resistance (10kΩ)

### Voltage Divider
```
R_ntc = R_fixed × (V_supply - V_adc) / V_adc
```

## Technical Specifications

### Accuracy Considerations
- **Beta Coefficient**: Critical for accuracy - obtain from thermistor datasheet
- **Fixed Resistor**: Use 1% tolerance or better for precise measurements
- **ADC Resolution**: 12-bit provides ~0.1°C resolution
- **Averaging**: 100 samples reduce noise significantly

### Measurement Range
- **Typical Range**: -40°C to +125°C (depends on thermistor)
- **Accuracy**: ±1°C with proper calibration
- **Resolution**: ~0.1°C with 12-bit ADC

## Troubleshooting

### Common Issues
1. **Inaccurate Readings**: Verify beta coefficient and resistor values
2. **Noisy Data**: Ensure stable power supply and proper filtering
3. **Wrong Temperature**: Check voltage divider resistor values
4. **Calibration Issues**: Use known temperature points for calibration

### Calibration Procedure
1. Measure temperature with reference thermometer
2. Adjust beta coefficient until readings match
3. Fine-tune fixed resistor value if necessary
4. Test across temperature range for linearity

## Applications
- Environmental monitoring systems
- Medical temperature monitoring
- Industrial process control
- HVAC systems
- Food safety monitoring
- Scientific experiments

## Dependencies
- `machine.ADC`
- `math.log`
- `time.sleep_ms`

## License
MicroPython NTC Thermistor Temperature Sensor Driver