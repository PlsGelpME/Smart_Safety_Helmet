# gps_module.py - On-demand GPS Class for Neo-6M GPS Module
from machine import UART, Pin
import time

class GPS:
    def __init__(self, power_pin, rx_pin, tx_pin, uart_num=2, baudrate=9600):
        """
        GPS class for Neo-6M module with on-demand power management
        Provides location acquisition with automatic power cycling to conserve energy
        
        Args:
            power_pin: GPIO pin for controlling GPS module power (None for always powered)
            rx_pin: UART RX pin for receiving GPS data (connects to GPS TX)
            tx_pin: UART TX pin for sending commands to GPS (optional, for configuration)
            uart_num: UART peripheral number (1 or 2 on ESP32)
            baudrate: Communication baud rate with GPS module (typically 9600)
        """
        # Initialize UART communication with GPS module
        self.uart = UART(uart_num, baudrate=baudrate, rx=rx_pin, tx=tx_pin)
        self.is_powered = False  # Track current power state
        self.last_fix = None  # Store last successful GPS position
        self.last_fix_time = 0  # Timestamp of last successful fix
        self.fix_timeout = 45  # Maximum seconds to wait for GPS fix
        
        self.power_pin = None
        if power_pin is not None:
            self.power_pin = Pin(power_pin, Pin.OUT)  # Power control pin
            self.power_pin.value(0)  # Start with GPS powered OFF for power savings
            self.is_powered = False
            
        print("OnDemandGPS initialized (powered OFF)")
    
    def power_on(self):
        """Power on GPS module and prepare for data acquisition"""
        if self.power_pin and not self.is_powered:
            self.power_pin.value(1)  # Apply power to GPS module
            time.sleep(1.5)  # Allow time for GPS to boot and initialize
            self.is_powered = True
            # Clear any stale data from UART buffer to start fresh
            if self.uart.any():
                self.uart.read()
    
    def power_off(self):
        """Power off GPS module to conserve energy"""
        if self.power_pin and self.is_powered:
            self.power_pin.value(0)  # Remove power from GPS module
            self.is_powered = False
    
    def read_nmea_data(self):
        """
        Read available NMEA data from GPS module
        Checks UART buffer for incoming GPS sentences
        
        Returns:
            str: Decoded NMEA sentence or None if no data available
        """
        if not self.is_powered:
            return None  # Cannot read if powered off
            
        if self.uart.any():
            try:
                data = self.uart.readline()  # Read line of NMEA data
                if data:
                    return data.decode('utf-8').strip()  # Convert bytes to string
            except:
                pass  # Silently handle decoding errors
        return None
    
    def get_position(self, timeout=None):
        """
        Acquire current GPS position with full power management
        Powers on GPS, waits for fix, returns position, then powers off
        
        Args:
            timeout: Maximum seconds to wait for fix (uses default if None)
            
        Returns:
            dict: Position data or None if timeout or error
        """
        if timeout is None:
            timeout = self.fix_timeout  # Use default timeout if not specified
        
        self.power_on()  # Ensure GPS is powered on
        print(f"Acquiring GPS fix (timeout: {timeout}s)...")
        
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                nmea_data = self.read_nmea_data()  # Check for new GPS data
                
                # Check if valid position fix is available
                if nmea_data and self._is_valid_gga_fix(nmea_data):
                    position = self._parse_gga_sentence(nmea_data)
                    if position:
                        # Store successful fix for caching
                        self.last_fix = position
                        self.last_fix_time = time.time()
                        print("GPS fix acquired!")
                        return position
                
                time.sleep(1)  # Check for data every second
                
                # Progress indication every 10 seconds
                elapsed = time.time() - start_time
                if int(elapsed) % 10 == 0:
                    print(f"  ...{int(elapsed)}s elapsed")
            
            print("GPS fix timeout")  # No fix within timeout period
            return None
            
        except Exception as e:
            print(f"GPS error: {e}")  # Handle any acquisition errors
            return None
        finally:
            # Always power off GPS regardless of success or failure
            # Critical for power management in battery-operated devices
            self.power_off()
    
    def get_position_cached(self, cache_time=300, timeout=None):
        """
        Get position using cache if recent fix is available
        Avoids unnecessary GPS power cycles if recent position is still valid
        
        Args:
            cache_time: Maximum age of cached fix in seconds (default 5 minutes)
            timeout: Maximum wait for new fix if cache is stale
            
        Returns:
            dict: Position data or None if no fix available
        """
        # Return cached position if it's still fresh enough
        if (self.last_fix and 
            time.time() - self.last_fix_time < cache_time):
            print("Using cached GPS position")
            return self.last_fix
        
        # Otherwise acquire new position fix
        return self.get_position(timeout)
    
    def _is_valid_gga_fix(self, nmea_data):
        """
        Check if GGA sentence contains valid position fix
        GGA sentences provide essential fix data including position and quality
        
        Args:
            nmea_data: Raw NMEA sentence string
            
        Returns:
            bool: True if sentence is valid GGA with active fix
        """
        return (nmea_data.startswith('$GPGGA') and  # GGA sentence identifier
                ',A,' in nmea_data)  # 'A' indicates active/valid fix
    
    def _parse_gga_sentence(self, gga_data):
        """
        Parse GGA NMEA sentence into structured position data
        Extracts latitude, longitude, altitude, and fix quality information
        
        Args:
            gga_data: GGA NMEA sentence string
            
        Returns:
            dict: Structured position data or None if invalid
        """
        try:
            parts = gga_data.split(',')  # Split sentence into fields
            if len(parts) < 10 or parts[6] == '0':  # Fix quality 0 = invalid
                return None
            
            return {
                'timestamp': parts[1],  # UTC time of fix (HHMMSS.SS)
                'latitude': f"{parts[2]} {parts[3]}",  # Latitude with direction
                'longitude': f"{parts[4]} {parts[5]}",  # Longitude with direction
                'fix_quality': parts[6],  # Fix quality indicator (0-2)
                'satellites': parts[7],  # Number of satellites used
                'altitude': f"{parts[9]} {parts[10]}",  # Altitude with units
                'raw': gga_data  # Original NMEA sentence for debugging
            }
        except:
            return None  # Handle any parsing errors gracefully
    
    def quick_status(self):
        """
        Quick diagnostic check of GPS module functionality
        Powers on briefly to verify GPS is communicating and receiving data
        Useful for debugging and system health checks
        """
        self.power_on()
        time.sleep(2)  # Brief period to check for data
        
        try:
            # Read a few sentences to verify GPS is working
            for _ in range(5):
                data = self.read_nmea_data()
                if data:
                    print(f"GPS data: {data[:50]}...")  # Show first 50 chars
                time.sleep(0.5)
        finally:
            self.power_off()  # Always power off after diagnostic