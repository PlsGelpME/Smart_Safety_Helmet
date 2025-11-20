# mqtt_receiver.py - High-performance MQTT Message Receiver with Buffer
import paho.mqtt.client as mqtt
import json
import threading
import queue
import time
import logging
from collections import deque
from datetime import datetime

class MQTTReceiver:
    """
    High-performance MQTT message receiver with message buffering
    Handles 25-30 message buffer with configurable processing
    """
    
    def __init__(self, broker_host="localhost", broker_port=1883, buffer_size=30):
        """
        Initialize MQTT receiver with message buffering
        
        Args:
            broker_host: MQTT broker hostname/IP
            broker_port: MQTT broker port
            buffer_size: Maximum number of messages to buffer (default: 30)
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.buffer_size = buffer_size
        
        # Message buffer using deque for efficient FIFO operations
        self.message_buffer = deque(maxlen=buffer_size)
        self.buffer_lock = threading.Lock()
        
        # Processing queue for worker thread
        self.processing_queue = queue.Queue(maxsize=buffer_size * 2)
        
        # Statistics
        self.stats = {
            'messages_received': 0,
            'messages_processed': 0,
            'buffer_overflows': 0,
            'last_message_time': None
        }
        self.stats_lock = threading.Lock()
        
        # Control flags
        self.is_running = False
        self.is_connected = False
        
        # Initialize MQTT client
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Message handlers registry
        self.message_handlers = {
            'sensors': {},
            'status': {}
        }
        
    def _setup_logging(self):
        """Setup logging configuration"""
        logger = logging.getLogger('MQTTReceiver')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # File handler
            file_handler = logging.FileHandler('mqtt_receiver.log')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.is_connected = True
            self.logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
        else:
            self.logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """
        MQTT message callback - handles incoming messages with buffering
        """
        try:
            message_data = {
                'topic': msg.topic,
                'payload': msg.payload.decode(),
                'timestamp': datetime.now(),
                'qos': msg.qos,
                'retained': msg.retain
            }
            
            # Parse JSON payload if possible
            try:
                message_data['parsed_payload'] = json.loads(message_data['payload'])
            except json.JSONDecodeError:
                message_data['parsed_payload'] = None
            
            # Add to buffer with thread safety
            with self.buffer_lock:
                if len(self.message_buffer) >= self.buffer_size:
                    # Remove oldest message if buffer is full
                    self.message_buffer.popleft()
                    with self.stats_lock:
                        self.stats['buffer_overflows'] += 1
                
                self.message_buffer.append(message_data)
            
            # Add to processing queue
            try:
                self.processing_queue.put(message_data, block=False, timeout=0.1)
            except queue.Full:
                self.logger.warning("Processing queue full, message may be delayed")
            
            # Update statistics
            with self.stats_lock:
                self.stats['messages_received'] += 1
                self.stats['last_message_time'] = datetime.now()
            
            self.logger.debug(f"Buffered message: {msg.topic}")
            
        except Exception as e:
            self.logger.error(f"Error processing incoming message: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.is_connected = False
        if rc != 0:
            self.logger.warning(f"Unexpected MQTT disconnection. Return code: {rc}")
        else:
            self.logger.info("Disconnected from MQTT broker")
    
    def _message_processor(self):
        """Background thread for processing messages from the queue"""
        self.logger.info("Message processor thread started")
        
        while self.is_running:
            try:
                # Wait for message with timeout to allow graceful shutdown
                message_data = self.processing_queue.get(timeout=1.0)
                
                if message_data is None:  # Shutdown signal
                    break
                
                # Process the message
                self._process_single_message(message_data)
                
                # Update statistics
                with self.stats_lock:
                    self.stats['messages_processed'] += 1
                
                # Mark task as done
                self.processing_queue.task_done()
                
            except queue.Empty:
                continue  # No messages, continue waiting
            except Exception as e:
                self.logger.error(f"Error in message processor: {e}")
        
        self.logger.info("Message processor thread stopped")
    
    def _process_single_message(self, message_data):
        """
        Process a single message from the queue
        Routes to appropriate handler based on topic
        """
        try:
            topic_parts = message_data['topic'].split('/')
            
            if len(topic_parts) >= 4 and topic_parts[0] == 'devices':
                device_id = topic_parts[1]
                message_type = topic_parts[2]  # 'sensors' or 'status'
                sub_type = topic_parts[3]      # sensor type or status type
                
                # Route to registered handler
                if message_type in self.message_handlers:
                    handler_key = f"{device_id}/{sub_type}"
                    
                    # Try exact match first
                    if handler_key in self.message_handlers[message_type]:
                        for handler in self.message_handlers[message_type][handler_key]:
                            handler(device_id, sub_type, message_data['parsed_payload'], message_data)
                    
                    # Try wildcard handlers
                    if '*' in self.message_handlers[message_type]:
                        for handler in self.message_handlers[message_type]['*']:
                            handler(device_id, sub_type, message_data['parsed_payload'], message_data)
                    
                    # Try device-only wildcard
                    device_wildcard = f"{device_id}/*"
                    if device_wildcard in self.message_handlers[message_type]:
                        for handler in self.message_handlers[message_type][device_wildcard]:
                            handler(device_id, sub_type, message_data['parsed_payload'], message_data)
                
                self.logger.debug(f"Processed message: {message_data['topic']}")
                
        except Exception as e:
            self.logger.error(f"Error routing message: {e}")
    
    def register_handler(self, message_type, handler_key, handler_function):
        """
        Register a handler function for specific message types
        
        Args:
            message_type: 'sensors' or 'status'
            handler_key: Format 'device_id/sensor_type' or use wildcards:
                        - 'device123/temperature' (exact match)
                        - 'device123/*' (all sensors for device123)
                        - '*/temperature' (temperature for all devices)
                        - '*' (all messages of this type)
            handler_function: Function to call when message matches
        """
        if message_type not in self.message_handlers:
            self.logger.warning(f"Unknown message type: {message_type}")
            return False
        
        if handler_key not in self.message_handlers[message_type]:
            self.message_handlers[message_type][handler_key] = []
        
        self.message_handlers[message_type][handler_key].append(handler_function)
        self.logger.info(f"Registered handler for {message_type}/{handler_key}")
        return True
    
    def unregister_handler(self, message_type, handler_key, handler_function=None):
        """
        Unregister handler function(s)
        
        Args:
            message_type: 'sensors' or 'status'
            handler_key: Handler key to remove
            handler_function: Specific function to remove (None removes all)
        """
        if (message_type in self.message_handlers and 
            handler_key in self.message_handlers[message_type]):
            
            if handler_function is None:
                # Remove all handlers for this key
                del self.message_handlers[message_type][handler_key]
                self.logger.info(f"Removed all handlers for {message_type}/{handler_key}")
            else:
                # Remove specific handler
                handlers = self.message_handlers[message_type][handler_key]
                if handler_function in handlers:
                    handlers.remove(handler_function)
                    self.logger.info(f"Removed specific handler for {message_type}/{handler_key}")
                
                # Clean up empty handler lists
                if not handlers:
                    del self.message_handlers[message_type][handler_key]
    
    def subscribe(self, topic_pattern):
        """
        Subscribe to MQTT topic pattern
        
        Args:
            topic_pattern: MQTT topic pattern to subscribe to
        """
        if self.is_connected:
            self.client.subscribe(topic_pattern)
            self.logger.info(f"Subscribed to topic: {topic_pattern}")
        else:
            self.logger.warning("Not connected, subscription queued")
            # Topic will be subscribed on connection
    
    def get_buffer_stats(self):
        """Get current buffer statistics"""
        with self.buffer_lock:
            buffer_size = len(self.message_buffer)
            buffer_contents = list(self.message_buffer)
        
        with self.stats_lock:
            stats = self.stats.copy()
        
        stats['current_buffer_size'] = buffer_size
        stats['buffer_capacity'] = self.buffer_size
        stats['processing_queue_size'] = self.processing_queue.qsize()
        
        return stats
    
    def get_recent_messages(self, count=10):
        """
        Get most recent messages from buffer
        
        Args:
            count: Number of recent messages to return
            
        Returns:
            list: Recent messages (newest first)
        """
        with self.buffer_lock:
            # Return newest messages first
            recent_messages = list(self.message_buffer)[-count:]
            return recent_messages[::-1]  # Reverse to show newest first
    
    def clear_buffer(self):
        """Clear the message buffer"""
        with self.buffer_lock:
            self.message_buffer.clear()
        self.logger.info("Message buffer cleared")
    
    def start(self):
        """Start the MQTT receiver and processing threads"""
        if self.is_running:
            self.logger.warning("Receiver is already running")
            return
        
        self.is_running = True
        
        try:
            # Connect to MQTT broker
            self.logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            
            # Subscribe to default topics
            self.client.subscribe("devices/+/sensors/+")
            self.client.subscribe("devices/+/status/+")
            
            # Start MQTT network loop in background thread
            self.client.loop_start()
            
            # Start message processor thread
            self.processor_thread = threading.Thread(
                target=self._message_processor,
                daemon=True,
                name="MessageProcessor"
            )
            self.processor_thread.start()
            
            self.logger.info("MQTT receiver started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start MQTT receiver: {e}")
            self.is_running = False
            raise
    
    def stop(self):
        """Stop the MQTT receiver and processing threads"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping MQTT receiver...")
        self.is_running = False
        
        # Stop MQTT client
        self.client.loop_stop()
        self.client.disconnect()
        
        # Signal processor thread to stop
        try:
            self.processing_queue.put(None, block=False)
        except:
            pass
        
        # Wait for processor thread to finish
        if hasattr(self, 'processor_thread') and self.processor_thread.is_alive():
            self.processor_thread.join(timeout=5.0)
        
        self.logger.info("MQTT receiver stopped")
    
    def wait_for_processing(self, timeout=None):
        """
        Wait for all queued messages to be processed
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if all messages processed, False if timeout
        """
        try:
            return self.processing_queue.join(timeout=timeout)
        except Exception as e:
            self.logger.error(f"Error waiting for processing: {e}")
            return False

