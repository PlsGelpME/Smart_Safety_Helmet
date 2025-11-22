import gc
import esp
from machine import *
from __gyro__ import GyroSetup
from __GPS__ import GPS
from __pulse__ import Pulse
from __buzzer__ import Buzzer

# Turn off vendor OS debugging messages to reduce serial output noise
esp.osdebug(None)

# Run garbage collector to free up memory before starting application
gc.collect()
# Enable automatic garbage collection for memory management
gc.enable()


"""
Pin declarations for all sensors and peripherals
Enter pin numbers here according to your ESP32 wiring configuration
"""
temp_pin  = ADC(36) # Analog Pin for temperature sensor - Can't use 25,26,27 as we are using WiFi. Read MicroPython ADC documentation.
gas_pin   = ADC(39) # Analog pin for gas sensor reading
gas_pwr   = Pin(13) # Digital pin to control gas sensor power
gps_pwr   = Pin(14) # Digital pin to control GPS module power
gps_rx    = 3 # UART RX pin for GPS data reception
gps_tx    = 1 # UART TX pin for GPS data transmission
gyro_sda  = Pin(21) # I2C SDA pin for gyroscope (I2C channel 1)
gyro_scl  = Pin(22) # I2C SCL pin for gyroscope (I2C channel 1)
gyro_int  = Pin(19) # Interrupt pin from gyroscope for free-fall detection
pulse_sda = Pin(21) # I2C SDA pin for pulse oximeter (I2C channel 2)
pulse_scl = Pin(22) # I2C SCL pin for pulse oximeter (I2C channel 2)
frc_pin   = Pin(32) # Digital input pin for force sensor
belt_int  = Pin(33) # Digital input pin for belt interrupt/safety switch
buzz_pin  = Pin(23) # Digital output pin for buzzer control

# Configure ADC attenuation for full 0-3.3V range reading
temp_pin.atten(ADC.ATTN_11DB)  # 11dB attenuation allows 0-3.3V range
gas_pin.atten(ADC.ATTN_11DB)   # 11dB attenuation allows 0-3.3V range

"""Sensor Setup and Object instantiation """
# MPU6050 Gyroscope setup with free-fall detection
gyro = GyroSetup(
    i2c_scl_pin=gyro_scl,  # I2C clock pin for gyroscope
    i2c_sda_pin=gyro_sda,  # I2C data pin for gyroscope  
    int_pin=gyro_int       # Interrupt pin for free-fall detection
)
# Configure free-fall detection with threshold and duration parameters
gyro.configure_freefall(threshold=0x10, duration=0x05) # threshold = 0.16g force and 5 ms duration

# Initialize GPS module - it starts powered OFF for power saving
gps = __GPS__(
    power_pin = gps_pwr,    # GPIO pin controlling GPS power (enable/disable)
    rx_pin = gps_rx,        # GPS TX -> ESP32 RX (data reception from GPS)
    tx_pin = gps_tx,        # ESP32 TX -> GPS RX (optional, for GPS configuration)
    baudrate = 9600         # Communication baud rate with GPS module
)

# Initialize gas sensor with optional power control for power management
gas_sensor = GasSensor(
    gas_adc_pin = gas_pin,    # ADC pin for reading gas sensor analog value
    power_pin = gas_pwr,      # GPIO pin to control sensor power (optional power saving)
    sensor_type = "MQ2"       # Type of gas sensor (MQ2 for flammable gases)
)

# Set appropriate gas concentration thresholds for warning and alarm levels
gas_sensor.set_threshold(warning=1500, alarm=2500)  # ADC values for warning and alarm levels

# Initialize Temperature module with NTC thermistor
temp  = Temp(pin = temp_pin,      # ADC pin for temperature sensor
             normal_temp = 36     # Normal body temperature threshold in Celsius
)    

# Initialize Pulse Oximeter sensor via I2C communication
pulse = Pulse(
    sda_pin = pulse_sda,      # I2C SDA pin for pulse oximeter
    scl_pin = pulse_scl,      # I2C SCL pin for pulse oximeter  
    sample_rate = 100         # 100Hz sampling rate for heart rate and SpO2 measurement
)

# Initialize Buzzer to create various tones
buzzer = Buzzer(
    pin = buzz_pin           #Digital Output Pin for PWM
)