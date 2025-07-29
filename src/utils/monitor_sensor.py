#!/usr/bin/env python3
"""
Continuous monitoring of moisture sensor
Helps debug sensor behavior
"""

from pico_adc import PicoADC
import time

print("Moisture Sensor Monitor - Press Ctrl+C to stop")
print("=" * 50)

pico = PicoADC()
if not pico.connect():
    print("Failed to connect to Pico")
    exit(1)

print("Connected! Monitoring sensor values...\n")

try:
    while True:
        value = pico.read_value_blocking(timeout=2)
        if value is not None:
            # Create a visual bar graph
            # Scale: 0-1023, show as 50 character bar
            bar_length = int((value / 1023) * 50)
            bar = '█' * bar_length + '░' * (50 - bar_length)
            
            print(f"Value: {value:4d} |{bar}|", end='\r')
        
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("\n\nStopping monitor...")
    pico.close()
