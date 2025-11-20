# message_creator.py - Create sensor messages and send them
import ujson
import time

class MessageCreator:
    """
    Message creation and publishing class for sensor data
    Formats sensor data as JSON and publishes via MQTT
    """
    def __init__(self, sender_function):
        """
        Create sensor messages and send using provided sender function
        
        Args:
            sender_function: Function that handles MQTT message publishing
        """
        self.send = sender_function  # Store the MQTT sender function
        print("Message Creator initialized")
    
    def publish_gas(self, value, status, unit="adc"):
        """
        Publish gas sensor data to MQTT
        
        Args:
            value: Gas sensor reading value
            status: Status of gas sensor (e.g., "normal", "alert")
            unit: Unit of measurement (default: "adc")
            
        Returns:
            bool: Result from sender function (True if sent successfully)
        """
        # Create JSON message with gas sensor data
        message = ujson.dumps({
            "sensor": "gas",        # Sensor type identifier
            "value": value,         # Sensor reading value
            "status": status,       # Operational status
            "unit": unit,           # Measurement unit
            "timestamp": time.time()  # Current timestamp
        })
        # Send to sensors/gas topic via MQTT
        return self.send("sensors/gas", message)
    
    def publish_gps(self, latitude, longitude, altitude):
        """
        Publish GPS location data to MQTT
        
        Args:
            latitude: GPS latitude coordinate
            longitude: GPS longitude coordinate  
            altitude: GPS altitude value
            
        Returns:
            bool: Result from sender function (True if sent successfully)
        """
        # Create JSON message with GPS location data
        message = ujson.dumps({
            "sensor": "gps",           # Sensor type identifier
            "latitude": latitude,      # Latitude coordinate
            "longitude": longitude,    # Longitude coordinate
            "altitude": altitude,      # Altitude value
            "timestamp": time.time()   # Current timestamp
        })
        # Send to sensors/gps topic via MQTT
        return self.send("sensors/gps", message)
    
    def publish_pulse(self, heart_rate, spo2):
        """
        Publish pulse oximeter data to MQTT
        
        Args:
            heart_rate: Heart rate measurement in BPM
            spo2: Blood oxygen saturation percentage
            
        Returns:
            bool: Result from sender function (True if sent successfully)
        """
        # Create JSON message with pulse oximeter data
        message = ujson.dumps({
            "sensor": "pulse_oximeter",  # Sensor type identifier
            "heart_rate": heart_rate,    # Heart rate in beats per minute
            "spo2": spo2,                # Blood oxygen saturation %
            "timestamp": time.time()     # Current timestamp
        })
        # Send to sensors/pulse topic via MQTT
        return self.send("sensors/pulse", message)
    
    def publish_temperature(self, temperature, unit="celsius"):
        """
        Publish temperature data to MQTT
        
        Args:
            temperature: Temperature reading value
            unit: Temperature unit (default: "celsius")
            
        Returns:
            bool: Result from sender function (True if sent successfully)
        """
        # Create JSON message with temperature data
        message = ujson.dumps({
            "sensor": "temperature",   # Sensor type identifier
            "value": temperature,      # Temperature value
            "unit": unit,              # Temperature unit
            "timestamp": time.time()   # Current timestamp
        })
        # Send to sensors/temperature topic via MQTT
        return self.send("sensors/temperature", message)
    
    def publish_status(self, status, message=None):
        """
        Publish device status information to MQTT
        
        Args:
            status: Device status (e.g., "online", "error", "warning")
            message: Optional descriptive message (default: None)
            
        Returns:
            bool: Result from sender function (True if sent successfully)
        """
        # Create base status data structure
        data = {
            "type": "status",        # Message type identifier
            "status": status,        # Device status
            "timestamp": time.time() # Current timestamp
        }
        
        # Add optional message if provided
        if message:
            data["message"] = message
        
        # Convert to JSON format
        json_message = ujson.dumps(data)
        # Send to status topic via MQTT
        return self.send("status", json_message)