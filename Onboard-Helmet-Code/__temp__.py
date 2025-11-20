from machine import ADC
from math import log
from time import sleep_ms

class Temp:
    """
    Temperature sensor class for NTC thermistor measurements
    Uses Steinhart-Hart equation for temperature calculation
    """
    
    def __init__(self, pin, normal_temp = 39):
        # Input parameters
        self.pin = pin  # ADC pin for reading thermistor voltage
        self.threshold = normal_temp  # Temperature threshold for alerts
        
        # Temperature Coefficient constants for NTC thermistor
        self.beta = 3950  # Beta coefficient of NTC thermistor
        self.R0 = 10000   # Resistance at reference temperature (25°C)
        self.T0 = 298.15  # Reference temperature in Kelvin (25°C)
        self.R_Fixed = 5800  # Fixed resistor value in voltage divider
        
        # Temperature values in different units
        self.cel  = 0  # Temperature in Celsius
        self.fahr = 0  # Temperature in Fahrenheit
        self.kel  = 0  # Temperature in Kelvin
        
    def calibration(self, beta, R_fixed):
        """
        Calibrate the thermistor parameters
        
        Args:
            beta: Beta coefficient for the specific NTC thermistor
            R_fixed: Value of the fixed resistor in the voltage divider
        """
        # Set Beta value and R_Fixed values here for calibration
        self.beta = beta
        self.R_Fixed = R_fixed
    
    def getTemp(self, unit = 1):
        """
        Read and calculate temperature from NTC thermistor
        
        Args:
            unit: Temperature unit code
                  0 - Kelvin
                  1 - Celsius  
                  2 - Fahrenheit
                  Default return unit is Celsius.
        
        Returns:
            float: Temperature in requested unit
        """
        # Read multiple ADC samples and average for noise reduction
        adc_val = 0
        for _ in range(100):
            adc_val += self.pin.read()
            sleep_ms(10)  # Small delay between readings
            
        # Calculate average ADC value
        adc_val //= 100
        
        # Convert ADC value to voltage (assuming 12-bit ADC with 3.3V reference)
        voltage = (3.3/4095)*adc_val
        
        # Calculate NTC resistance using voltage divider formula
        r_ntc = (self.R_Fixed*(3.3 - voltage))/voltage
        
        # Calculate temperature using Steinhart-Hart equation (simplified beta version)
        temp  = 1/((1/self.T0) + (1/self.beta)*log(r_ntc/self.R0))
        
        # Convert to different temperature units
        self.kel  = temp        # Kelvin (already calculated)
        self.cel  = self.kel - 273.15  # Convert Kelvin to Celsius
        self.fahr = (self.cel * 9/5) + 32  # Convert Celsius to Fahrenheit
        
        # Array for easy unit selection
        all_units = [self.kel, self.cel, self.fahr]
        
        return all_units[unit]  # Return temperature in requested unit
    
    def istemp(self):
        """
        Check if current temperature exceeds threshold
        
        Returns:
            bool: True if temperature > threshold, False otherwise
        """
        temp = self.temp()  # Get current temperature (note: should be self.getTemp())
        if temp > self.threshold:
            return True
        
        return False
    
    def setThreshold(self, t):
        """
        Set temperature threshold for alerts
        
        Args:
            t: New threshold temperature value
        """
        self.threshold = t