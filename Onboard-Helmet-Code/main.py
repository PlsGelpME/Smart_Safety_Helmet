from machine import *
import time
from mqtt_setup import MQTTSetup
from message_creator import MessageCreator

# Constants for MQTT broker configuration
server_ip = "192.168.1.100"  # Replace with your MQTT broker IP address
username = None              # Set if your broker requires authentication
password = None              # Set if your broker requires authentication

# Sensor reading intervals in seconds for power management
GPS_READ_INTERVAL      = 300      # 5 minutes - GPS consumes high power
GAS_READ_INTERVAL      = 3600     # 1 hour - Gas sensor typically stable
TEMP_READ_INTERVAL     = 300      # 5 minutes - Temperature monitoring
PULSE_READ_INTERVAL    = 60       # 1 minute - Frequent health monitoring
STATUS_UPDATE_INTERVAL = 60       # 1 minute - Regular status updates

# Initialize MQTT communication system
mqtt_setup = MQTTSetup(server=server_ip, username=username, password=password)
# Get the sender function for MQTT message publishing
sender_function = mqtt_setup.setup_connection()
# Create message creator instance for formatting sensor data
message_sender = MessageCreator(sender_function=sender_function)

# Global emergency flags - NOT reset automatically (requires power cycle)
free_fall = False          # Flag for free-fall detection from gyroscope
impact = False             # Flag for impact detection from force sensor
emergency_active = False   # Global emergency state flag

# Buzzer control initialization for emergency alerts
if 'buzzer' in globals():
    b = 0 # flag for buzzer

# Function declarations for interrupt handlers and emergency procedures
def free_fall_handler(pin):
    """Interrupt handler for free-fall detection from gyroscope"""
    global free_fall, emergency_active
    free_fall = True           # Set free-fall flag
    emergency_active = True    # Activate global emergency state

def impact_handler(pin):
    """Interrupt handler for impact detection from force sensor"""  
    global impact, emergency_active
    impact = True              # Set impact flag
    emergency_active = True    # Activate global emergency state

def activate_buzzer():
    """Activate buzzer and keep it on until system power off"""
    if 'buzzer' in globals():
        buzzer.value(1)  # Turn buzzer ON (continuous alert)
        print("BUZZER ACTIVATED - Requires manual power cycle to reset")

def send_emergency_data():
    """Send comprehensive emergency data including GPS and pulse readings"""
    print("SENDING EMERGENCY DATA PACKAGE...")
    
    # 1. Send emergency status with type identification
    if free_fall:
        emergency_type = "FREE_FALL"  # Free-fall emergency
    else:
        emergency_type = "IMPACT"     # Impact emergency
    
    message_sender.publish_status("emergency", f"{emergency_type} detected")
    
    # 2. Get and send GPS location with extended timeout for reliability
    gps_data_sent = False
    if 'gps' in globals():
        location = gps.get_position(timeout=20)  # Longer timeout for emergency situation
        if location:
            message_sender.publish_gps(location['latitude'], location['longitude'], location['altitude'])
            gps_data_sent = True
            print("Emergency GPS location sent")
    
    # 3. Get and send pulse oximeter data for health status
    pulse_data_sent = False
    if 'pulse' in globals():
        pulse_data = pulse.get_sensor_data()
        if pulse_data:
            message_sender.publish_pulse(pulse_data['heart_rate'], pulse_data['spo2'])
            pulse_data_sent = True
            print("Emergency pulse data sent")
    
    # 4. Send gas and temperature data for environmental context
    if 'gas_sensor' in globals():
        gas_reading = gas_sensor.take_reading()
        if gas_reading:
            message_sender.publish_gas(gas_reading['value'], gas_reading['status'])
    
    if 'temp' in globals():
        temperature = temp.getTemp(unit=1)  # Get temperature in Celsius
        message_sender.publish_temperature(temperature)
    
    # 5. Activate buzzer (non-stop until power off for attention)
    activate_buzzer()
    
    print("EMERGENCY PROTOCOL COMPLETE - System requires manual reset")

