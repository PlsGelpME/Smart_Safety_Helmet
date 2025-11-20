# main.py - Emergency Helmet System with Web GUI Auto-Launch
import time
import signal
import sys
import logging
import json
import os
import threading
import webbrowser
from datetime import datetime
from mqtt_receiver import MQTTReceiver, BufferedHelmetReceiver
from database_manager import DatabaseManager, DatabaseIntegration

# Import Flask web server
from flask import Flask, render_template, jsonify, request
import threading

class WebDashboard:
    """
    Web-based GUI dashboard for real-time monitoring
    """
    
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.system_stats = {}
        self.recent_messages = []
        self.active_emergencies = {}
        self.connected_devices = {}
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/stats')
        def get_stats():
            """API endpoint for system statistics"""
            return jsonify({
                'system_stats': self.system_stats,
                'active_emergencies': self.active_emergencies,
                'connected_devices': self.connected_devices,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/recent-messages')
        def get_recent_messages():
            """API endpoint for recent messages"""
            return jsonify(self.recent_messages[-50:])  # Last 50 messages
        
        @self.app.route('/api/emergencies')
        def get_emergencies():
            """API endpoint for active emergencies"""
            return jsonify(self.active_emergencies)
        
        @self.app.route('/api/health')
        def health_check():
            """Health check endpoint"""
            return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})
        
        @self.app.route('/api/command', methods=['POST'])
        def handle_command():
            """Handle system commands from GUI"""
            command = request.json.get('command')
            if command == 'clear_emergencies':
                self.active_emergencies.clear()
                return jsonify({'status': 'success', 'message': 'Emergencies cleared'})
            elif command == 'get_logs':
                return jsonify({'status': 'success', 'logs': self._get_recent_logs()})
            else:
                return jsonify({'status': 'error', 'message': 'Unknown command'})
    
    def _get_recent_logs(self):
        """Get recent log entries"""
        try:
            with open('helmet_system.log', 'r') as f:
                lines = f.readlines()[-100:]  # Last 100 lines
            return lines
        except:
            return ["No log file available"]
    
    def update_stats(self, system_stats, mqtt_stats, db_stats):
        """Update dashboard statistics"""
        self.system_stats = {
            'uptime': system_stats.get('uptime', '0:00:00'),
            'total_messages': system_stats.get('total_messages', 0),
            'system_status': system_stats.get('status', 'unknown'),
            'mqtt_connected': mqtt_stats.get('is_connected', False),
            'messages_received': mqtt_stats.get('messages_received', 0),
            'messages_processed': mqtt_stats.get('messages_processed', 0),
            'buffer_usage': mqtt_stats.get('current_buffer_size', 0),
            'buffer_capacity': mqtt_stats.get('buffer_capacity', 30),
            'db_queued': db_stats.get('operations_queued', 0),
            'db_completed': db_stats.get('operations_completed', 0),
            'db_errors': db_stats.get('errors', 0),
            'last_update': datetime.now().isoformat()
        }
    
    def add_message(self, device_id, message_type, data):
        """Add a new message to recent messages"""
        self.recent_messages.append({
            'device_id': device_id,
            'type': message_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 100 messages
        if len(self.recent_messages) > 100:
            self.recent_messages.pop(0)
    
    def add_emergency(self, device_id, emergency_data):
        """Add an emergency event"""
        self.active_emergencies[device_id] = {
            **emergency_data,
            'start_time': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat()
        }
    
    def update_device_status(self, device_id, status):
        """Update device connection status"""
        if device_id not in self.connected_devices:
            self.connected_devices[device_id] = {
                'first_seen': datetime.now().isoformat(),
                'status': status,
                'last_seen': datetime.now().isoformat()
            }
        else:
            self.connected_devices[device_id].update({
                'status': status,
                'last_seen': datetime.now().isoformat()
            })
    
    def start(self):
        """Start the web dashboard in a separate thread"""
        def run_flask():
            self.app.run(
                host=self.host, 
                port=self.port, 
                debug=False, 
                threaded=True,
                use_reloader=False
            )
        
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        print(f"📊 Web dashboard started: http://{self.host}:{self.port}")
        return True
    
    def open_browser(self):
        """Open web browser automatically"""
        # Wait a moment for Flask to start
        time.sleep(2)
        webbrowser.open(f"http://localhost:{self.port}")

class EmergencyHelmetSystem:
    """
    Main application class for the Emergency Helmet Monitoring System
    Now with integrated web GUI
    """
    
    def __init__(self, config_path="config.json"):
        """
        Initialize the complete helmet monitoring system
        
        Args:
            config_path: Path to JSON configuration file
        """
        self.config_path = config_path
        self.config = None
        self.is_running = False
        
        # Initialize components
        self.mqtt_receiver = None
        self.db_manager = None
        self.db_integration = None
        self.web_dashboard = None
        
        # Statistics
        self.start_time = None
        self.message_count = 0
        
        # Load configuration
        if not self._load_config():
            raise Exception(f"Failed to load configuration from {config_path}")
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger('HelmetSystem')
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self):
        """
        Load configuration from JSON file
        
        Returns:
            bool: True if configuration loaded successfully
        """
        try:
            if not os.path.exists(self.config_path):
                self._create_default_config()
                print(f"Created default configuration file: {self.config_path}")
                print("Please edit the configuration file and restart the application.")
                return False
            
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            # Validate required configuration sections
            required_sections = ['mqtt', 'database', 'monitoring']
            for section in required_sections:
                if section not in self.config:
                    raise ValueError(f"Missing required configuration section: {section}")
            
            print(f"Configuration loaded successfully from {self.config_path}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"Error parsing configuration file: {e}")
            return False
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False
    
    def _create_default_config(self):
        """Create a default configuration file"""
        default_config = {
            "mqtt": {
                "broker_host": "192.168.1.100",
                "broker_port": 1883,
                "username": None,
                "password": None,
                "buffer_size": 30,
                "keepalive": 60,
                "topics": [
                    "devices/+/sensors/+",
                    "devices/+/status/+"
                ]
            },
            "database": {
                "db_path": "helmet_system.db",
                "batch_size": 15,
                "max_queue_size": 200,
                "wal_mode": True
            },
            "monitoring": {
                "stats_interval": 30,
                "health_check_interval": 60,
                "log_level": "INFO",
                "log_file": "helmet_system.log",
                "emergency_contacts": [
                    "admin@yourcompany.com",
                    "safety-team@yourcompany.com"
                ],
                "web_dashboard": {
                    "host": "0.0.0.0",
                    "port": 5000,
                    "auto_open_browser": True
                }
            },
            "alerts": {
                "high_temperature": 38.0,
                "critical_temperature": 40.0,
                "low_heart_rate": 50,
                "high_heart_rate": 150,
                "low_oxygen": 90,
                "gas_warning": 1500,
                "gas_alarm": 2500
            },
            "system": {
                "shutdown_timeout": 10,
                "max_retries": 3,
                "retry_delay": 5
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
    
    def _setup_logging(self):
        """Setup comprehensive logging configuration"""
        log_level = getattr(logging, self.config['monitoring']['log_level'], logging.INFO)
        log_file = self.config['monitoring']['log_file']
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def initialize_components(self):
        """Initialize all system components"""
        try:
            self.logger.info("Initializing Emergency Helmet System components...")
            
            # Initialize Web Dashboard
            web_config = self.config['monitoring'].get('web_dashboard', {})
            self.web_dashboard = WebDashboard(
                host=web_config.get('host', '0.0.0.0'),
                port=web_config.get('port', 5000)
            )
            
            # Initialize MQTT Receiver
            self.mqtt_receiver = MQTTReceiver(
                broker_host=self.config['mqtt']['broker_host'],
                broker_port=self.config['mqtt']['broker_port'],
                buffer_size=self.config['mqtt']['buffer_size']
            )
            
            # Initialize Database Manager
            self.db_manager = DatabaseManager(
                db_path=self.config['database']['db_path'],
                batch_size=self.config['database']['batch_size'],
                max_queue_size=self.config['database']['max_queue_size']
            )
            
            # Create integration between MQTT and Database
            self.db_integration = DatabaseIntegration(
                mqtt_receiver=self.mqtt_receiver,
                db_manager=self.db_manager
            )
            
            # Register custom handlers for GUI updates
            self._register_gui_handlers()
            
            self.logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            return False
    
    def _register_gui_handlers(self):
        """Register handlers for GUI updates"""
        
        # Emergency alert handler for GUI
        def emergency_gui_handler(device_id, status_type, data, raw_message):
            if status_type == 'emergency':
                self.web_dashboard.add_emergency(device_id, data)
                self._handle_immediate_emergency(device_id, data)
        
        self.mqtt_receiver.register_handler(
            'status', '*/emergency',
            emergency_gui_handler
        )
        
        # All messages handler for GUI
        def all_messages_gui_handler(device_id, message_type, data, raw_message):
            self.web_dashboard.add_message(device_id, message_type, data)
            self.web_dashboard.update_device_status(device_id, 'online')
        
        self.mqtt_receiver.register_handler(
            'sensors', '*',
            all_messages_gui_handler
        )
        
        self.mqtt_receiver.register_handler(
            'status', '*',
            all_messages_gui_handler
        )
    
    def _handle_immediate_emergency(self, device_id, data):
        """Handle immediate emergency notifications"""
        self.logger.critical(f"IMMEDIATE EMERGENCY: Device {device_id} - {data}")
        
        # Visual alert in CLI
        print(f"\n{'!!!'* 20}")
        print(f"EMERGENCY ALERT - Device: {device_id}")
        print(f"Type: {data.get('message', 'Unknown')}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'!!!'* 20}\n")
    
    def start(self):
        """Start the complete helmet monitoring system with GUI"""
        if self.is_running:
            self.logger.warning("System is already running")
            return
        
        if not self.initialize_components():
            self.logger.error("Failed to initialize components, cannot start system")
            return
        
        try:
            self.logger.info("Starting Emergency Helmet System...")
            self.start_time = datetime.now()
            self.is_running = True
            
            # Start web dashboard first
            self.web_dashboard.start()
            
            # Auto-open browser if configured
            web_config = self.config['monitoring'].get('web_dashboard', {})
            if web_config.get('auto_open_browser', True):
                self.logger.info("Opening web browser automatically...")
                self.web_dashboard.open_browser()
            
            # Start database manager
            self.db_manager.start()
            self.logger.info("Database manager started")
            
            # Start MQTT receiver
            self.mqtt_receiver.start()
            self.logger.info("MQTT receiver started")
            
            self.logger.info("Emergency Helmet System started successfully")
            self._run_main_loop()
            
        except Exception as e:
            self.logger.error(f"Failed to start system: {e}")
            self.stop()
    
    def _run_main_loop(self):
        """Main system monitoring and management loop"""
        self.logger.info("Entering main monitoring loop...")
        
        last_stats_time = time.time()
        stats_interval = self.config['monitoring']['stats_interval']
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # Update GUI statistics periodically
                if current_time - last_stats_time >= stats_interval:
                    self._update_gui_stats()
                    self._print_cli_stats()
                    last_stats_time = current_time
                
                # Check system health
                self._check_system_health()
                
                # Small sleep to prevent excessive CPU usage
                time.sleep(1)
                
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(5)
    
    def _update_gui_stats(self):
        """Update web dashboard statistics"""
        if not self.mqtt_receiver or not self.db_manager or not self.web_dashboard:
            return
        
        mqtt_stats = self.mqtt_receiver.get_buffer_stats()
        db_stats = self.db_manager.get_stats()
        
        # Calculate uptime
        uptime = datetime.now() - self.start_time
        uptime_str = str(uptime).split('.')[0]
        
        system_stats = {
            'uptime': uptime_str,
            'total_messages': self.message_count,
            'status': 'running'
        }
        
        self.web_dashboard.update_stats(system_stats, mqtt_stats, db_stats)
    
    def _print_cli_stats(self):
        """Print comprehensive system statistics to CLI"""
        if not self.mqtt_receiver or not self.db_manager:
            return
        
        mqtt_stats = self.mqtt_receiver.get_buffer_stats()
        db_stats = self.db_manager.get_stats()
        
        # Calculate uptime
        uptime = datetime.now() - self.start_time
        uptime_str = str(uptime).split('.')[0]
        
        print(f"\n{'='*70}")
        print(f"️  EMERGENCY HELMET SYSTEM - REAL-TIME MONITORING")
        print(f"{'='*70}")
        print(f" Uptime: {uptime_str} | 📨 Total Messages: {self.message_count}")
        print(f" Web GUI: http://localhost:{self.config['monitoring']['web_dashboard']['port']}")
        print(f"")
        print(f" MQTT RECEIVER:")
        print(f"   Connected: {'Yes' if mqtt_stats['is_connected'] else '❌ No'}")
        print(f"   Received: {mqtt_stats['messages_received']}")
        print(f"   Processed: {mqtt_stats['messages_processed']}")
        print(f"  ️  Buffer: {mqtt_stats['current_buffer_size']}/{mqtt_stats['buffer_capacity']}")
        print(f"    Overflows: {mqtt_stats['buffer_overflows']}")
        print(f"")
        print(f" DATABASE MANAGER:")
        print(f"   Queued: {db_stats['operations_queued']}")
        print(f"   Completed: {db_stats['operations_completed']}")
        print(f"  ️  Queue: {db_stats['queue_size']}/{db_stats['queue_capacity']}")
        print(f"   Batch Inserts: {db_stats['batch_inserts']}")
        print(f"   Errors: {db_stats['errors']}")
        print(f"")
        print(f" ACTIVE EMERGENCIES: {len(self.web_dashboard.active_emergencies)}")
        for device_id, emergency in self.web_dashboard.active_emergencies.items():
            print(f"   {device_id}: {emergency.get('type', 'Unknown')}")
        print(f"{'='*70}")
        print(f" Tip: Check web GUI for detailed visualizations")
        print(f" Press Ctrl+C to stop the system")
        print(f"{'='*70}\n")
    
    def _check_system_health(self):
        """Check system health and trigger alerts if needed"""
        if not self.mqtt_receiver or not self.db_manager:
            return
        
        mqtt_stats = self.mqtt_receiver.get_buffer_stats()
        db_stats = self.db_manager.get_stats()
        
        # Check for MQTT connection issues
        if not self.mqtt_receiver.is_connected:
            self.logger.warning(" MQTT receiver is not connected to broker")
        
        # Check for database queue issues
        queue_usage = db_stats['queue_size'] / db_stats['queue_capacity']
        if queue_usage > 0.8:
            self.logger.warning(f"️ Database queue is {queue_usage:.1%} full")
        
        # Check for buffer overflows
        if mqtt_stats['buffer_overflows'] > 0:
            self.logger.warning(f" MQTT buffer has {mqtt_stats['buffer_overflows']} overflows")

    def stop(self):
        """Stop the complete system gracefully"""
        if not self.is_running:
            return
        
        self.logger.info(" Initiating system shutdown...")
        self.is_running = False
        
        try:
            # Stop MQTT receiver first to prevent new messages
            if self.mqtt_receiver:
                self.logger.info("Stopping MQTT receiver...")
                self.mqtt_receiver.stop()
            
            # Wait for database operations to complete
            if self.db_manager:
                self.logger.info("Waiting for pending database operations...")
                if not self.db_manager.wait_for_queue_empty(timeout=10.0):
                    self.logger.warning("Some database operations may not have completed")
                
                self.logger.info("Stopping database manager...")
                self.db_manager.stop()
            
            # Calculate final statistics
            if self.start_time:
                uptime = datetime.now() - self.start_time
                uptime_str = str(uptime).split('.')[0]
                self.logger.info(f"System ran for {uptime_str}, processed {self.message_count} messages")
            
            self.logger.info("✅ Emergency Helmet System stopped successfully")
            
        except Exception as e:
            self.logger.error(f" Error during shutdown: {e}")
        finally:
            # Ensure we exit cleanly
            sys.exit(0)

def main():
    """
    Main entry point for the Emergency Helmet System
    """
    print(" Emergency Helmet Monitoring System")
    print("=" * 60)
    print(" Web GUI will open automatically")
    print(" CLI will continue running for real-time monitoring")
    print(" Use Ctrl+C to stop the system")
    print("=" * 60)
    
    # Parse command line arguments
    config_path = "config.json"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    # Create and start the system
    try:
        helmet_system = EmergencyHelmetSystem(config_path)
        helmet_system.start()
    except Exception as e:
        print(f" Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()