# __gas__.py - Gas Sensor Class for MQ2 Gas Detection
from machine import Pin, ADC, RTC
import time

class Gas:
    def __init__(self, analog_pin, power_pin,
                 warning_threshold = 1500, alarm_threshold = 2500,
                 warm_up_time=15, operating_hours=(8, 18)):
        """
        Gas sensor class for MQ2 gas detection with power management
        Implements hourly monitoring during specified operating hours with automatic power cycling
        
        Args:
            analog_pin: Pre-configured ADC object for gas concentration reading
            power_pin: Pre-configured Pin object for sensor power control
            warning_threshold: ADC value that triggers warning status (default: 1500)
            alarm_threshold: ADC value that triggers alarm status (default: 2500)
            warm_up_time: Seconds for sensor stabilization after power on (default: 15)
            operating_hours: Tuple (start_hour, end_hour) for daily monitoring window
        """
        self.adc = analog_pin  # Pre-configured ADC object for gas reading
        self.power_pin = power_pin  # Pre-configured Pin object for power control
        self.power_pin.value(0)  # Start with sensor powered OFF for power savings
        
        self.warm_up_time = warm_up_time  # Sensor stabilization time after power on
        self.operating_start, self.operating_end = operating_hours  # Monitoring time window
        
        # Gas concentration thresholds for status determination
        self.warning_threshold = warning_threshold  # Level for warning status
        self.alarm_threshold = alarm_threshold  # Level for alarm/emergency status
        
        self.last_reading = None  # Stores the most recent gas reading
        
        print(f"MQ2 Hourly Monitor: {operating_hours[0]}:00-{operating_hours[1]}:00")
    
    def should_monitor_now(self):
        """
        Check if current time is within operating hours and at start of hour
        Ensures gas monitoring only occurs during specified daily window
        
        Returns:
            bool: True if should monitor now, False otherwise
        """
        rtc = RTC()  # Real-time clock for time checking
        current_hour = rtc.datetime()[4]  # Get current hour (0-23)
        current_minute = rtc.datetime()[5]  # Get current minute (0-59)
        
        # Check if within operating hours and at the start of an hour
        if self.operating_start <= current_hour < self.operating_end:
            return current_minute == 0  # Only monitor at :00 minutes
        return False
    
    def _get_reading_status(self, value):
        """
        Determine gas level status based on threshold values
        Converts raw ADC reading to meaningful status indicator
        
        Args:
            value: Raw ADC reading from gas sensor
            
        Returns:
            str: Status string - "NORMAL", "WARNING", or "ALARM"
        """
        if value >= self.alarm_threshold:
            return "ALARM"  # Emergency level gas concentration
        elif value >= self.warning_threshold:
            return "WARNING"  # Elevated gas concentration
        else:
            return "NORMAL"  # Safe gas concentration levels
    
    def set_thresholds(self, warning, alarm):
        """
        Update gas concentration thresholds for status determination
        Allows dynamic adjustment of sensitivity levels
        
        Args:
            warning: New warning threshold ADC value
            alarm: New alarm threshold ADC value
        """
        self.warning_threshold = warning
        self.alarm_threshold = alarm
        print(f"Thresholds updated - Warning: {warning}, Alarm: {alarm}")
        
    def take_reading(self):
        """
        Take a single gas reading with full power management
        Powers on sensor, waits for stabilization, takes multiple samples, then powers off
        Implements complete power cycling for energy efficiency
        
        Returns:
            dict: Gas reading data with value, status, timestamp, and raw samples
        """
        print("Powering on MQ2 for hourly reading...")
        
        # Power on sensor - enables heater and sensing circuitry
        self.power_pin.value(1)
        
        try:
            # Warm-up period for sensor stabilization
            # MQ2 requires time for heater to reach operating temperature
            print(f"Warming up for {self.warm_up_time}s...")
            time.sleep(self.warm_up_time)
            
            # Take multiple samples for accuracy and noise reduction
            # Averages 10 samples over 4.5 seconds for stable reading
            samples = []
            for i in range(10):
                sample = self.adc.read()  # Read current gas concentration
                samples.append(sample)
                if i < 4:  # No delay after last sample
                    time.sleep(0.5)  # 500ms between samples
            
            # Calculate average of all samples for final reading
            avg_reading = sum(samples) / len(samples)
            self.last_reading = avg_reading  # Store for potential reuse
            
            # Determine status based on thresholds
            status = self._get_reading_status(avg_reading)
            
            return {
                'value': avg_reading,  # Average ADC reading
                'status': status,  # "NORMAL", "WARNING", or "ALARM"
                'timestamp': time.time(),  # Unix timestamp of reading
                'samples': samples  # Raw samples for debugging/analysis
            }
            
        finally:
            # Always power off sensor regardless of success or failure
            # Critical for power management in battery-operated devices
            self.power_pin.value(0)
            print("MQ2 powered off")