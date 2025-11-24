from machine import ADC,Pin
from __gas__ import Gas
from __gyro__ import GyroSetup
#from __GPS__ import GPS
from __pulse__ import Pulse
from __buzzer__ import Buzzer
from __temp__ import Temp

class boot:
    
    def __init__(self):
        """
        Pin declarations for all sensors and peripherals
        Enter pin numbers here according to your ESP32 wiring configuration
        """
        self.temp_pin  = ADC(36) # Analog Pin for temperature sensor - Can't use 25,26,27 as we are using WiFi. Read MicroPython ADC documentation.
        self.gas_pin   = ADC(39) # Analog pin for gas sensor reading
        self.gas_pwr   = Pin(13) # Digital pin to control gas sensor power
        #self.gps_pwr   = Pin(14) # Digital pin to control GPS module power
        #self.gps_rx    = 3       # UART RX pin for GPS data reception
        #self.gps_tx    = 1       # UART TX pin for GPS data transmission
        self.gyro_sda  = Pin(21) # I2C SDA pin for gyroscope (I2C channel 1)
        self.gyro_scl  = Pin(22) # I2C SCL pin for gyroscope (I2C channel 1)
        self.gyro_int  = Pin(19) # Interrupt pin from gyroscope for free-fall detection
        self.pulse_sda = Pin(21) # I2C SDA pin for pulse oximeter (I2C channel 2)
        self.pulse_scl = Pin(22) # I2C SCL pin for pulse oximeter (I2C channel 2)
        self.frc_pin   = Pin(32) # Digital input pin for force sensor
        self.buzz_pin  = Pin(23) # Digital output pin for buzzer control

        # Configure ADC attenuation for full 0-3.3V range reading
        self.temp_pin.atten(ADC.ATTN_11DB)  # 11dB attenuation allows 0-3.3V range
        self.gas_pin.atten(ADC.ATTN_11DB)   # 11dB attenuation allows 0-3.3V range

        """Sensor Setup and Object instantiation """
        # MPU6050 Gyroscope setup with free-fall detection
        self.gyro = GyroSetup(
            i2c_scl_pin=self.gyro_scl,  # I2C clock pin for gyroscope
            i2c_sda_pin=self.gyro_sda,  # I2C data pin for gyroscope  
            int_pin=self.gyro_int       # Interrupt pin for free-fall detection
        )
        # Configure free-fall detection with threshold and duration parameters
        self.gyro.configure_freefall(threshold=0x10, duration=0x05) # threshold = 0.16g force and 5 ms duration

        # Initialize GPS module - it starts powered OFF for power saving
        '''
        self.gps = GPS(
            power_pin = self.gps_pwr,    # GPIO pin controlling GPS power (enable/disable)
            rx_pin = self.gps_rx,        # GPS TX -> ESP32 RX (data reception from GPS)
            tx_pin = self.gps_tx,        # ESP32 TX -> GPS RX (optional, for GPS configuration)
            baudrate = 9600         # Communication baud rate with GPS module
        )
        '''

        # Initialize gas sensor with optional power control for power management
        self.gas_sensor = Gas(
            analog_pin = self.gas_pin,    # ADC pin for reading gas sensor analog value
            power_pin = self.gas_pwr,      # GPIO pin to control sensor power (optional power saving)
        )

        # Set appropriate gas concentration thresholds for warning and alarm levels
        self.gas_sensor.set_threshold(warning=1500, alarm=2500)  # ADC values for warning and alarm levels

        # Initialize Temperature module with NTC thermistor
        self.temp  = Temp(pin = self.temp_pin,      # ADC pin for temperature sensor
                     normal_temp = 36     # Normal body temperature threshold in Celsius
        )    

        # Initialize Pulse Oximeter sensor via I2C communication
        self.pulse = Pulse(
            sda_pin = self.pulse_sda,      # I2C SDA pin for pulse oximeter
            scl_pin = self.pulse_scl,      # I2C SCL pin for pulse oximeter  
            sample_rate = 100         # 100Hz sampling rate for heart rate and SpO2 measurement
        )

        # Initialize Buzzer to create various tones
        self.buzzer = Buzzer(
            pin = self.buzz_pin           #Digital Output Pin for PWM
        )
    
    def unpack_globals(self):
        return (self.gyro, self.gas_sensor, self.temp, self.pulse, self.buzzer, self.frc_pin)