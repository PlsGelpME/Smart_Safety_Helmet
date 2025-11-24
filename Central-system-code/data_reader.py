# data_reader.py - Data reading and processing with organized folders
import json
import logging
import os
from datetime import datetime

class DataReader:
    def __init__(self, base_log_dir="logs"):
        self.base_log_dir = base_log_dir
        self.log_files = {}
        self.processed_count = 0
        self.setup_logging()
        self.create_directory_structure()
        
    def setup_logging(self):
        """Setup logging for data reader"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('DataReader')
        
    def create_directory_structure(self):
        """Create organized folder structure for logs"""
        # Main directories
        directories = [
            self.base_log_dir,
            os.path.join(self.base_log_dir, "sensors"),
            os.path.join(self.base_log_dir, "sensors", "gas"),
            os.path.join(self.base_log_dir, "sensors", "gps"),
            os.path.join(self.base_log_dir, "sensors", "temperature"),
            os.path.join(self.base_log_dir, "sensors", "pulse"),
            os.path.join(self.base_log_dir, "status"),
            os.path.join(self.base_log_dir, "raw"),
            os.path.join(self.base_log_dir, "combined")
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
    def process_message(self, client_id, message):
        """Process incoming MQTT message"""
        try:
            self.processed_count += 1
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.logger.info(f"Processing message #{self.processed_count} from {client_id}")
            
            # Always log to raw data file
            self.log_to_file('raw', f"{timestamp}|{client_id}|{message}")
            
            # Check if message is in JSON format
            if message.startswith('{') and message.endswith('}'):
                try:
                    data = json.loads(message)
                    self.process_json_data(client_id, data, timestamp)
                except json.JSONDecodeError:
                    self.process_raw_data(client_id, message, timestamp)
            else:
                self.process_raw_data(client_id, message, timestamp)
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
        
    def process_json_data(self, client_id, data, timestamp):
        """Process JSON formatted data"""
        sensor_type = data.get('sensor', 'unknown')
        
        if sensor_type == 'gas':
            self.process_gas_data(client_id, data, timestamp)
        elif sensor_type == 'gps':
            self.process_gps_data(client_id, data, timestamp)
        elif sensor_type == 'temperature':
            self.process_temperature_data(client_id, data, timestamp)
        elif sensor_type == 'pulse_oximeter':
            self.process_pulse_data(client_id, data, timestamp)
        elif data.get('type') == 'status':
            self.process_status_data(client_id, data, timestamp)
        else:
            self.logger.warning(f"Unknown sensor type: {sensor_type}")
            self.log_to_file('all', f"{timestamp}|{client_id}|unknown|{json.dumps(data)}")
            
    def process_raw_data(self, client_id, message, timestamp):
        """Process raw text data"""
        self.logger.info(f"Raw data from {client_id}: {message}")
        self.log_to_file('all', f"{timestamp}|{client_id}|raw|{message}")
        
    def process_gas_data(self, client_id, data, timestamp):
        """Process gas sensor data"""
        value = data.get('value', 'N/A')
        status = data.get('status', 'N/A')
        unit = data.get('unit', 'adc')
        
        log_entry = f"{timestamp}|{client_id}|{value}|{status}|{unit}|-"
        self.log_to_file('gas', log_entry)
        self.log_to_file('all', f"{timestamp}|{client_id}|gas|Value:{value}, Status:{status}")
        
        self.logger.info(f"Gas Sensor - Client: {client_id}, Value: {value}, Status: {status}")
        
    def process_gps_data(self, client_id, data, timestamp):
        """Process GPS data"""
        lat = data.get('latitude', 'N/A')
        lon = data.get('longitude', 'N/A')
        alt = data.get('altitude', 'N/A')
        
        log_entry = f"{timestamp}|{client_id}|{lat},{lon}|active|degrees|alt:{alt}"
        self.log_to_file('gps', log_entry)
        self.log_to_file('all', f"{timestamp}|{client_id}|gps|Lat:{lat}, Lon:{lon}, Alt:{alt}")
        
        self.logger.info(f"GPS Data - Client: {client_id}, Location: {lat}, {lon}, Altitude: {alt}")
        
    def process_temperature_data(self, client_id, data, timestamp):
        """Process temperature data"""
        value = data.get('value', 'N/A')
        unit = data.get('unit', 'celsius')
        
        log_entry = f"{timestamp}|{client_id}|{value}|normal|{unit}|-"
        self.log_to_file('temperature', log_entry)
        self.log_to_file('all', f"{timestamp}|{client_id}|temperature|Value:{value} {unit}")
        
        self.logger.info(f"Temperature - Client: {client_id}, Value: {value} {unit}")
        
    def process_pulse_data(self, client_id, data, timestamp):
        """Process pulse oximeter data"""
        heart_rate = data.get('heart_rate', 'N/A')
        spo2 = data.get('spo2', 'N/A')
        
        log_entry = f"{timestamp}|{client_id}|HR:{heart_rate}, SpO2:{spo2}|normal|bpm,percent|-"
        self.log_to_file('pulse', log_entry)
        self.log_to_file('all', f"{timestamp}|{client_id}|pulse|HR:{heart_rate}bpm, SpO2:{spo2}%")
        
        self.logger.info(f"Pulse Oximeter - Client: {client_id}, HR: {heart_rate}bpm, SpO2: {spo2}%")
        
    def process_status_data(self, client_id, data, timestamp):
        """Process status data"""
        status = data.get('status', 'N/A')
        message = data.get('message', '')
        
        log_entry = f"{timestamp}|{client_id}|{status}|-|-|msg:{message}"
        self.log_to_file('status', log_entry)
        self.log_to_file('all', f"{timestamp}|{client_id}|status|{status}: {message}")
        
        self.logger.info(f"Status Update - Client: {client_id}, Status: {status}, Message: {message}")
        
    def log_to_file(self, log_type, message):
        """Write message to log file"""
        try:
            if log_type in self.log_files:
                self.log_files[log_type].write(message + '\n')
                self.log_files[log_type].flush()
        except Exception as e:
            self.logger.error(f"Error writing to log file {log_type}: {e}")
            
    def get_log_directory_structure(self):
        """Return the current log directory structure"""
        structure = {
            "base_directory": self.base_log_dir,
            "session_id": getattr(self, 'session_id', 'Not initialized'),
            "log_files": {
                log_type: file.name for log_type, file in self.log_files.items()
            }
        }
        return structure
            
    def close_logs(self):
        """Close all log files and print summary"""
        log_summary = self.get_log_directory_structure()
        
        self.logger.info("Closing log files...")
        self.logger.info(f"Session ID: {log_summary['session_id']}")
        self.logger.info(f"Base directory: {log_summary['base_directory']}")
        
        for log_type, file in self.log_files.items():
            try:
                file.close()
                self.logger.info(f"Closed: {file.name}")
            except Exception as e:
                self.logger.error(f"Error closing log file {log_type}: {e}")
                
        self.logger.info("All log files closed")
        
        # Print directory structure
        self.logger.info("Final directory structure:")
        for root, dirs, files in os.walk(self.base_log_dir):
            level = root.replace(self.base_log_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            self.logger.info(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                self.logger.info(f"{subindent}{file}")
