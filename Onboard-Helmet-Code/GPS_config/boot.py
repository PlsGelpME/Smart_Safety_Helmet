# boot.py - Standard configuration file

# Import necessary libraries
import machine
import os
from machine import Pin
import gc  # Garbage collector interface

# 2. Disable ESP32 debug output to avoid spamming the serial port
# This is optional but cleans up your serial output for your application.
#uart = machine.UART(0, 115200) # This line is often not needed, as it's the default
#os.dupterm(None, 1) # This can disable the REPL on UART0, use with caution.

# 3. Run Garbage Collection to free up memory before main.py starts
gc.collect()
gc.enable() # Enable automatic garbage collection

# 4. Mount the filesystem (if you have an SD card or use internal storage)
# For example, using LittleFS on the ESP32:
# try:
#     os.mount(machine.SDCard(), '/sd')
#     print("SD card mounted.")
# except OSError as e:
#     print("No SD card found or error mounting:", e)

# 5. Set a custom CPU frequency for power savings or performance (optional)
# machine.freq(240000000)  # Set to 240 MHz (default)
# machine.freq(160000000)  # Set to 160 MHz to save a bit of power
# machine.freq(80000000)   # Set to 80 MHz for significant power savings

# 6. Configure other hardware that MUST be set up at boot
# For example, ensure a safety pin is in a known state.
# safety_relay = Pin(23, Pin.OUT, value=0)  # Start with relay OFF

# Boot completed successfully
#led.value(0)  # Turn LED OFF to indicate boot is done
print("Boot configuration complete.")
print("Free memory:", gc.mem_free())

# The main.py file will now execute automatically.