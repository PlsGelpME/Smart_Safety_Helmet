# Main file description

## Overview
Main application file that orchestrates the complete emergency detection and monitoring system. Implements real-time sensor monitoring, emergency response protocols, and MQTT communication for a comprehensive safety monitoring solution.

## System Architecture

### Operational Modes
- **Normal Monitoring**: Periodic sensor readings with power management
- **Emergency Response**: Full emergency protocol with continuous alerts
- **Status Reporting**: Regular system health updates

## Configuration

### MQTT Broker Settings
```python
server_ip = "192.168.1.100"  # MQTT broker IP address
username = None              # Broker authentication username
password = None              # Broker authentication password
```

### Sensor Monitoring Intervals
```python
GPS_READ_INTERVAL = 300      # 5 minutes (high power consumption)
GAS_READ_INTERVAL = 3600     # 1 hour (stable environmental reading)
TEMP_READ_INTERVAL = 300     # 5 minutes (body temperature monitoring)
PULSE_READ_INTERVAL = 60     # 1 minute (frequent health checks)
STATUS_UPDATE_INTERVAL = 60  # 1 minute (system status updates)
```

## Emergency Detection System

### Trigger Conditions
- **Free-fall**: MPU6050 gyroscope interrupt (0.16g threshold)
- **Impact**: Force sensor interrupt (physical collision detection)
- **Non-resettable**: Emergency state requires manual power cycle

### Emergency Response Protocol
1. **Immediate Alert**: Continuous buzzer activation
2. **Location Acquisition**: Extended GPS timeout (20 seconds)
3. **Vital Signs**: Pulse oximeter data transmission
4. **Environmental Context**: Gas and temperature readings
5. **Status Updates**: Periodic emergency notifications

## Core Functions

### Interrupt Handlers
```python
def free_fall_handler(pin):
    # Triggers on MPU6050 free-fall detection
    # Sets global emergency state

def impact_handler(pin):
    # Triggers on force sensor impact detection  
    # Sets global emergency state
```

### Emergency Functions
```python
def activate_buzzer():
    # Continuous buzzer activation until power cycle
    # Non-resettable alert system

def send_emergency_data():
    # Comprehensive emergency data package
    # GPS location, vital signs, environmental data
```

## Main Loop Operation

### Emergency Mode (Highest Priority)
```python
if emergency_active:
    # Execute emergency protocol once
    # Continuous buzzer activation
    # Periodic status updates every 30 seconds
```

### Normal Operation Mode
```python
else:
    # GPS: 5-minute intervals with position caching
    # Gas Sensor: 1-hour intervals with power management
    # Temperature: 5-minute intervals with threshold checking
    # Pulse Oximeter: 1-minute intervals for health monitoring
    # Status: 1-minute system health updates
```

## Sensor Integration

### GPS Monitoring
- **Interval**: 5 minutes
- **Power Management**: Cached positions (5-minute validity)
- **Emergency**: Extended 20-second timeout

### Gas Sensor Monitoring
- **Interval**: 1 hour
- **Power Management**: Conditional monitoring with auto power-off
- **Smart Scheduling**: Operating hours and hourly checks

### Temperature Monitoring
- **Interval**: 5 minutes
- **Alert Threshold**: Configurable temperature limits
- **Multi-unit Support**: Celsius, Fahrenheit, Kelvin

### Pulse Oximeter Monitoring
- **Interval**: 1 minute
- **Health Metrics**: Heart rate (BPM) and blood oxygen (SpO2)
- **Real-time Tracking**: Continuous health monitoring

## Message Publishing

### Normal Operation Messages
- `sensors/gps`: Location coordinates and altitude
- `sensors/gas`: Gas concentration with status
- `sensors/temperature`: Temperature readings
- `sensors/pulse`: Heart rate and SpO2 data
- `status`: System operational status

### Emergency Messages
- `status/emergency`: Initial emergency notification
- `status/emergency_active`: Periodic emergency updates
- All sensor data with emergency context

## Power Management Strategy

### Efficient Operation
- **1-second loop delay**: Reduces CPU usage
- **Sensor power cycling**: GPS and gas sensor auto power-off
- **Cached data**: GPS position reuse to minimize activations
- **Conditional monitoring**: Gas sensor hourly checks only

### Emergency Power Usage
- **Maximum power**: All sensors active during emergencies
- **Continuous operation**: Buzzer and communications active
- **Extended timeouts**: GPS given more time for fix acquisition

## System States

### Initialization
1. MQTT connection setup with retry logic
2. Sensor object initialization
3. Interrupt handler configuration
4. Global variable setup

### Normal Operation
- Periodic sensor readings
- Power-efficient monitoring
- Regular status updates
- Emergency detection readiness

### Emergency State
- Non-resettable emergency flag
- Comprehensive data collection
- Continuous alert activation
- Manual reset requirement

## Usage Examples

### Basic Operation
```python
# System runs automatically after initialization
# Normal monitoring with configured intervals
# Automatic emergency detection and response
```

### Custom Configuration
```python
# Adjust monitoring intervals based on application
GPS_READ_INTERVAL = 600    # 10 minutes for battery saving
PULSE_READ_INTERVAL = 30   # 30 seconds for critical care
```

## Error Handling

### Connection Resilience
- MQTT connection retries (3 attempts)
- Graceful degradation on communication failure
- Continued local operation during network issues

### Sensor Fault Tolerance
- Conditional sensor checks (`if 'sensor' in globals()`)
- Individual sensor failure doesn't crash system
- Error reporting through status messages

## Performance Characteristics

### Response Time
- **Emergency Detection**: <1 second (hardware interrupts)
- **GPS Acquisition**: 30-45 seconds typical
- **Message Publishing**: Immediate with MQTT connection

### Resource Usage
- **Memory**: Efficient garbage collection enabled
- **CPU**: 1-second sleep intervals reduce usage
- **Network**: Optimized message frequency

## Integration Requirements

### Required Modules
- `mqtt_setup.py`: MQTT communication handling
- `message_creator.py`: Sensor data formatting
- Sensor driver classes (`__gyro__`, `__GPS__`, etc.)

### Hardware Dependencies
- ESP32 with WiFi capability
- All configured sensors and peripherals
- Proper pin assignments from main configuration

## Troubleshooting

### Common Issues
1. **MQTT Connection Fails**: Check broker IP and network connectivity
2. **GPS No Fix**: Ensure clear sky view and adequate timeout
3. **Sensor Not Detected**: Verify pin assignments and power
4. **Emergency State Stuck**: Requires manual power cycle

### Debugging Features
- Detailed print statements for system states
- Individual sensor status reporting
- Connection success/failure notifications

## Safety Features

### Non-resettable Emergency
- Manual power cycle required after emergency
- Prevents accidental emergency state clearance
- Ensures continuous alert until intervention

### Comprehensive Data Collection
- Location, vital signs, and environmental data
- Multiple data points for emergency response
- Timestamped information for analysis

## Application Scenarios

### Healthcare Monitoring
- Elderly fall detection with location tracking
- Continuous vital signs monitoring
- Emergency alert with comprehensive context

### Industrial Safety
- Worker fall and impact detection
- Environmental hazard monitoring
- Remote location emergency response

### Personal Safety
- Adventure sports safety monitoring
- Remote area emergency communication
- Automated emergency notification system

## License
Emergency Detection System - Main Application Controller