# config.py - Configuration settings
"""
Configuration file for Emergency Helmet System
Modify these settings according to your environment
"""

# MQTT Broker Configuration
MQTT_CONFIG = {
    'broker_host': '192.168.1.100',  # Your MQTT broker IP address
    'broker_port': 1883,
    'username': None,                # If your broker requires authentication
    'password': None,                # If your broker requires authentication
    'buffer_size': 30,               # Message buffer size
    'keepalive': 60                  # MQTT keepalive interval
}

# Database Configuration
DATABASE_CONFIG = {
    'db_path': 'helmet_system.db',   # SQLite database file path
    'batch_size': 15,                # Database operations per batch
    'max_queue_size': 200,           # Maximum queue size for database operations
    'wal_mode': True                 # Use WAL journal mode for better performance
}

# System Monitoring Configuration
MONITORING_CONFIG = {
    'stats_interval': 30,            # Statistics print interval (seconds)
    'health_check_interval': 60,     # System health check interval (seconds)
    'log_level': 'INFO',             # Logging level: DEBUG, INFO, WARNING, ERROR
    'emergency_contacts': [          # Emergency notification contacts
        'admin@yourcompany.com',
        'safety-team@yourcompany.com'
    ]
}

# Alert Thresholds
ALERT_THRESHOLDS = {
    'high_temperature': 38.0,        # Celsius
    'critical_temperature': 40.0,    # Celsius
    'low_heart_rate': 50,            # BPM
    'high_heart_rate': 150,          # BPM
    'low_oxygen': 90,                # SpO2 percentage
    'gas_warning': 1500,             # ADC value for warning
    'gas_alarm': 2500                # ADC value for alarm
}