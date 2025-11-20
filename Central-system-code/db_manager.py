# database_manager.py - Asynchronous Database Management with Buffered Operations
import sqlite3
import threading
import queue
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import time

class DatabaseManager:
    """
    Asynchronous database management system with buffered operations
    Prioritizes message receiving over database insertion
    Uses background thread for non-blocking database operations
    """
    
    def __init__(self, db_path: str = "helmet_system.db", batch_size: int = 10, max_queue_size: int = 100):
        """
        Initialize the database manager with buffered operations
        
        Args:
            db_path: Path to SQLite database file
            batch_size: Number of operations to batch together
            max_queue_size: Maximum queue size before applying backpressure
        """
        self.db_path = db_path
        self.batch_size = batch_size
        self.max_queue_size = max_queue_size
        
        # Operation queue for asynchronous processing
        self.operation_queue = queue.Queue(maxsize=max_queue_size)
        
        # Control flags
        self.is_running = False
        self.worker_thread = None
        
        # Statistics
        self.stats = {
            'operations_queued': 0,
            'operations_completed': 0,
            'batch_inserts': 0,
            'errors': 0,
            'queue_overflows': 0
        }
        self.stats_lock = threading.Lock()
        
        # Initialize database schema
        self._init_database()
        
        # Setup logging
        self.logger = self._setup_logging()
        
        self.logger.info(f"DatabaseManager initialized with batch_size={batch_size}, max_queue={max_queue_size}")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logger = logging.getLogger('DatabaseManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # File handler
            file_handler = logging.FileHandler('database_manager.log')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def _init_database(self):
        """Initialize database schema"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            # Devices table - tracks all connected devices
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'offline',
                    firmware_version TEXT,
                    last_battery_level REAL,
                    total_messages INTEGER DEFAULT 0
                )
            ''')
            
            # Sensor data table - stores all sensor readings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    sensor_type TEXT,
                    value_json TEXT,
                    raw_message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices (device_id),
                    INDEX idx_device_sensor (device_id, sensor_type),
                    INDEX idx_timestamp (timestamp)
                )
            ''')
            
            # Emergency events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emergency_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    emergency_type TEXT,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    location_data TEXT,
                    sensor_context TEXT,
                    resolved_by TEXT,
                    resolution_notes TEXT,
                    FOREIGN KEY (device_id) REFERENCES devices (device_id),
                    INDEX idx_emergency_status (status),
                    INDEX idx_emergency_time (start_time)
                )
            ''')
            
            # System alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    alert_type TEXT,
                    alert_level TEXT,
                    message TEXT,
                    sensor_data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_by TEXT,
                    acknowledged_at TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices (device_id),
                    INDEX idx_alert_type (alert_type),
                    INDEX idx_alert_time (timestamp)
                )
            ''')
            
            # Message buffer audit table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS buffer_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT,
                    items_count INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    duration_ms INTEGER,
                    success BOOLEAN
                )
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Database schema initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _db_worker(self):
        """
        Background worker thread that processes database operations
        Implements batching for efficient database operations
        """
        self.logger.info("Database worker thread started")
        
        batch_operations = []
        last_batch_time = time.time()
        
        while self.is_running:
            try:
                # Try to get operation from queue with timeout
                try:
                    operation = self.operation_queue.get(timeout=1.0)
                    batch_operations.append(operation)
                    
                    # Update statistics
                    with self.stats_lock:
                        self.stats['operations_queued'] += 1
                    
                except queue.Empty:
                    operation = None
                
                # Process batch if we have enough operations or enough time has passed
                current_time = time.time()
                should_process_batch = (
                    len(batch_operations) >= self.batch_size or
                    (operation is None and len(batch_operations) > 0) or
                    (current_time - last_batch_time >= 5.0 and len(batch_operations) > 0)
                )
                
                if should_process_batch:
                    if batch_operations:
                        self._process_batch(batch_operations)
                        batch_operations = []
                        last_batch_time = current_time
                
                # Mark operation as done if we processed it
                if operation is not None:
                    self.operation_queue.task_done()
                    
            except Exception as e:
                self.logger.error(f"Error in database worker: {e}")
                with self.stats_lock:
                    self.stats['errors'] += 1
        
        # Process any remaining operations before shutdown
        if batch_operations:
            self._process_batch(batch_operations)
        
        self.logger.info("Database worker thread stopped")
    
    def _process_batch(self, operations: List[Dict[str, Any]]):
        """
        Process a batch of database operations
        
        Args:
            operations: List of operation dictionaries
        """
        start_time = time.time()
        
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent performance
            cursor = conn.cursor()
            
            # Group operations by type for more efficient processing
            device_ops = [op for op in operations if op['type'] == 'update_device']
            sensor_ops = [op for op in operations if op['type'] == 'insert_sensor_data']
            emergency_ops = [op for op in operations if op['type'] == 'emergency_event']
            alert_ops = [op for op in operations if op['type'] == 'system_alert']
            
            # Process device updates
            if device_ops:
                self._batch_update_devices(cursor, device_ops)
            
            # Process sensor data inserts
            if sensor_ops:
                self._batch_insert_sensor_data(cursor, sensor_ops)
            
            # Process emergency events
            if emergency_ops:
                self._batch_insert_emergency_events(cursor, emergency_ops)
            
            # Process system alerts
            if alert_ops:
                self._batch_insert_system_alerts(cursor, alert_ops)
            
            conn.commit()
            
            # Update statistics
            with self.stats_lock:
                self.stats['operations_completed'] += len(operations)
                self.stats['batch_inserts'] += 1
            
            duration = int((time.time() - start_time) * 1000)
            
            # Log batch processing success
            cursor.execute('''
                INSERT INTO buffer_audit (operation_type, items_count, duration_ms, success)
                VALUES (?, ?, ?, ?)
            ''', ('batch_process', len(operations), duration, True))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(f"Processed batch of {len(operations)} operations in {duration}ms")
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            
            # Log batch processing failure
            try:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                duration = int((time.time() - start_time) * 1000)
                cursor.execute('''
                    INSERT INTO buffer_audit (operation_type, items_count, duration_ms, success)
                    VALUES (?, ?, ?, ?)
                ''', ('batch_process', len(operations), duration, False))
                conn.commit()
                conn.close()
            except:
                pass
            
            with self.stats_lock:
                self.stats['errors'] += 1
    
    def _batch_update_devices(self, cursor, device_ops):
        """Batch update device information"""
        for op in device_ops:
            data = op['data']
            cursor.execute('''
                INSERT OR REPLACE INTO devices 
                (device_id, last_seen, status, firmware_version, last_battery_level, total_messages)
                VALUES (?, ?, ?, ?, ?, COALESCE((SELECT total_messages FROM devices WHERE device_id = ?), 0) + 1)
            ''', (
                data['device_id'],
                data.get('timestamp', datetime.now()),
                data.get('status', 'online'),
                data.get('firmware_version'),
                data.get('battery_level'),
                data['device_id']
            ))
    
    def _batch_insert_sensor_data(self, cursor, sensor_ops):
        """Batch insert sensor data"""
        for op in sensor_ops:
            data = op['data']
            cursor.execute('''
                INSERT INTO sensor_data 
                (device_id, sensor_type, value_json, raw_message, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data['device_id'],
                data['sensor_type'],
                json.dumps(data['value_data']),
                data.get('raw_message', ''),
                data.get('timestamp', datetime.now())
            ))
    
    def _batch_insert_emergency_events(self, cursor, emergency_ops):
        """Batch insert emergency events"""
        for op in emergency_ops:
            data = op['data']
            cursor.execute('''
                INSERT INTO emergency_events 
                (device_id, emergency_type, location_data, sensor_context)
                VALUES (?, ?, ?, ?)
            ''', (
                data['device_id'],
                data['emergency_type'],
                json.dumps(data.get('location_data', {})),
                json.dumps(data.get('sensor_context', {}))
            ))
    
    def _batch_insert_system_alerts(self, cursor, alert_ops):
        """Batch insert system alerts"""
        for op in alert_ops:
            data = op['data']
            cursor.execute('''
                INSERT INTO system_alerts 
                (device_id, alert_type, alert_level, message, sensor_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data['device_id'],
                data['alert_type'],
                data.get('alert_level', 'warning'),
                data.get('message', ''),
                json.dumps(data.get('sensor_data', {}))
            ))
    
    def queue_operation(self, operation_type: str, data: Dict[str, Any]) -> bool:
        """
        Queue a database operation for asynchronous processing
        
        Args:
            operation_type: Type of operation ('update_device', 'insert_sensor_data', etc.)
            data: Operation-specific data
            
        Returns:
            bool: True if operation was queued successfully
        """
        if not self.is_running:
            self.logger.warning("Database manager not running, operation rejected")
            return False
        
        operation = {
            'type': operation_type,
            'data': data,
            'queued_at': datetime.now()
        }
        
        try:
            # Non-blocking put with timeout
            self.operation_queue.put(operation, block=False, timeout=0.1)
            return True
            
        except queue.Full:
            self.logger.warning("Database operation queue full, operation dropped")
            with self.stats_lock:
                self.stats['queue_overflows'] += 1
            return False
    
    # Public API methods for different operation types
    
    def update_device_status(self, device_id: str, status: str = 'online', 
                           firmware_version: str = None, battery_level: float = None) -> bool:
        """
        Update device status information
        
        Args:
            device_id: Unique device identifier
            status: Device status ('online', 'offline', 'error')
            firmware_version: Device firmware version
            battery_level: Last known battery level
            
        Returns:
            bool: True if operation queued successfully
        """
        data = {
            'device_id': device_id,
            'status': status,
            'firmware_version': firmware_version,
            'battery_level': battery_level,
            'timestamp': datetime.now()
        }
        
        return self.queue_operation('update_device', data)
    
    def insert_sensor_data(self, device_id: str, sensor_type: str, 
                          value_data: Dict[str, Any], raw_message: str = '') -> bool:
        """
        Insert sensor data reading
        
        Args:
            device_id: Unique device identifier
            sensor_type: Type of sensor ('temperature', 'gps', 'gas', 'pulse')
            value_data: Sensor reading data as dictionary
            raw_message: Original raw message for debugging
            
        Returns:
            bool: True if operation queued successfully
        """
        data = {
            'device_id': device_id,
            'sensor_type': sensor_type,
            'value_data': value_data,
            'raw_message': raw_message,
            'timestamp': value_data.get('timestamp', datetime.now())
        }
        
        return self.queue_operation('insert_sensor_data', data)
    
    def record_emergency_event(self, device_id: str, emergency_type: str,
                             location_data: Dict[str, Any] = None,
                             sensor_context: Dict[str, Any] = None) -> bool:
        """
        Record an emergency event
        
        Args:
            device_id: Unique device identifier
            emergency_type: Type of emergency ('FREE_FALL', 'IMPACT', etc.)
            location_data: GPS location data if available
            sensor_context: Sensor readings at time of emergency
            
        Returns:
            bool: True if operation queued successfully
        """
        data = {
            'device_id': device_id,
            'emergency_type': emergency_type,
            'location_data': location_data or {},
            'sensor_context': sensor_context or {}
        }
        
        return self.queue_operation('emergency_event', data)
    
    def create_system_alert(self, device_id: str, alert_type: str, message: str,
                          alert_level: str = 'warning', sensor_data: Dict[str, Any] = None) -> bool:
        """
        Create a system alert
        
        Args:
            device_id: Unique device identifier
            alert_type: Type of alert ('high_temperature', 'gas_alarm', etc.)
            message: Alert message
            alert_level: Alert level ('info', 'warning', 'critical')
            sensor_data: Relevant sensor data for the alert
            
        Returns:
            bool: True if operation queued successfully
        """
        data = {
            'device_id': device_id,
            'alert_type': alert_type,
            'message': message,
            'alert_level': alert_level,
            'sensor_data': sensor_data or {}
        }
        
        return self.queue_operation('system_alert', data)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current database manager statistics
        
        Returns:
            dict: Statistics including queue size, operations count, etc.
        """
        with self.stats_lock:
            stats = self.stats.copy()
        
        stats['queue_size'] = self.operation_queue.qsize()
        stats['queue_capacity'] = self.max_queue_size
        stats['is_running'] = self.is_running
        
        return stats
    
    def wait_for_queue_empty(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all queued operations to be processed
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if queue emptied, False if timeout
        """
        try:
            return self.operation_queue.join(timeout=timeout)
        except Exception as e:
            self.logger.error(f"Error waiting for queue empty: {e}")
            return False
    
    def start(self):
        """Start the database manager"""
        if self.is_running:
            self.logger.warning("Database manager is already running")
            return
        
        self.is_running = True
        self.worker_thread = threading.Thread(
            target=self._db_worker,
            daemon=True,
            name="DatabaseWorker"
        )
        self.worker_thread.start()
        
        self.logger.info("Database manager started successfully")
    
    def stop(self):
        """Stop the database manager and wait for pending operations"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping database manager...")
        self.is_running = False
        
        # Wait for worker thread to finish
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=10.0)
        
        self.logger.info("Database manager stopped")

