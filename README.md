# Smart_Safety_Helmet

# MPU6050 Gyroscope Interface

## Overview
I2C-based driver for MPU6050 gyroscope/accelerometer with free-fall detection capabilities.

## Features
- **Free-fall Detection**: Configurable threshold and duration settings
- **Hardware Interrupts**: Pin-based interrupt triggering
- **I2C Communication**: 400kHz communication with register-level access
- **Connection Verification**: WHO_AM_I register validation

## Quick Start
```python
gyro = GyroSetup(scl_pin=22, sda_pin=21, int_pin=4)
gyro.configure_freefall(threshold=0x10, duration=0x05)
```

## Key Methods
- `configure_freefall()`: Setup free-fall detection parameters
- `verify_connection()`: Validate sensor communication
- `get_interrupt_status()`: Read interrupt register state
- `is_initialized()`: Check configuration status

## Default Settings
- **I2C Address**: 0x68
- **Free-fall Threshold**: 0x10 (~0.16g)
- **Free-fall Duration**: 0x05 (~5ms)
- **Interrupt**: Active low, latched until cleared

## Use Case
Emergency detection systems requiring reliable free-fall or motion detection with hardware interrupts.
