# max30100.py - MAX30100 Pulse Oximeter MicroPython Class
from machine import I2C, Pin
import time
import ustruct

class Pulse:
    """
    MAX30100 Pulse Oximeter and Heart-Rate Sensor Class
    Provides interface for reading heart rate and blood oxygen saturation (SpO2)
    Uses I2C communication protocol
    """
    
    # Register addresses [citation:5]
    REG_INTR_STATUS_1 = 0x00    # Interrupt status register 1
    REG_INTR_STATUS_2 = 0x01    # Interrupt status register 2
    REG_INTR_ENABLE_1 = 0x02    # Interrupt enable register 1
    REG_INTR_ENABLE_2 = 0x03    # Interrupt enable register 2
    REG_FIFO_WR_PTR = 0x04      # FIFO write pointer
    REG_OVF_COUNTER = 0x05      # FIFO overflow counter
    REG_FIFO_RD_PTR = 0x06      # FIFO read pointer
    REG_FIFO_DATA = 0x07        # FIFO data register (read sensor data here)
    REG_FIFO_CONFIG = 0x08      # FIFO configuration register
    REG_MODE_CONFIG = 0x09      # Operation mode configuration
    REG_SPO2_CONFIG = 0x0A      # SpO2 configuration (sample rate, LED pulse width)
    REG_LED1_PA = 0x0C          # LED1 (RED) pulse amplitude control
    REG_LED2_PA = 0x0D          # LED2 (IR) pulse amplitude control
    REG_PILOT_PA = 0x10         # Pilot LED pulse amplitude
    REG_MULTI_LED_CTRL1 = 0x11  # Multi-LED mode control 1
    REG_MULTI_LED_CTRL2 = 0x12  # Multi-LED mode control 2
    REG_TEMP_INTR = 0x1F        # Temperature integer part
    REG_TEMP_FRAC = 0x20        # Temperature fractional part
    REG_TEMP_CONFIG = 0x21      # Temperature configuration
    REG_PROX_INT_THRESH = 0x30  # Proximity interrupt threshold
    REG_REV_ID = 0xFE           # Revision ID register
    REG_PART_ID = 0xFF          # Part ID register (should read 0x11 for MAX30100)
    
    # Mode configurations [citation:1]
    MODE_HEART_RATE = 0x02      # Heart rate only mode
    MODE_SPO2 = 0x03            # SpO2 mode (heart rate + blood oxygen)
    
    # LED current settings [citation:5]
    # Controls LED brightness for different skin types/conditions
    LED_CURRENT_0MA = 0x00      # LED off
    LED_CURRENT_4_4MA = 0x01    # 4.4mA LED current
    LED_CURRENT_7_6MA = 0x02    # 7.6mA LED current
    LED_CURRENT_11MA = 0x03     # 11mA LED current
    LED_CURRENT_14_2MA = 0x04   # 14.2mA LED current
    LED_CURRENT_17_4MA = 0x05   # 17.4mA LED current
    LED_CURRENT_20_8MA = 0x06   # 20.8mA LED current
    LED_CURRENT_24MA = 0x07     # 24mA LED current
    LED_CURRENT_27_1MA = 0x08   # 27.1mA LED current
    LED_CURRENT_30_6MA = 0x09   # 30.6mA LED current
    LED_CURRENT_33_8MA = 0x0A   # 33.8mA LED current
    LED_CURRENT_37MA = 0x0B     # 37mA LED current
    LED_CURRENT_40_2MA = 0x0C   # 40.2mA LED current
    LED_CURRENT_43_6MA = 0x0D   # 43.6mA LED current
    LED_CURRENT_46_8MA = 0x0E   # 46.8mA LED current
    LED_CURRENT_50MA = 0x0F     # 50mA LED current (maximum)
    
    def __init__(self, i2c_bus=None, i2c_addr=0x57, sda_pin=21, scl_pin=22, 
                 fifo_samples=16, sample_rate=100):
        """
        Initialize MAX30100 pulse oximeter [citation:1][citation:5]
        
        Args:
            i2c_bus: I2C bus object (if None, creates new bus)
            i2c_addr: I2C address of MAX30100 (typically 0x57)
            sda_pin: SDA pin number for I2C communication
            scl_pin: SCL pin number for I2C communication
            fifo_samples: Number of samples in FIFO buffer (1-32)
            sample_rate: Sampling rate in Hz (50, 100, 167, 200, 400, 600, 800, 1000)
        """
        self.i2c_addr = i2c_addr
          
        # Initialize I2C bus [citation:3]
        if i2c_bus is None:
            # Create new I2C bus with specified pins and 400kHz frequency
            self.i2c = I2C(0, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=400000)
        else:
            # Use provided I2C bus
            self.i2c = i2c_bus
        
        # Sensor data buffers [citation:1]
        self.ir_buffer = []     # Infrared LED readings buffer
        self.red_buffer = []    # Red LED readings buffer
        self.buffer_size = 32   # Maximum buffer size for signal processing
        
        # Configuration parameters
        self.sample_rate = sample_rate      # Samples per second
        self.led_current_ir = self.LED_CURRENT_50MA   # IR LED current (50mA max)
        self.led_current_red = self.LED_CURRENT_50MA  # Red LED current (50mA max)
        self.mode = self.MODE_SPO2          # Default to SpO2 + heart rate mode
        
        # Data processing variables
        self.last_heart_rate = 0    # Last calculated heart rate (BPM)
        self.last_spo2 = 0          # Last calculated blood oxygen saturation (%)
        self.beat_detected = False  # Flag indicating heart beat detection
        
        # Initialize sensor hardware
        self._initialize_sensor()
        
        print("MAX30100 pulse oximeter initialized")
    
    def _write_register(self, reg, value):
        """
        Write value to sensor register
        
        Args:
            reg: Register address to write to
            value: Value to write (0-255)
            
        Returns:
            bool: True if write successful, False if I2C error
        """
        try:
            self.i2c.writeto_mem(self.i2c_addr, reg, bytes([value]))
            return True
        except OSError:
            print(f"I2C write error to register 0x{reg:02x}")
            return False
    
    def _read_register(self, reg, length=1):
        """
        Read value from sensor register
        
        Args:
            reg: Register address to read from
            length: Number of bytes to read
            
        Returns:
            bytes: Register value(s) or None if I2C error
        """
        try:
            return self.i2c.readfrom_mem(self.i2c_addr, reg, length)
        except OSError:
            print(f"I2C read error from register 0x{reg:02x}")
            return None
    
    def _initialize_sensor(self):
        """
        Initialize sensor with default configuration [citation:5]
        Sets up FIFO, sample rate, LED currents, and operation mode
        
        Returns:
            bool: True if initialization successful, False if sensor not found
        """
        # Reset sensor to default state
        self._write_register(self.REG_MODE_CONFIG, 0x40)
        time.sleep(0.1)  # Wait for reset to complete
        
        # Check if sensor is present by reading part ID [citation:3]
        part_id = self._read_register(self.REG_PART_ID)
        if part_id is None or part_id[0] != 0x11:  # MAX30100 part ID should be 0x11
            print("MAX30100 not found. Check wiring.")
            return False
        
        # Set FIFO configuration [citation:1]
        # Average 4 samples, rollover enabled (continue when full)
        fifo_config = 0x40 | (0x3 << 5)  # Sample average = 4, rollover enabled
        self._write_register(self.REG_FIFO_CONFIG, fifo_config)
        
        # Set mode configuration [citation:5]
        self.set_mode(self.MODE_SPO2)
        
        # Set SpO2 configuration (sample rate)
        self.set_sample_rate(self.sample_rate)
        
        # Set LED currents [citation:5]
        self.set_led_current(self.led_current_ir, self.led_current_red)
        
        # Clear FIFO buffers
        self._write_register(self.REG_FIFO_WR_PTR, 0x00)   # Reset write pointer
        self._write_register(self.REG_OVF_COUNTER, 0x00)   # Clear overflow counter
        self._write_register(self.REG_FIFO_RD_PTR, 0x00)   # Reset read pointer
        
        return True
    
    def set_mode(self, mode):
        """
        Set operating mode [citation:1]
        
        Args:
            mode: Operation mode (MODE_HEART_RATE or MODE_SPO2)
        """
        self.mode = mode
        self._write_register(self.REG_MODE_CONFIG, mode)
    
    def set_sample_rate(self, sample_rate):
        """
        Set sampling rate [citation:1]
        
        Args:
            sample_rate: Sampling rate in Hz (50, 100, 167, 200, 400, 600, 800, 1000)
        """
        self.sample_rate = sample_rate
        
        # Map sample rate to register value [citation:5]
        rate_codes = {
            50: 0x00, 100: 0x01, 167: 0x02, 200: 0x03, 
            400: 0x04, 600: 0x05, 800: 0x06, 1000: 0x07
        }
        
        if sample_rate in rate_codes:
            # Read current SpO2 configuration
            spo2_config = self._read_register(self.REG_SPO2_CONFIG)
            if spo2_config:
                # Preserve existing bits and set new sample rate
                new_config = (spo2_config[0] & 0xE3) | (rate_codes[sample_rate] << 2)
                self._write_register(self.REG_SPO2_CONFIG, new_config)
    
    def set_led_current(self, ir_current, red_current):
        """
        Set LED currents [citation:5]
        Higher currents work better for darker skin or poor contact
        
        Args:
            ir_current: IR LED current (use LED_CURRENT_* constants)
            red_current: Red LED current (use LED_CURRENT_* constants)
        """
        self.led_current_ir = ir_current
        self.led_current_red = red_current
        
        # Write LED current settings to registers
        self._write_register(self.REG_LED1_PA, ir_current)   # IR LED
        self._write_register(self.REG_LED2_PA, red_current)  # Red LED
    
    def read_sensor(self):
        """
        Read data from sensor FIFO [citation:1]
        Reads one sample pair (IR and Red) from the FIFO buffer
        
        Returns:
            tuple: (ir_value, red_value) or (None, None) if no data or error
        """
        try:
            # Read FIFO data (4 bytes: IR high, IR low, RED high, RED low)
            fifo_data = self._read_register(self.REG_FIFO_DATA, 4)
            if fifo_data is None or len(fifo_data) != 4:
                return None, None
            
            # Convert bytes to 16-bit values [citation:1]
            ir_value = (fifo_data[0] << 8) | fifo_data[1]   # Combine high and low bytes
            red_value = (fifo_data[2] << 8) | fifo_data[3]  # Combine high and low bytes
            
            # Update buffers for signal processing
            self._update_buffers(ir_value, red_value)
            
            return ir_value, red_value
            
        except Exception as e:
            print(f"Error reading sensor: {e}")
            return None, None
    
    def _update_buffers(self, ir_value, red_value):
        """
        Update data buffers with new readings
        Maintains rolling buffer for signal processing algorithms
        
        Args:
            ir_value: New IR sensor reading
            red_value: New Red sensor reading
        """
        self.ir_buffer.append(ir_value)
        self.red_buffer.append(red_value)
        
        # Maintain buffer size by removing oldest values
        if len(self.ir_buffer) > self.buffer_size:
            self.ir_buffer.pop(0)
            self.red_buffer.pop(0)
    
    def read_temperature(self):
        """
        Read die temperature from sensor
        
        Returns:
            float: Temperature in Celsius or None if error
        """
        # Trigger temperature reading
        self._write_register(self.REG_TEMP_CONFIG, 0x01)
        
        # Wait for temperature conversion to complete
        time.sleep(0.1)
        
        # Read temperature data
        temp_int = self._read_register(self.REG_TEMP_INTR)   # Integer part
        temp_frac = self._read_register(self.REG_TEMP_FRAC)  # Fractional part
        
        if temp_int is None or temp_frac is None:
            return None
        
        # Calculate temperature (integer part + fractional part)
        temperature = temp_int[0] + (temp_frac[0] * 0.0625)  # Each LSB = 0.0625°C
        return temperature
    
    def calculate_heart_rate(self):
        """
        Basic heart rate calculation from IR data [citation:2][citation:4]
        Uses simple peak detection algorithm on IR signal
        Note: This is a simplified implementation - consider more advanced algorithms for production
        
        Returns:
            float: Heart rate in beats per minute (BPM)
        """
        if len(self.ir_buffer) < 10:
            return 0  # Not enough data for calculation
        
        # Simple peak detection algorithm
        threshold = sum(self.ir_buffer) / len(self.ir_buffer)  # Dynamic threshold
        peaks = 0
        
        # Find peaks in IR signal (local maxima above threshold)
        for i in range(1, len(self.ir_buffer) - 1):
            if (self.ir_buffer[i] > self.ir_buffer[i-1] and     # Higher than previous
                self.ir_buffer[i] > self.ir_buffer[i+1] and     # Higher than next
                self.ir_buffer[i] > threshold * 1.1):           # Above noise threshold
                peaks += 1
        
        # Calculate BPM based on peaks in buffer
        if peaks > 1:
            time_window = len(self.ir_buffer) / self.sample_rate  # Buffer duration in seconds
            bpm = (peaks - 1) * (60.0 / time_window)  # Convert to beats per minute
            self.last_heart_rate = bpm
            self.beat_detected = True
        else:
            self.beat_detected = False
        
        return self.last_heart_rate
    
    def calculate_spo2(self):
        """
        Basic SpO2 calculation from red and IR ratios [citation:2]
        Uses ratio-of-ratios method (AC/DC components)
        Note: This requires proper calibration for accurate results
        
        Returns:
            float: Blood oxygen saturation percentage (0-100%)
        """
        if len(self.red_buffer) < 10 or len(self.ir_buffer) < 10:
            return 0  # Not enough data for calculation
        
        # Calculate AC components (pulsatile, varies with heartbeat)
        red_ac = max(self.red_buffer) - min(self.red_buffer)   # Red AC component
        ir_ac = max(self.ir_buffer) - min(self.ir_buffer)      # IR AC component
        
        # Calculate DC components (non-pulsatile, baseline)
        red_dc = sum(self.red_buffer) / len(self.red_buffer)   # Red DC component
        ir_dc = sum(self.ir_buffer) / len(self.ir_buffer)      # IR DC component
        
        if red_dc == 0 or ir_dc == 0:
            return 0  # Avoid division by zero
        
        # Calculate ratio of ratios (R-value) [citation:2]
        ratio = (red_ac / red_dc) / (ir_ac / ir_dc)
        
        # Empirical formula for SpO2 (requires calibration) [citation:2]
        spo2 = 110 - (25 * ratio)
        spo2 = max(70, min(100, spo2))  # Clamp to reasonable range (70-100%)
        
        self.last_spo2 = spo2
        return spo2
    
    def get_sensor_data(self):
        """
        Get comprehensive sensor data
        Reads current sensor values and calculates all metrics
        
        Returns:
            dict: Sensor readings and calculated values or None if error
        """
        # Read raw sensor data
        ir, red = self.read_sensor()
        
        if ir is None or red is None:
            return None  # No data available
        
        # Calculate derived metrics
        heart_rate = self.calculate_heart_rate()
        spo2 = self.calculate_spo2()
        temperature = self.read_temperature()
        
        return {
            'ir_value': ir,                 # Raw IR sensor reading
            'red_value': red,               # Raw Red sensor reading
            'heart_rate': heart_rate,       # Calculated heart rate (BPM)
            'spo2': spo2,                   # Calculated blood oxygen (%)
            'temperature': temperature,     # Sensor temperature (°C)
            'beat_detected': self.beat_detected,  # Heart beat detection flag
            'timestamp': time.time()        # Measurement timestamp
        }
    
    def get_sensor_info(self):
        """
        Get sensor information and current configuration
        
        Returns:
            dict: Sensor identification and configuration details
        """
        part_id = self._read_register(self.REG_PART_ID)
        rev_id = self._read_register(self.REG_REV_ID)
        
        return {
            'part_id': part_id[0] if part_id else None,        # Should be 0x11
            'revision_id': rev_id[0] if rev_id else None,      # Chip revision
            'mode': self.mode,                                 # Current operation mode
            'sample_rate': self.sample_rate,                   # Samples per second
            'led_current_ir': self.led_current_ir,             # IR LED current setting
            'led_current_red': self.led_current_red,           # Red LED current setting
            'buffer_size': len(self.ir_buffer)                 # Current data buffer size
        }