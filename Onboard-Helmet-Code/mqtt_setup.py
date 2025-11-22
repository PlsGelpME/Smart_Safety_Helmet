# mqtt_setup.py - MQTT connection setup and basic sender
from umqttsimple import MQTTClient
import ubinascii
import machine
import time

class MQTTSetup:
    """
    MQTT client setup class for ESP32 devices
    Handles connection to MQTT broker and message publishing
    """
    def __init__(self, server, port=1883, username=None, password=None):
        """
        Setup MQTT connection and return a sender function
        
        Args:
            server: MQTT broker server address
            port: MQTT broker port (default: 1883)
            username: MQTT authentication username (optional)
            password: MQTT authentication password (optional)
        """
        # Generate unique client ID from MAC address for device identification
        self.client_id = "esp32_" + ubinascii.hexlify(machine.unique_id()).decode('utf-8')
        self.server = server    # MQTT broker server address
        self.port = port        # MQTT broker port number
        self.username = username  # Authentication username
        self.password = password  # Authentication password
        
        # Connection state variables
        self.client = None      # MQTT client instance
        self.is_connected = False  # Connection status flag
        
        print(f"MQTT Setup: Client ID {self.client_id}")
    
    def setup_connection(self):
        """Setup MQTT connection with 3 retries and return sender function"""
        max_retries = 3  # Maximum number of connection attempts
        
        for attempt in range(max_retries):
            try:
                # Create MQTT client instance with connection parameters
                self.client = MQTTClient(
                    self.client_id,
                    self.server,
                    port=self.port,
                    user=self.username,
                    password=self.password,
                    keepalive=60  # Keepalive interval in seconds
                )
                
                # Establish connection to MQTT broker
                self.client.connect()
                self.is_connected = True
                print(f"MQTT connected to {self.server}:{self.port}")
                
                # Return the sender function with client_id baked in
                return self._create_sender_function()
                
            except Exception as e:
                # Handle connection failures with retry logic
                print(f"MQTT connection failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait 2 seconds before retry
        
        print("MQTT connection failed after 3 attempts")
        # Return a fallback function that does nothing when connection fails
        return lambda topic, message: False
    
    def _create_sender_function(self):
        """Create and return sender function with client_id as default"""
        def send_message(topic_suffix, message):
            """
            Send message to MQTT broker
            
            Args:
                topic_suffix: Topic after client_id (e.g., "gas", "gps/location")
                message: String message to send
                
            Returns:
                bool: True if message sent successfully, False otherwise
            """
            # Check if MQTT connection is active
            if not self.is_connected or not self.client:
                print("MQTT not connected")
                return False
            
            try:
                # Auto-prepend client_id to topic for device-specific topics
                full_topic = f"devices/{self.client_id}/{topic_suffix}"
                # Publish message to MQTT broker
                self.client.publish(full_topic, str(message))
                print(f"Sent to {full_topic}: {message}")
                return True
            except Exception as e:
                # Handle publish failures and update connection status
                print(f"Send failed: {e}")
                self.is_connected = False
                return False
        
        return send_message
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client and self.is_connected:
            try:
                self.client.disconnect()  # Close MQTT connection
                self.is_connected = False  # Update connection status
                print("MQTT disconnected")
            except Exception as e:
                print(f"Error disconnecting: {e}")