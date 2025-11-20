# MQTT Client Setup for ESP32

## Overview
`mqtt_setup.py` provides a robust MQTT client implementation for ESP32 devices with automatic reconnection, unique device identification, and simplified message publishing. Designed for IoT applications requiring reliable cloud communication.

## Features
- **Automatic Device ID**: Unique client ID generation from MAC address
- **Connection Resilience**: 3-attempt retry logic with exponential backoff
- **Simplified Publishing**: Topic auto-formatting with device prefix
- **Connection Management**: Automatic disconnect handling and status tracking
- **Authentication Support**: Username/password authentication for secure brokers

## Installation
```python
from mqtt_setup import MQTTSetup
```

## Quick Start
```python
# Initialize MQTT connection
mqtt = MQTTSetup(server="192.168.1.100", port=1883)
sender = mqtt.setup_connection()

# Send sensor data
sender("sensors/temperature", "23.5")
sender("status/online", "device_active")
```

## API Reference

### Class: MQTTSetup

#### Constructor
```python
MQTTSetup(server, port=1883, username=None, password=None)
```
- `server`: MQTT broker IP address or hostname
- `port`: Broker port (default: 1883)
- `username`: Authentication username (optional)
- `password`: Authentication password (optional)

#### Key Methods

##### `setup_connection()`
Establishes MQTT connection with retry logic.
- **Returns**: Message sender function or fallback function
- **Retry Strategy**: 3 attempts with 2-second delays

##### `disconnect()`
Safely disconnects from MQTT broker.
- **Cleanup**: Updates connection status and closes socket

#### Internal Methods

##### `_create_sender_function()`
Creates pre-configured message sender with device ID.

## Message Sender Function

### Signature
```python
send_message(topic_suffix, message)
```

### Parameters
- `topic_suffix`: Topic path after device ID (e.g., "sensors/gas")
- `message`: Data to publish (automatically converted to string)

### Returns
- `True`: Message sent successfully
- `False`: Send failed or not connected

### Topic Structure
```
devices/{client_id}/{topic_suffix}
```
Example: `devices/esp32_a1b2c3d4/sensors/temperature`

## Configuration

### Default Settings
- **Keepalive**: 60 seconds
- **Retry Attempts**: 3
- **Retry Delay**: 2 seconds
- **Client ID Format**: `esp32_{mac_address}`

### Client ID Generation
```python
# Example: "esp32_a1b2c3d4e5f6"
client_id = "esp32_" + ubinascii.hexlify(machine.unique_id()).decode('utf-8')
```

## Usage Examples

### Basic Sensor Monitoring
```python
mqtt = MQTTSetup(server="mqtt.broker.com")
publish = mqtt.setup_connection()

# Publish sensor readings
publish("sensors/temperature", "25.3")
publish("sensors/humidity", "65.2")
publish("status/battery", "85")
```

### Secure Connection
```python
mqtt = MQTTSetup(
    server="secure.broker.com",
    port=8883,  # TLS port
    username="device_user",
    password="secure_password"
)
sender = mqtt.setup_connection()
```

### Error Handling
```python
sender = mqtt.setup_connection()

if sender("sensors/data", sensor_reading):
    print("Data sent successfully")
else:
    print("Failed to send data")
    # Implement fallback storage or retry logic
```

## Topic Convention Examples

### Sensor Data
```
devices/esp32_a1b2c3d4/sensors/temperature
devices/esp32_a1b2c3d4/sensors/gas
devices/esp32_a1b2c3d4/sensors/gps
devices/esp32_a1b2c3d4/sensors/pulse
```

### Device Status
```
devices/esp32_a1b2c3d4/status/online
devices/esp32_a1b2c3d4/status/battery
devices/esp32_a1b2c3d4/status/emergency
```

### Commands (for receiving)
```
devices/esp32_a1b2c3d4/commands/restart
devices/esp32_a1b2c3d4/commands/configuration
```

## Error Handling

### Connection Failures
- Automatic retry with 3 attempts
- Detailed error messages for debugging
- Graceful fallback to prevent system crashes

### Publish Failures
- Connection status validation before sending
- Automatic connection state updates on failure
- Returns boolean for success/failure tracking

### Common Error Scenarios
1. **Network Issues**: Retry logic with delays
2. **Broker Unavailable**: Fallback function prevents crashes
3. **Authentication Failed**: Clear error messages for configuration issues

## Integration Patterns

### With Sensor Classes
```python
# Combine with sensor reading classes
mqtt = MQTTSetup(server="broker.local")
publish = mqtt.setup_connection()

def send_sensor_data():
    temp = temp_sensor.getTemp()
    publish("sensors/temperature", temp)
    
    gas = gas_sensor.take_reading()
    publish("sensors/gas", gas['value'])
```

### Emergency Scenarios
```python
def emergency_handler():
    publish("status/emergency", "free_fall_detected")
    publish("sensors/gps", get_gps_location())
    publish("sensors/pulse", get_heart_rate())
```

## Performance Considerations

### Memory Usage
- Minimal object creation after setup
- Reusable sender function reduces overhead
- Efficient string handling for topic generation

### Network Efficiency
- Keepalive settings prevent unnecessary reconnections
- Batch messages where possible
- Connection reuse across multiple publishes

## Troubleshooting

### Common Issues
1. **Connection Timeout**: Check broker address and network connectivity
2. **Authentication Failed**: Verify username/password credentials
3. **Topic Rejected**: Ensure broker permissions allow publishing
4. **Memory Errors**: Monitor heap size in memory-constrained environments

### Debugging Tips
```python
# Enable detailed logging
import umqtt.simple
umqtt.simple.DEBUG = True

# Check connection status
print(f"Connected: {mqtt.is_connected}")
print(f"Client ID: {mqtt.client_id}")
```

## Dependencies
- `umqtt.simple` - MicroPython MQTT client
- `ubinascii` - MAC address encoding
- `machine` - Device unique ID access
- `time` - Retry delays

## Security Notes
- Avoid hardcoding credentials in source code
- Consider TLS/SSL for production environments
- Use unique client IDs to prevent conflicts
- Implement proper access control on broker

## License
MicroPython MQTT Client with Connection Management