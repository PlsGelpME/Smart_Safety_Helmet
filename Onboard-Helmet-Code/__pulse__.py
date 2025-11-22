# __pulse__.py - Simplified MAX30100 Pulse Oximeter Class
from machine import I2C, Pin
import time

class Pulse:
    """
    Simplified MAX30100 Pulse Oximeter Class
    Provides essential heart rate and SpO2 monitoring
    """
    
    # Essential register addresses
    REG_INTR_STATUS_1 = 0x00
    REG_INTR_ENABLE_1 = 0x02
    REG_FIFO_WR_PTR = 0x04
    REG_OVF_COUNTER = 0x05
    REG_FIFO_RD_PTR = 0x06
    REG_FIFO_DATA = 0x07
    REG_FIFO_CONFIG = 0x08
    REG_MODE_CONFIG = 0x09
    REG_SPO2_CONFIG = 0x0A
    REG_LED1_PA = 0x0C  # IR LED
    REG_LED2_PA = 0x0D  # Red LED
    REG_PART_ID = 0xFF
    
    # Mode configurations
    MODE_SPO2 = 0x03
    
    # LED current settings
    LED_CURRENT_24MA = 0x06
    LED_CURRENT_27MA = 0x08
    LED_CURRENT_50MA = 0x0F
    
    def __init__(self, sda_pin=21, scl_pin=22, i2c_addr=0x57, sample_rate=100):
        """
        Initialize pulse oximeter
        
        Args:
            sda_pin: I2C SDA pin
            scl_pin: I2C SCL pin  
            i2c_addr: I2C address
            sample_rate: Sampling rate in Hz
        """
        self.i2c_addr = i2c_addr
        
        # Initialize I2C
        self.i2c = I2C(0, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=400000)
        
        # Data buffers
        self.ir_buffer = []
        self.red_buffer = []
        self.buffer_size = 32
        
        # Configuration
        self.sample_rate = sample_rate
        self.led_current = self.LED_CURRENT_27MA
        
        # Initialize sensor
        self._initialize_sensor()
        
        print("Pulse oximeter initialized")
    
    def _write_register(self, reg, value):
        """Write to sensor register"""
        try:
            self.i2c.writeto_mem(self.i2c_addr, reg, bytes([value]))
            return True
        except:
            return False
    
    def _read_register(self, reg, length=1):
        """Read from sensor register"""
        try:
            return self.i2c.readfrom_mem(self.i2c_addr, reg, length)
        except:
            return None
    
    def _initialize_sensor(self):
        """Initialize sensor with basic configuration"""
        # Reset sensor
        self._write_register(self.REG_MODE_CONFIG, 0x40)
        time.sleep(0.1)
        
        # Verify sensor
        part_id = self._read_register(self.REG_PART_ID)
        if part_id is None or part_id[0] != 0x11:
            print("MAX30100 not found")
            return False
        
        # Configure FIFO
        self._write_register(self.REG_FIFO_CONFIG, 0x40)  # Rollover enabled
        
        # Set mode
        self._write_register(self.REG_MODE_CONFIG, self.MODE_SPO2)
        
        # Set LED currents
        self._write_register(self.REG_LED1_PA, self.led_current)  # IR LED
        self._write_register(self.REG_LED2_PA, self.led_current)  # Red LED
        
        # Clear FIFO
        self._write_register(self.REG_FIFO_WR_PTR, 0x00)
        self._write_register(self.REG_OVF_COUNTER, 0x00)
        self._write_register(self.REG_FIFO_RD_PTR, 0x00)
        
        return True
    
    def read_sensor(self):
        """
        Read raw sensor data from FIFO
        
        Returns:
            tuple: (ir_value, red_value) or (None, None) if error
        """
        try:
            # Read 4 bytes from FIFO
            fifo_data = self._read_register(self.REG_FIFO_DATA, 4)
            if fifo_data is None or len(fifo_data) != 4:
                return None, None
            
            # Convert to 16-bit values
            ir_value = (fifo_data[0] << 8) | fifo_data[1]
            red_value = (fifo_data[2] << 8) | fifo_data[3]
            
            # Update buffers
            self._update_buffers(ir_value, red_value)
            
            return ir_value, red_value
            
        except:
            return None, None
    
    def _update_buffers(self, ir_value, red_value):
        """Update data buffers with new readings"""
        self.ir_buffer.append(ir_value)
        self.red_buffer.append(red_value)
        
        # Maintain buffer size
        if len(self.ir_buffer) > self.buffer_size:
            self.ir_buffer.pop(0)
            self.red_buffer.pop(0)
    
    def calculate_heart_rate(self):
        """
        Calculate heart rate from IR data using peak detection
        
        Returns:
            float: Heart rate in BPM
        """
        if len(self.ir_buffer) < 10:
            return 0
        
        # Simple peak detection
        threshold = sum(self.ir_buffer) / len(self.ir_buffer)
        peaks = 0
        
        for i in range(1, len(self.ir_buffer) - 1):
            if (self.ir_buffer[i] > self.ir_buffer[i-1] and
                self.ir_buffer[i] > self.ir_buffer[i+1] and
                self.ir_buffer[i] > threshold * 1.1):
                peaks += 1
        
        # Calculate BPM
        if peaks > 1:
            time_window = len(self.ir_buffer) / self.sample_rate
            bpm = (peaks - 1) * (60.0 / time_window)
            return max(40, min(180, bpm))  # Clamp to reasonable range
        
        return 0
    
    def calculate_spo2(self):
        """
        Calculate blood oxygen saturation
        
        Returns:
            float: SpO2 percentage
        """
        if len(self.red_buffer) < 10 or len(self.ir_buffer) < 10:
            return 0
        
        # Calculate AC and DC components
        red_ac = max(self.red_buffer) - min(self.red_buffer)
        ir_ac = max(self.ir_buffer) - min(self.ir_buffer)
        
        red_dc = sum(self.red_buffer) / len(self.red_buffer)
        ir_dc = sum(self.ir_buffer) / len(self.ir_buffer)
        
        if red_dc == 0 or ir_dc == 0:
            return 0
        
        # Calculate ratio and SpO2
        ratio = (red_ac / red_dc) / (ir_ac / ir_dc)
        spo2 = 110 - (25 * ratio)
        
        # Clamp to reasonable range
        return max(70, min(100, spo2))
    
    def get_sensor_data(self):
        """
        Get comprehensive sensor data
        
        Returns:
            dict: Sensor readings and calculated values
        """
        ir, red = self.read_sensor()
        
        if ir is None or red is None:
            return None
        
        heart_rate = self.calculate_heart_rate()
        spo2 = self.calculate_spo2()
        
        return {
            'ir_value': ir,
            'red_value': red,
            'heart_rate': heart_rate,
            'spo2': spo2,
            'timestamp': time.time()
        }
    
    def set_led_current(self, current):
        """
        Set LED current for both IR and Red LEDs
        
        Args:
            current: LED current value (use LED_CURRENT_* constants)
        """
        self.led_current = current
        self._write_register(self.REG_LED1_PA, current)  # IR LED
        self._write_register(self.REG_LED2_PA, current)  # Red LED

# Simple usage example
if __name__ == "__main__":
    pulse = Pulse(sda_pin=21, scl_pin=22)
    
    print("Testing pulse oximeter...")
    for i in range(50):
        data = pulse.get_sensor_data()
        if data:
            print(f"HR: {data['heart_rate']:.1f} BPM, SpO2: {data['spo2']:.1f}%")
        time.sleep(0.1)