# Setup interrupt handlers for emergency detection
if 'gyro' in globals():
    # Configure gyroscope interrupt for free-fall detection on falling edge
    gyro.int_pin.irq(trigger=Pin.IRQ_FALLING, handler=free_fall_handler)

if 'frc_pin' in globals():
    # Configure force sensor interrupt for impact detection on falling edge  
    frc_pin.irq(trigger=Pin.IRQ_FALLING, handler=impact_handler)

# Timing variables for sensor reading intervals
last_gps_read      = 0   # Last GPS reading timestamp
last_gas_read      = 0   # Last gas sensor reading timestamp  
last_temp_read     = 0   # Last temperature reading timestamp
last_pulse_read    = 0   # Last pulse oximeter reading timestamp
last_status_update = 0   # Last status update timestamp

print("System initialized. Starting main loop...")

# Main program loop - runs continuously
while True:
    current_time = time.time()  # Get current time for interval checking
    
    while belt_int.value() == 0:
        if b == 0:
            buzzer.helmet_alert()
            b = 1
        
        time.sleep(1)
    else:
        b = 0
        buzzer.stop()
        
    # Handle emergency events (highest priority - non-resettable)
    if emergency_active:
        if not 'emergency_handled' in globals():
            # First time emergency detected - execute full emergency protocol
            send_emergency_data()
            global emergency_handled
            emergency_handled = True  # Mark emergency as handled
        
        buzzer.faint_alert()
        # Send periodic emergency updates while system is active
        if current_time - last_status_update >= 30:  # Every 30 seconds during emergency
            if free_fall:
                emergency_msg = "FAINT"    # Free-fall likely indicates fainting
            else:
                emergency_msg = "IMPACT"   # Impact indicates collision/fall
                
            message_sender.publish_status("emergency_active", emergency_msg)
            last_status_update = current_time
            
    else:
        # Normal operation (only if no emergency active)
        
        # Periodic GPS reading with caching for power efficiency
        if 'gps' in globals() and (current_time - last_gps_read >= GPS_READ_INTERVAL):
            print("Reading GPS...")
            location = gps.get_position_cached(cache_time=300)  # Use cached position if recent
            if location:
                message_sender.publish_gps(location['latitude'], location['longitude'], location['altitude'])
                last_gps_read = current_time  # Update last read timestamp
        
        # Periodic gas sensor reading with conditional monitoring
        if 'gas_sensor' in globals() and (current_time - last_gas_read >= GAS_READ_INTERVAL):
            if gas_sensor.should_monitor_now():  # Check if monitoring is needed
                print("Reading gas sensor...")
                reading = gas_sensor.take_reading()
                if reading:
                    message_sender.publish_gas(reading['value'], reading['status'])
                    last_gas_read = current_time  # Update last read timestamp
        
        # Periodic temperature reading with alert checking
        if 'temp' in globals() and (current_time - last_temp_read >= TEMP_READ_INTERVAL):
            print("Reading temperature...")
            temperature = temp.getTemp(unit=1)  # Get temperature in Celsius
            message_sender.publish_temperature(temperature)
            last_temp_read = current_time  # Update last read timestamp
            
            # Check if temperature exceeds threshold and send warning
            if temp.istemp():
                message_sender.publish_status("warning", "High temperature detected")
        
        # Periodic pulse oximeter reading for health monitoring
        if 'pulse' in globals() and (current_time - last_pulse_read >= PULSE_READ_INTERVAL):
            print("Reading pulse oximeter...")
            sensor_data = pulse.get_sensor_data()
            if sensor_data:
                message_sender.publish_pulse(sensor_data['heart_rate'], sensor_data['spo2'])
                last_pulse_read = current_time  # Update last read timestamp
        
        # Periodic system status update
        if current_time - last_status_update >= STATUS_UPDATE_INTERVAL:
            message_sender.publish_status("active", "System operating normally")
            last_status_update = current_time  # Update last status timestamp
    
    # Small delay to prevent excessive CPU usage and reduce power consumption
    time.sleep(1)