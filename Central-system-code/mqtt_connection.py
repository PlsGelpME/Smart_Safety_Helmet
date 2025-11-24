# mqtt_connection.py - MQTT connection management
import paho.mqtt.client as mqtt
import logging
import time

class MQTTConnection:
    def __init__(self, broker_host='localhost', broker_port=1883, client_id=''):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.client = None
        self.connected = False
        self.on_message_callback = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('MQTTConnection')
        
    def set_message_callback(self, callback):
        """Set the callback function for incoming messages"""
        self.on_message_callback = callback
        
    def on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            self.connected = True
            self.logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
        else:
            self.connected = False
            self.logger.error(f"Connection failed with code: {rc}")
            
    def on_disconnect(self, client, userdata, rc, properties=None):
        """Callback when disconnected from MQTT broker"""
        self.connected = False
        if rc != 0:
            self.logger.warning("Unexpected disconnection from MQTT broker")
        else:
            self.logger.info("Disconnected from MQTT broker")
            
    def on_message(self, client, userdata, msg):
        """Callback when message is received"""
        if self.on_message_callback:
            self.on_message_callback(msg.topic, msg.payload.decode())
        else:
            self.logger.warning("No message callback set")
            
    def connect(self):
        """Connect to MQTT broker"""
        try:
            # Create client with callback API version for paho-mqtt 2.0+
            self.client = mqtt.Client(
                client_id=self.client_id,
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2
            )
            
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            self.logger.info("MQTT connection initiated")
            
            # Wait a moment for connection to establish
            time.sleep(2)
            return self.connected
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {e}")
            return False

    # Alternative method for older paho-mqtt versions
    def connect_legacy(self):
        """Alternative connect method for older paho-mqtt versions"""
        try:
            # Try without callback API version (for older versions)
            self.client = mqtt.Client(client_id=self.client_id)
            
            # Use legacy callbacks without properties parameter
            def legacy_on_connect(client, userdata, flags, rc):
                if rc == 0:
                    self.connected = True
                    self.logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
                else:
                    self.connected = False
                    self.logger.error(f"Connection failed with code: {rc}")
            
            def legacy_on_disconnect(client, userdata, rc):
                self.connected = False
                if rc != 0:
                    self.logger.warning("Unexpected disconnection from MQTT broker")
                else:
                    self.logger.info("Disconnected from MQTT broker")
            
            self.client.on_connect = legacy_on_connect
            self.client.on_disconnect = legacy_on_disconnect
            self.client.on_message = self.on_message
            
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            self.logger.info("MQTT connection initiated (legacy mode)")
            
            time.sleep(2)
            return self.connected
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker (legacy): {e}")
            return False
            
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            self.logger.info("Disconnected from MQTT broker")
            
    def subscribe(self, topic):
        """Subscribe to MQTT topic"""
        if self.client and self.connected:
            result = self.client.subscribe(topic)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info(f"Subscribed to topic: {topic}")
                return True
            else:
                self.logger.error(f"Failed to subscribe to {topic}: {result[0]}")
                return False
        else:
            self.logger.warning("Cannot subscribe - not connected to broker")
            return False
            
    def publish(self, topic, message):
        """Publish message to MQTT topic"""
        if self.client and self.connected:
            result = self.client.publish(topic, message)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug(f"Published to {topic}: {message}")
                return True
            else:
                self.logger.error(f"Failed to publish message: {result.rc}")
                return False
        else:
            self.logger.warning("Cannot publish - not connected to broker")
            return False
            
    def is_connected(self):
        """Check if connected to MQTT broker"""
        return self.connected
