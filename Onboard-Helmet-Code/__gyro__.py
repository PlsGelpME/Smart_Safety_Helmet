# __gyro__.py - MPU6050 Interrupt Configuration Class
from machine import I2C, Pin
import time

class GyroSetup:
    # MPU6050 Register Definitions
    MPU6050_ADDR = 0x68  # I2C address of MPU6050 sensor
    PWR_MGMT_1 = 0x6B    # Power management register 1
    INT_PIN_CFG = 0x37   # Interrupt pin configuration register
    INT_ENABLE = 0x38    # Interrupt enable register
    INT_STATUS = 0x3A    # Interrupt status register
    FF_THR = 0x1D        # Free-Fall Threshold register
    FF_DUR = 0x1E        # Free-Fall Duration register
    WHO_AM_I = 0x75      # Device identification register
    
    def __init__(self, i2c_scl_pin, i2c_sda_pin, int_pin, i2c_bus=0):
        """
        Initialize GyroSetup with pin configuration
        
        Args:
            i2c_scl_pin: SCL pin number for I2C communication (default: 22)
            i2c_sda_pin: SDA pin number for I2C communication (default: 21)
            int_pin: Interrupt pin number (default: 4)
            i2c_bus: I2C bus number (default: 0)
        """
        # Initialize I2C communication with MPU6050 sensor
        self.i2c = I2C(i2c_bus, scl=i2c_scl_pin, sda=i2c_sda_pin, freq=400000)
        
        # Initialize interrupt pin as input with pull-up resistor
        self.int_pin = int_pin
        self.int_pin.init(Pin.IN, Pin.PULL_UP)
        
        # State variables to track sensor status
        self.free_fall_detected = False  # Flag for free-fall detection
        self.interrupt_enabled = False   # Flag for interrupt status
        self.initialized = False         # Flag for initialization status
        
        print("GyroSetup hardware initialized")
    
    def _write_reg(self, reg, value):
        """Write to MPU6050 register"""
        # Write single byte value to specified register address
        self.i2c.writeto_mem(self.MPU6050_ADDR, reg, bytes([value]))
    
    def _read_reg(self, reg):
        """Read from MPU6050 register"""
        # Read single byte from specified register address
        return self.i2c.readfrom_mem(self.MPU6050_ADDR, reg, 1)[0]
    
    def verify_connection(self):
        """Verify I2C communication with MPU6050"""
        try:
            # Read WHO_AM_I register to verify device identity
            who_am_i = self._read_reg(self.WHO_AM_I)
            if who_am_i == 0x68:
                print("MPU6050 connection verified")
                return True
            else:
                print(f"MPU6050 not found. WHO_AM_I returned: 0x{who_am_i:02x}")
                return False
        except OSError:
            print("I2C communication error. Check wiring.")
            return False
    
    def configure_freefall(self, threshold=0x10, duration=0x05):
        """
        Configure MPU6050 for free-fall detection
        
        Args:
            threshold: Free-fall detection threshold value (default: 0x10)
            duration: Free-fall detection duration value (default: 0x05)
            
        Returns:
            bool: True if configuration successful, raises exception otherwise
        """
        # First verify communication with sensor
        if not self.verify_connection():
            raise Exception("Cannot configure MPU6050: Communication failed")
        
        # Wake up sensor by clearing sleep bit in power management register
        self._write_reg(self.PWR_MGMT_1, 0x00)
        time.sleep_ms(100)  # Allow time for sensor to wake up
        
        # Configure interrupt pin: active low, latched until cleared
        self._write_reg(self.INT_PIN_CFG, 0x20)
        
        # Set free-fall detection parameters
        self._write_reg(self.FF_THR, threshold)  # Set sensitivity threshold
        self._write_reg(self.FF_DUR, duration)   # Set time duration
        
        # Enable free-fall interrupt (bit 7 in INT_ENABLE register)
        self._write_reg(self.INT_ENABLE, 0x80)
        
        # Update initialization status
        self.initialized = True
        print(f"Free-fall detection configured: Threshold=0x{threshold:02x}, Duration=0x{duration:02x}")
        return True
    
    def is_initialized(self):
        """Check if gyro is properly initialized"""
        return self.initialized
    
    def get_interrupt_status(self):
        """Read and return the INT_STATUS register"""
        # Returns current interrupt status to check for free-fall events
        return self._read_reg(self.INT_STATUS)