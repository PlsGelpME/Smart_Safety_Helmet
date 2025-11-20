# Neo-6M GPS Module MicroPython Driver

## Overview
`gps_module.py` provides power-efficient GPS location acquisition using the Neo-6M GPS module. Features intelligent power management with on-demand positioning and position caching to minimize energy consumption.

## Features
- **Power Management**: Automatic GPS power cycling for energy efficiency
- **Position Caching**: Reuse recent fixes to avoid unnecessary GPS activations
- **NMEA Parsing**: Automatic GGA sentence parsing for position data
- **Configurable Timeouts**: Adjustable fix acquisition timeouts
- **Diagnostic Tools**: Quick status checks for system verification

## Hardware Requirements
- Neo-6M GPS Module
- ESP32 or compatible MicroPython board
- UART RX pin (GPS TX → ESP32 RX)
- Optional: UART TX pin for GPS configuration
- Optional: Digital pin for GPS power control

## Installation
```python
from gps_module import GPS
```

## Quick Start
```python
# Initialize GPS with power management
gps = GPS(power_pin=23, rx_pin=16, tx_pin=17)

# Get current position (automatically powers on/off)
position = gps.get_position(timeout=30)
if position:
    print(f"Lat: {position['latitude']}, Lon: {position['longitude']}")
```

## API Reference

### Class: GPS

#### Constructor
```python
GPS(power_pin=23, rx_pin=16, tx_pin=17, uart_num=2, baudrate=9600)
```
- `power_pin`: GPIO for GPS power control (None for always powered)
- `rx_pin`: UART RX pin for GPS data reception
- `tx_pin`: UART TX pin for GPS configuration (optional)
- `uart_num`: UART peripheral number (default: 2)
- `baudrate`: Communication speed (default: 9600)

#### Key Methods

##### `get_position(timeout=None)`
Acquires current GPS position with full power management.
- `timeout`: Maximum wait time in seconds (default: 45)
- **Returns**: Dictionary with position data or None if timeout

##### `get_position_cached(cache_time=300, timeout=None)`
Uses cached position if recent, otherwise acquires new fix.
- `cache_time`: Maximum cache age in seconds (default: 300)
- **Returns**: Position data or None

##### `quick_status()`
Brief diagnostic check of GPS functionality.
- **Returns**: Prints GPS data samples for verification

##### `power_on()`
Manually powers on GPS module.

##### `power_off()`
Manually powers off GPS module.

## Default Configuration
- **Baud Rate**: 9600 (standard for Neo-6M)
- **Fix Timeout**: 45 seconds
- **Cache Time**: 300 seconds (5 minutes)
- **Power State**: Starts powered OFF
- **UART**: UART2 on ESP32

## Usage Examples

### Basic Location Acquisition
```python
gps = GPS(power_pin=23, rx_pin=16)

position = gps.get_position(timeout=30)
if position:
    print(f"Location: {position['latitude']}, {position['longitude']}")
    print(f"Altitude: {position['altitude']}")
    print(f"Satellites: {position['satellites']}")
```

### Power-Efficient Monitoring
```python
# Use cached positions to minimize power consumption
gps = GPS(power_pin=23, rx_pin=16)

while True:
    position = gps.get_position_cached(cache_time=600)  # 10-minute cache
    if position:
        send_to_server(position)
    time.sleep(60)  # Check every minute
```

### Always-Powered Configuration
```python
# For applications where GPS can remain powered continuously
gps = GPS(power_pin=None, rx_pin=16)  # No power control
gps.power_on()  # Manually keep powered on
```

## Position Data Format
Returns dictionary with:
- `latitude`: Formatted latitude with direction (e.g., "4124.8963 N")
- `longitude`: Formatted longitude with direction (e.g., "08151.6838 W")
- `altitude`: Altitude with units (e.g., "295.4 M")
- `timestamp`: UTC time (HHMMSS.SS format)
- `satellites`: Number of satellites used for fix
- `fix_quality`: GPS fix quality indicator
- `raw`: Original NMEA sentence for debugging

## Power Management Strategy
- **Default State**: Powered OFF for maximum energy savings
- **Activation**: Powers on only during position acquisition
- **Automatic Shutdown**: Guaranteed power-off after fix or timeout
- **Cache Optimization**: Reuses recent fixes to avoid power cycles

## Technical Details

### NMEA Processing
- Parses GGA (Global Positioning System Fix Data) sentences
- Validates fix quality before returning position
- Handles multiple sentence types in data stream

### Fix Acquisition
- Waits for valid 3D fix (quality indicator 1 or 2)
- Provides progress updates during acquisition
- Configurable timeout for different environments

### Error Handling
- Graceful timeout handling
- Invalid data filtering
- Exception protection during parsing

## Troubleshooting

### Common Issues
1. **No GPS Data**: Check wiring (GPS TX → ESP32 RX)
2. **Long Fix Times**: Ensure clear sky view for satellite acquisition
3. **Power Problems**: Verify power pin configuration and voltage levels
4. **Parsing Errors**: Check baud rate matches GPS module (typically 9600)

### Diagnostic Usage
```python
# Quick system check
gps.quick_status()  # Should show raw NMEA data if working
```

## Performance Notes
- **Cold Start**: 30-45 seconds typical for first fix
- **Warm Start**: 10-30 seconds with recent almanac data
- **Hot Start**: 1-5 seconds with current ephemeris data
- **Urban Areas**: Longer fix times due to signal obstruction

## Applications
- Battery-powered tracking devices
- Emergency location systems
- Environmental monitoring stations
- Asset tracking solutions
- Field research equipment

## Dependencies
- `machine.UART`
- `machine.Pin`
- `time`

## License
MicroPython GPS Driver with Power Management