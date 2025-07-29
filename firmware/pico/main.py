#!/usr/bin/env python3
"""
Raspberry Pi Pico ADC Reader for Sprout
Reads capacitive moisture sensor and sends data via UART
Part of Sprout v1.0 - Autonomous Plant Care System
"""

import machine
import time
import json

# Initialize ADC on GPIO26 (ADC0)
adc = machine.ADC(26)

# Initialize UART
uart = machine.UART(0, baudrate=9600, tx=machine.Pin(0), rx=machine.Pin(1))

def read_moisture():
    """Read ADC value and convert to moisture data."""
    # Read ADC value (0-65535 for 16-bit)
    raw_16bit = adc.read_u16()
    # Convert to 10-bit for compatibility
    raw_10bit = raw_16bit >> 6
    
    return {
        "raw_10bit": raw_10bit,
        "raw_16bit": raw_16bit,
        "status": "ok",
        "timestamp": time.ticks_ms()
    }

# Main loop
while True:
    try:
        data = read_moisture()
        json_data = json.dumps(data) + '\n'
        uart.write(json_data.encode())
        time.sleep(0.1)  # 10Hz update rate
    except Exception as e:
        error_data = {"status": "error", "message": str(e)}
        uart.write((json.dumps(error_data) + '\n').encode())
        time.sleep(1)
