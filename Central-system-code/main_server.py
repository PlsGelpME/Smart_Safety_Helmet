# main_server.py - Main MQTT server application with fallback
import time
import signal
import sys
import json
import os
from datetime import datetime
from mqtt_connection import MQTTConnection
from data_reader import DataReader

class MQTTServer:
    def __init__(self, broker_host='localhost', broker_port=1883, client_id='mqtt_server'):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.mqtt_connection = None
        self.data_reader = None
        self.running = False
        self.start_time = time.time()
        
    def setup(self):
        """Setup MQTT connection and data reader"""
        print("Setting up MQTT Server...")
        print(f"Broker: {self.broker_host}:{self.broker_port}")
        print(f"Client ID: {self.client_id}")
        
        # Initialize data reader
        self.data_reader = DataReader()
        self.data_reader.setup_logging()
        
        # Initialize MQTT connection
        self.mqtt_connection = MQTTConnection(
            broker_host=self.broker_host,
            broker_port=self.broker_port,
            client_id=self.client_id
        )
        
        # Set message callback
        self.mqtt_connection.set_message_callback(self.on_mqtt_message)
        
    def connect_to_broker(self):
        """Connect to broker with fallback for version issues"""
        print("Attempting to connect to MQTT broker...")
        
        # First try the standard connection (for paho-mqtt 2.0+)
        if self.mqtt_connection.connect():
            return True
        
        # If that fails, try legacy connection (for older versions)
        print("Standard connection failed, trying legacy mode...")
        if self.mqtt_connection.connect_legacy():
            return True
        
        print("All connection attempts failed")
        return False
        
    def on_mqtt_message(self, topic, payload):
        """Callback for MQTT messages"""
        try:
            # Extract client_id from topic (devices/esp32_abc123/sensors/gas)
            parts = topic.split('/')
            if len(parts) >= 2 and parts[0] == 'devices':
                client_id = parts[1]
            else:
                client_id = 'unknown_client'
                
            print(f"Received message from {client_id} on topic: {topic}")
            self.data_reader.process_message(client_id, payload)
            
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
        
    def start(self):
        """Start the MQTT server"""
        print("\n" + "="*50)
        print("Starting MQTT Server")
        print("="*50)
        print(f"Broker Host: {self.broker_host}")
        print(f"Broker Port: {self.broker_port}")
        print(f"Client ID: {self.client_id}")
        print("Press Ctrl+C to stop the server")
        print("="*50)
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Connect to MQTT broker with fallback
        if not self.connect_to_broker():
            print("Failed to connect to MQTT broker!")
            print("\nTroubleshooting steps:")
            print("1. Check if MQTT broker is running: mosquitto -v")
            print("2. Install/update paho-mqtt: pip install --upgrade paho-mqtt")
            print("3. Try different paho-mqtt version: pip install paho-mqtt==1.6.1")
            return
        
        # Subscribe to ESP32 topics
        topics = [
            "devices/+/sensors/gas",
            "devices/+/sensors/gps", 
            "devices/+/sensors/temperature",
            "devices/+/sensors/pulse",
            "devices/+/status",
            "devices/+/+/+"  # Catch-all for any device topics
        ]
        
        print("\nSubscribing to topics:")
        for topic in topics:
            if self.mqtt_connection.subscribe(topic):
                print(f"{topic}")
            else:
                print(f"{topic}")
        
        self.running = True
        print("\nServer started successfully!")
        print("Waiting for ESP32 messages...\n")
        
        # Main server loop
        try:
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.stop()
            
    def stop(self):
        """Stop the MQTT server"""
        print("\nStopping MQTT Server...")
        self.running = False
        
        if self.mqtt_connection:
            self.mqtt_connection.disconnect()
            
        if self.data_reader:
            self.data_reader.close_logs()
            
        print("Server stopped successfully")
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)

def main():
    # Configuration for local development
    BROKER_HOST = 'localhost'    # or '127.0.0.1'
    BROKER_PORT = 1883           # Default MQTT port
    CLIENT_ID = 'python_server'  # Can be any unique name
    
    # Create and start server
    server = MQTTServer(
        broker_host=BROKER_HOST,
        broker_port=BROKER_PORT, 
        client_id=CLIENT_ID
    )
    
    server.setup()
    server.start()

if __name__ == "__main__":
    main()
