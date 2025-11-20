# Sensor Message Creator for MQTT

## Overview
`message_creator.py` provides standardized JSON message formatting and publishing for IoT sensor data. Creates consistent, timestamped JSON messages for various sensor types and handles MQTT communication through a provided sender function.

## Features
- **Standardized JSON Format**: Consistent message structure across all sensors
- **Automatic Timestamping**: Unix timestamp included in every message
- **Sensor Type Identification**: Clear sensor identification in each message
- **Flexible Status Reporting**: Configurable status messages with optional descriptions
- **MQTT Integration**: Seamless integration with MQTT publisher functions

## Installation
```python
from message_creator import MessageCreator
```

## Quick Start
```python
# Initialize with MQTT sender function
message_sender = MessageCreator(mqtt_sender_function)

# Publish sensor data
message_sender.publish_temperature(25.3)
message_sender.publish_gps(40.7128, -74.0060, 10.5)
message_sender.publish_status("online", "System operational")
```

## API Reference

### Class: MessageCreator

#### Constructor
```python
MessageCreator(sender_function)
```
- `sender_function`: MQTT message publishing function (from MQTTSetup)

#### Sensor Publishing Methods

##### `publish_gas(value, status, unit="adc")`
Publishes gas sensor readings.
- `value`: Gas concentration reading
- `status`: "normal", "warning", or "alarm"
- `unit`: Measurement unit (default: "adc")

##### `publish_gps(latitude, longitude, altitude)`
Publishes GPS location data.
- `latitude`: Latitude coordinate
- `longitude`: Longitude coordinate
- `altitude`: Altitude value

##### `publish_pulse(heart_rate, spo2)`
Publishes pulse oximeter data.
- `heart_rate`: Heart rate in BPM
- `spo2`: Blood oxygen saturation percentage

##### `publish_temperature(temperature, unit="celsius")`
Publishes temperature readings.
- `temperature`: Temperature value
- `unit`: Temperature unit (default: "celsius")

##### `publish_status(status, message=None)`
Publishes device status information.
- `status`: Status type ("online", "error", "warning", "emergency")
- `message`: Optional descriptive message

## Message Formats

### Gas Sensor Message
```json
{
  "sensor": "gas",
  "value": 1250,
  "status": "normal",
  "unit": "adc",
  "timestamp": 1635789200.123456
}
```

### GPS Location Message
```json
{
  "sensor": "gps",
  "latitude": "40.7128 N",
  "longitude": "74.0060 W", 
  "altitude": "10.5 M",
  "timestamp": 1635789200.123456
}
```

### Pulse Oximeter Message
```json
{
  "sensor": "pulse_oximeter",
  "heart_rate": 72,
  "spo2": 98,
  "timestamp": 1635789200.123456
}
```

### Temperature Message
```json
{
  "sensor": "temperature",
  "value": 36.5,
  "unit": "celsius",
  "timestamp": 1635789200.123456
}
```

### Status Message
```json
{
  "type": "status",
  "status": "online",
  "message": "System operational",
  "timestamp": 1635789200.123456
}
```

## Usage Examples

### Complete Sensor System
```python
# Initialize message creator
message_sender = MessageCreator(mqtt_publisher)

# Periodic sensor readings
def read_and_publish_sensors():
    # Temperature
    temp = temp_sensor.getTemp(unit=1)
    message_sender.publish_temperature(temp)
    
    # GPS (if available)
    location = gps.get_position_cached()
    if location:
        message_sender.publish_gps(
            location['latitude'], 
            location['longitude'], 
            location['altitude']
        )
    
    # Pulse oximeter
    pulse_data = pulse_sensor.get_sensor_data()
    if pulse_data:
        message_sender.publish_pulse(
            pulse_data['heart_rate'],
            pulse_data['spo2']
        )
    
    # System status
    message_sender.publish_status("active", "Normal operation")
```

### Emergency Scenarios
```python
def handle_emergency():
    # Send emergency status
    message_sender.publish_status("emergency", "Free-fall detected")
    
    # Send critical sensor data
    message_sender.publish_gps(current_lat, current_lon, current_alt)
    message_sender.publish_pulse(current_hr, current_spo2)
    
    # Environmental context
    message_sender.publish_temperature(current_temp)
    message_sender.publish_gas(gas_reading, "alarm")
```

### Error Handling
```python
def safe_publish():
    try:
        if message_sender.publish_temperature(25.5):
            print("Temperature published successfully")
        else:
            print("Failed to publish temperature")
            # Implement retry or local storage
    except Exception as e:
        print(f"Publish error: {e}")
```

## Topic Structure

All messages are sent to device-specific topics:
```
devices/{client_id}/sensors/{sensor_type}
devices/{client_id}/status
```

Example topics:
- `devices/esp32_a1b2c3d4/sensors/temperature`
- `devices/esp32_a1b2c3d4/sensors/gps`
- `devices/esp32_a1b2c3d4/sensors/pulse`
- `devices/esp32_a1b2c3d4/sensors/gas`
- `devices/esp32_a1b2c3d4/status`

## Integration Patterns

### With Main Application Loop
```python
# In main application
message_creator = MessageCreator(sender_function)

while True:
    # Read and publish all sensors
    publish_sensor_data(message_creator)
    
    # Handle emergency conditions
    if emergency_detected:
        publish_emergency_data(message_creator)
    
    time.sleep(update_interval)
```

### Batch Publishing
```python
def publish_all_sensors():
    results = []
    results.append(message_creator.publish_temperature(get_temperature()))
    results.append(message_creator.publish_gas(get_gas_reading(), "normal"))
    results.append(message_creator.publish_status("active"))
    
    successful = sum(results)
    print(f"Published {successful}/3 messages successfully")
```

## Error Handling and Reliability

### Return Values
- All methods return `True` on successful publish
- Returns `False` if MQTT sender fails
- Allows for success tracking and retry logic

### Timestamp Consistency
- Uses `time.time()` for consistent Unix timestamps
- All messages include timestamp for temporal analysis
- Enables time-series data processing on server side

## Performance Considerations

### Memory Usage
- JSON serialization uses ujson for efficiency
- Minimal object creation in message methods
- Reuse of sender function reduces overhead

### Network Efficiency
- Compact JSON formatting reduces packet size
- Consistent structure enables efficient parsing
- Batch operations where possible

## Troubleshooting

### Common Issues
1. **JSON Serialization Failures**: Ensure all data types are serializable
2. **MQTT Connection Drops**: Check sender function connectivity
3. **Missing Timestamps**: Verify system time is set correctly
4. **Topic Permission Errors**: Confirm broker topic permissions

### Debugging
```python
# Check individual publish results
success = message_creator.publish_temperature(25.5)
print(f"Publish successful: {success}")

# Verify JSON output
test_message = ujson.dumps({
    "sensor": "test",
    "value": 123,
    "timestamp": time.time()
})
print(f"JSON: {test_message}")
```

## Dependencies
- `ujson` - Efficient JSON serialization
- `time` - Timestamp generation

## Integration Requirements
- Requires MQTT sender function from `MQTTSetup` class
- Compatible with any function matching `send(topic, message)` signature
- Expects boolean return value for success tracking

## Best Practices

### Message Consistency
- Use consistent status values across system
- Maintain uniform timestamp format
- Follow established sensor naming conventions

### Error Recovery
- Implement retry logic for failed publishes
- Consider local storage for critical data
- Monitor publish success rates

## License
MicroPython Sensor Message Formatting and Publishing Library