# Integration class with the buffered MQTT receiver
class DatabaseIntegration:
    """
    Integration class that connects the buffered MQTT receiver with the database manager
    """
    
    def __init__(self, mqtt_receiver, db_manager):
        """
        Initialize the integration
        
        Args:
            mqtt_receiver: Instance of MQTTReceiver
            db_manager: Instance of DatabaseManager
        """
        self.mqtt_receiver = mqtt_receiver
        self.db_manager = db_manager
        
        # Register database handlers with MQTT receiver
        self._register_handlers()
    
    def _register_handlers(self):
        """Register database handlers for MQTT messages"""
        
        # Handler for all sensor data - routes to database
        self.mqtt_receiver.register_handler(
            'sensors', '*',
            self._handle_sensor_data
        )
        
        # Handler for status messages - updates device status
        self.mqtt_receiver.register_handler(
            'status', '*',
            self._handle_status_message
        )
    
    def _handle_sensor_data(self, device_id, sensor_type, data, raw_message):
        """Handle sensor data and store in database"""
        if data is None:
            return
        
        # Update device as online
        self.db_manager.update_device_status(device_id, 'online')
        
        # Store sensor data
        success = self.db_manager.insert_sensor_data(
            device_id=device_id,
            sensor_type=sensor_type,
            value_data=data,
            raw_message=json.dumps(raw_message) if raw_message else ''
        )
        
        if not success:
            # Log the failure but don't block the main thread
            logging.warning(f"Failed to queue sensor data for {device_id}/{sensor_type}")
        
        # Check for critical conditions that need alerts
        self._check_critical_conditions(device_id, sensor_type, data)
    
    def _handle_status_message(self, device_id, status_type, data, raw_message):
        """Handle status messages"""
        if data is None:
            return
        
        # Update device status
        self.db_manager.update_device_status(device_id, 'online')
        
        # Handle emergency status
        if status_type == 'emergency':
            self.db_manager.record_emergency_event(
                device_id=device_id,
                emergency_type=data.get('message', 'unknown'),
                sensor_context=data
            )
            
            # Also create a system alert for emergencies
            self.db_manager.create_system_alert(
                device_id=device_id,
                alert_type='emergency',
                message=f"Emergency detected: {data.get('message', 'unknown')}",
                alert_level='critical',
                sensor_data=data
            )
        
        elif status_type == 'warning':
            self.db_manager.create_system_alert(
                device_id=device_id,
                alert_type='warning',
                message=data.get('message', 'Unknown warning'),
                alert_level='warning',
                sensor_data=data
            )
    
    def _check_critical_conditions(self, device_id, sensor_type, data):
        """Check for critical sensor readings that need alerts"""
        if sensor_type == 'gas' and data.get('status') == 'ALARM':
            self.db_manager.create_system_alert(
                device_id=device_id,
                alert_type='gas_alarm',
                message='High gas concentration detected',
                alert_level='critical',
                sensor_data=data
            )
        
        elif sensor_type == 'temperature' and data.get('value', 0) > 38.0:
            self.db_manager.create_system_alert(
                device_id=device_id,
                alert_type='high_temperature',
                message='Elevated temperature detected',
                alert_level='warning',
                sensor_data=data
            )
        
        elif sensor_type == 'pulse':
            hr = data.get('heart_rate', 0)
            spo2 = data.get('spo2', 100)
            
            if hr < 50 or hr > 150:
                self.db_manager.create_system_alert(
                    device_id=device_id,
                    alert_type='abnormal_heart_rate',
                    message=f'Abnormal heart rate: {hr} BPM',
                    alert_level='warning',
                    sensor_data=data
                )
            
            if spo2 < 90:
                self.db_manager.create_system_alert(
                    device_id=device_id,
                    alert_type='low_oxygen',
                    message=f'Low blood oxygen: {spo2}%',
                    alert_level='critical',
                    sensor_data=data
                )

# Example usage
if __name__ == "__main__":
    # Create instances
    from mqtt_receiver import MQTTReceiver
    
    mqtt_receiver = MQTTReceiver(broker_host="192.168.1.100")
    db_manager = DatabaseManager(batch_size=15, max_queue_size=200)
    
    # Create integration
    db_integration = DatabaseIntegration(mqtt_receiver, db_manager)
    
    try:
        # Start both systems
        db_manager.start()
        mqtt_receiver.start()
        
        print("Database integration started. Press Ctrl+C to stop.")
        
        # Monitor statistics
        import time
        while True:
            mqtt_stats = mqtt_receiver.get_buffer_stats()
            db_stats = db_manager.get_stats()
            
            print(f"MQTT: {mqtt_stats['messages_received']} received | "
                  f"DB: {db_stats['operations_queued']} queued, {db_stats['operations_completed']} completed")
            
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\nStopping systems...")
        mqtt_receiver.stop()
        db_manager.stop()