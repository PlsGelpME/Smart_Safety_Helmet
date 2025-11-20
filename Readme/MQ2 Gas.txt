# MQ2 Gas Sensor MicroPython Driver

## Overview
`__gas__.py` provides a power-efficient gas detection system using the MQ2 gas sensor. Features intelligent power management with hourly monitoring during specified operating hours to maximize battery life.

## Features
- **Power Management**: Automatic sensor power cycling for energy efficiency
- **Hourly Monitoring**: Configurable daily operating hours with on-the-hour readings
- **Multi-threshold Detection**: Warning and alarm levels for gas concentration
- **Sensor Stabilization**: Built-in warm-up period for accurate readings
- **Noise Reduction**: Multiple sample averaging for reliable data

## Hardware Requirements
- MQ2 Gas Sensor Module
- ESP32 or compatible MicroPython board
- ADC pin for gas concentration reading
- Digital pin for sensor power control

## Installation
```python
from __gas__ import Gas
```

## Quick Start
```python
# Initialize gas sensor with power management
gas_sensor = Gas(
    analog_pin=ADC(Pin(32)),
    power_pin=Pin(25, Pin.OUT),
    operating_hours=(8, 18)  # Monitor from 8 AM to 6 PM
)

# Check if it's time to monitor
if gas_sensor.should_monitor_now():
    reading = gas_sensor.take_reading()
    print(f"Gas Level: {reading['value']} - Status: {reading['status']}")
```

## API Reference

### Class: Gas

#### Constructor
```python
Gas(analog_pin, power_pin, warning_threshold=1500, alarm_threshold=2500, warm_up_time=15, operating_hours=(8, 18))
```
- `analog_pin`: Pre-configured ADC object for gas reading
- `power_pin`: Pre-configured Pin object for power control
- `warning_threshold`: ADC value for warning status (default: 1500)
- `alarm_threshold`: ADC value for alarm status (default: 2500)
- `warm_up_time`: Sensor stabilization time in seconds (default: 15)
- `operating_hours`: Daily monitoring window as (start_hour, end_hour)

#### Key Methods

##### `should_monitor_now()`
Checks if current time is within operating hours and at start of hour.
- **Returns**: `True` if monitoring should occur, `False` otherwise

##### `take_reading()`
Takes a complete gas reading with full power management cycle.
- **Returns**: Dictionary with:
  - `value`: Average ADC reading
  - `status`: "NORMAL", "WARNING", or "ALARM"
  - `timestamp`: Unix timestamp
  - `samples`: Raw sample data

##### `set_thresholds(warning, alarm)`
Updates gas concentration thresholds.
- `warning`: New warning threshold value
- `alarm`: New alarm threshold value

##### `_get_reading_status(value)`
Determines status based on gas concentration (internal method).

## Default Configuration
- **Operating Hours**: 8:00 - 18:00 (10-hour window)
- **Monitoring Frequency**: Once per hour at :00 minutes
- **Warm-up Time**: 15 seconds for sensor stabilization
- **Sampling**: 10 samples over 4.5 seconds
- **Warning Threshold**: 1500 ADC value
- **Alarm Threshold**: 2500 ADC value

## Usage Examples

### Basic Monitoring
```python
gas = Gas(ADC(Pin(32)), Pin(25, Pin.OUT))

while True:
    if gas.should_monitor_now():
        data = gas.take_reading()
        print(f"Gas: {data['value']} - {data['status']}")
    time.sleep(60)  # Check every minute
```

### Custom Configuration
```python
# 24-hour monitoring with custom thresholds
gas = Gas(
    analog_pin=ADC(Pin(32)),
    power_pin=Pin(25, Pin.OUT),
    warning_threshold=1200,
    alarm_threshold=3000,
    warm_up_time=20,
    operating_hours=(0, 24)  # 24-hour monitoring
)
```

### Emergency Response
```python
reading = gas_sensor.take_reading()
if reading['status'] == "ALARM":
    # Trigger emergency protocols
    activate_alarm()
    send_emergency_alert()
```

## Power Management
- Sensor powered OFF by default for maximum energy savings
- Automatic power-on only during scheduled monitoring periods
- 15-second warm-up ensures accurate readings
- Guaranteed power-off after reading completion

## Status Levels
- **NORMAL**: Below warning threshold (safe conditions)
- **WARNING**: Between warning and alarm thresholds (elevated levels)
- **ALARM**: Above alarm threshold (emergency conditions)

## Technical Details

### Sensor Behavior
- MQ2 requires warm-up time for heater stabilization
- Multiple samples reduce noise and improve accuracy
- Power cycling extends sensor lifespan

### Timing Considerations
- Operating hours use 24-hour format (0-23)
- Monitoring occurs precisely at :00 minutes
- Warm-up time should accommodate environmental conditions

## Troubleshooting

### Common Issues
1. **Inconsistent Readings**: Ensure adequate warm-up time
2. **No Power Control**: Verify power pin configuration
3. **Wrong Timing**: Check RTC is properly set
4. **Threshold Calibration**: Adjust based on environment and gas types

### Calibration Notes
- Thresholds are ADC values (0-4095 for 12-bit ESP32 ADC)
- Calibrate thresholds for specific environment and gas concentrations
- Consider baseline readings in clean air for reference

## Applications
- Environmental monitoring systems
- Industrial safety equipment
- Smart home air quality monitoring
- Battery-powered gas detection devices

## Dependencies
- `machine.ADC`
- `machine.Pin`
- `machine.RTC`
- `time`

## License
MicroPython Gas Sensor Driver with Power Management