import time

# Initialize UART with both TX and RX connected
uart = UART(2, baudrate=9600, rx=16, tx=17) # Use UART2 on ESP32

# --- DEFINE THE UBX CONFIGURATION PAYLOADS ---
# This is a standard UBX-CFG-MSG packet structure.

# 1. Command to disable ALL NMEA sentences
# UBX-CFG-MSG: Set Message Rate(s)
# This command structure: [Class, ID, Rate]
# Rate: 0 = Disable, 1 = Enable on I2C, ... , 6 = Enable on UART1
disable_gsv = b'\xb5\x62\x06\x01\x08\x00\xf0\x03\x00\x00\x00\x00\x00\x00\x03\x39' # GPGSV
disable_rmc = b'\xb5\x62\x06\x01\x08\x00\xf0\x04\x00\x00\x00\x00\x00\x00\x04\x46' # GPRMC
disable_vtg = b'\xb5\x62\x06\x01\x08\x00\xf0\x05\x00\x00\x00\x00\x00\x00\x05\x4f' # GPVTG
disable_gll = b'\xb5\x62\x06\x01\x08\x00\xf0\x01\x00\x00\x00\x00\x00\x00\x01\x2b' # GPGLL
disable_gsa = b'\xb5\x62\x06\x01\x08\x00\xf0\x02\x00\x00\x00\x00\x00\x00\x02\x32' # GPGSA

# 2. Command to enable ONLY the GGA sentence
enable_gga = b'\xb5\x62\x06\x01\x08\x00\xf0\x00\x00\x06\x00\x00\x00\x00\x04\x16' # GPGGA, Rate=6 (Enable on UART1)

# 3. Command to SAVE the configuration to Battery-Backed RAM (non-volatile memory)
save_config = b'\xb5\x62\x06\x09\x0d\x00\x00\x00\x00\x00\xff\xff\x00\x00\x00\x00\x00\x00\x03\x1b\x9a'

def send_ubx_packet(payload):
    """Sends a UBX packet over UART and waits a bit."""
    print("Sending command...")
    uart.write(payload)
    time.sleep(0.5) # Short delay

print("Starting Neo-6M configuration to output only GGA...")
time.sleep(2) # Wait for module to boot

# --- SEND THE DISABLE COMMANDS ---
print("Disabling all NMEA sentences...")
send_ubx_packet(disable_gsv)
send_ubx_packet(disable_rmc)
send_ubx_packet(disable_vtg)
send_ubx_packet(disable_gll)
send_ubx_packet(disable_gsa)

# --- SEND THE ENABLE COMMAND FOR GGA ---
print("Enabling GGA sentence...")
send_ubx_packet(enable_gga)

# --- SAVE THE CONFIGURATION ---
print("Saving configuration to non-volatile memory...")
send_ubx_packet(save_config)

print("Configuration complete!")
print("Your Neo-6M should now only output GGA sentences.")
print("You can disconnect the RX wire if you only need to read data.")