# Example usage and integration with main server
class BufferedHelmetReceiver:
    """
    Example integration class showing how to use the buffered MQTT receiver
    with the helmet monitoring system
    """
    
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.mqtt_receiver = MQTTReceiver(
            broker_host=broker_host,
            broker_port=broker_port,
            buffer_size=30
        )
        
        # Register handlers
        self._register_handlers()
        
        # Data storage
        self.device_data = {}
        self.emergencies = {}
        
    def _register_handlers(self):
        """Register message handlers for different sensor types"""
        
        # Handler for all gas sensor data
        self.mqtt_receiver.register_handler(
            'sensors', '*/gas',
            self._handle_gas_data
        )
        
        # Handler for all GPS data
        self.mqtt_receiver.register_handler(
            'sensors', '*/gps',
            self._handle_gps_data
        )
        
        # Handler for all temperature data
        self.mqtt_receiver.register_handler(
            'sensors', '*/temperature',
            self._handle_temperature_data
        )
        
        # Handler for all pulse data
        self.mqtt_receiver.register_handler(
            'sensors', '*/pulse',
            self._handle_pulse_data
        )
        
        # Handler for emergency status
        self.mqtt_receiver.register_handler(
            'status', '*/emergency',
            self._handle_emergency_status
        )
        
        # Handler for all status messages (catch-all)
        self.mqtt_receiver.register_handler(
            'status', '*',
            self._handle_general_status
        )
    
    def _handle_gas_data(self, device_id, sensor_type, data, raw_message):
        """Handle gas sensor data"""
        print(f"Gas data from {device_id}: {data}")
        # Store in device data
        if device_id not in self.device_data:
            self.device_data[device_id] = {}
        self.device_data[device_id]['gas'] = data
    
    def _handle_gps_data(self, device_id, sensor_type, data, raw_message):
        """Handle GPS data"""
        print(f"GPS data from {device_id}: {data}")
        if device_id not in self.device_data:
            self.device_data[device_id] = {}
        self.device_data[device_id]['gps'] = data
    
    def _handle_temperature_data(self, device_id, sensor_type, data, raw_message):
        """Handle temperature data"""
        print(f"Temperature from {device_id}: {data}")
        if device_id not in self.device_data:
            self.device_data[device_id] = {}
        self.device_data[device_id]['temperature'] = data
        
        # Check for high temperature alert
        if data and data.get('value', 0) > 38.0:
            print(f"ALERT: High temperature from {device_id}")
    
    def _handle_pulse_data(self, device_id, sensor_type, data, raw_message):
        """Handle pulse oximeter data"""
        print(f"Pulse data from {device_id}: {data}")
        if device_id not in self.device_data:
            self.device_data[device_id] = {}
        self.device_data[device_id]['pulse'] = data
        
        # Check for critical vitals
        if data:
            hr = data.get('heart_rate', 0)
            spo2 = data.get('spo2', 100)
            if hr < 50 or hr > 150 or spo2 < 90:
                print(f"ALERT: Critical vitals from {device_id}")
    
    def _handle_emergency_status(self, device_id, status_type, data, raw_message):
        """Handle emergency status messages"""
        print(f"EMERGENCY from {device_id}: {data}")
        self.emergencies[device_id] = {
            'type': data.get('message', 'unknown'),
            'timestamp': datetime.now(),
            'data': data
        }
        
        # Trigger emergency response
        self._trigger_emergency_response(device_id, data)
    
    def _handle_general_status(self, device_id, status_type, data, raw_message):
        """Handle general status messages"""
        print(f"Status from {device_id} ({status_type}): {data}")
        if device_id not in self.device_data:
            self.device_data[device_id] = {}
        self.device_data[device_id]['last_status'] = data
    
    def _trigger_emergency_response(self, device_id, data):
        """Trigger emergency response procedures"""
        print(f"EMERGENCY RESPONSE for {device_id}: {data}")
        # Implement emergency response logic here
        # Send notifications, log to database, etc.
    
    def start(self):
        """Start the buffered receiver"""
        self.mqtt_receiver.start()
    
    def stop(self):
        """Stop the buffered receiver"""
        self.mqtt_receiver.stop()
    
    def get_stats(self):
        """Get receiver statistics"""
        return self.mqtt_receiver.get_buffer_stats()
    
    def get_recent_messages(self, count=10):
        """Get recent messages"""
        return self.mqtt_receiver.get_recent_messages(count)

# Example usage
if __name__ == "__main__":
    # Create and start the buffered receiver
    receiver = BufferedHelmetReceiver(broker_host="192.168.1.100")
    
    try:
        receiver.start()
        print("Buffered MQTT receiver started. Press Ctrl+C to stop.")
        
        # Monitor statistics
        import time
        while True:
            stats = receiver.get_stats()
            print(f"Received: {stats['messages_received']}, "
                  f"Processed: {stats['messages_processed']}, "
                  f"Buffer: {stats['current_buffer_size']}/{stats['buffer_capacity']}")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\nStopping receiver...")
        receiver.stop()