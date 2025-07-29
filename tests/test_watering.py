#!/usr/bin/env python3
"""
Test script for the complete watering system
Checks sensor and pump operation
"""

import time
import RPi.GPIO as GPIO
from pico_adc import PicoADC

# Configuration
PUMP_PIN = 17
DRY_THRESHOLD = 750  # Adjust based on your calibration
PUMP_DURATION = 3    # Seconds to run pump for test

def setup_pump():
    """Initialize pump GPIO"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PUMP_PIN, GPIO.OUT)
    GPIO.output(PUMP_PIN, GPIO.LOW)
    print("✓ Pump initialized")

def test_pump():
    """Test pump operation"""
    print("\n🚿 Testing pump...")
    print("WARNING: Pump will run for 3 seconds!")
    input("Press Enter to test pump (Ctrl+C to skip)...")
    
    print("Pump ON")
    GPIO.output(PUMP_PIN, GPIO.HIGH)
    time.sleep(PUMP_DURATION)
    GPIO.output(PUMP_PIN, GPIO.LOW)
    print("Pump OFF")

def monitor_moisture(pico):
    """Monitor moisture and suggest watering"""
    print("\n🌱 Monitoring moisture levels...")
    print(f"Dry threshold: {DRY_THRESHOLD}")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            value = pico.read_value_blocking(timeout=2)
            if value is not None:
                # Calculate moisture percentage (850=dry, 500=wet)
                moisture_pct = ((850 - value) / 350) * 100
                moisture_pct = max(0, min(100, moisture_pct))
                
                status = "💧 WET" if value < 600 else "🏜️  DRY" if value > DRY_THRESHOLD else "✅ GOOD"
                
                print(f"Reading: {value:4d} | Moisture: {moisture_pct:3.0f}% | Status: {status}", end='\r')
                
                if value > DRY_THRESHOLD:
                    print(f"\n⚠️  Soil is dry ({value})! Press 'w' + Enter to water, or wait...")
                    # Simple input check with timeout
                    import select
                    i, o, e = select.select([sys.stdin], [], [], 0.1)
                    if i and sys.stdin.readline().strip().lower() == 'w':
                        print("💦 Watering for 3 seconds...")
                        GPIO.output(PUMP_PIN, GPIO.HIGH)
                        time.sleep(PUMP_DURATION)
                        GPIO.output(PUMP_PIN, GPIO.LOW)
                        print("✓ Watering complete!")
                        time.sleep(5)  # Wait before continuing monitoring
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nStopping monitor...")

def main():
    print("=== Sprout System Test ===\n")
    
    # Initialize components
    setup_pump()
    
    pico = PicoADC()
    if not pico.connect():
        print("❌ Failed to connect to Pico")
        GPIO.cleanup()
        return
    
    print("✓ Connected to moisture sensor")
    
    # Run tests
    try:
        # Test 1: Pump
        test_pump()
        
        # Test 2: Monitor with manual watering
        monitor_moisture(pico)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    finally:
        pico.close()
        GPIO.cleanup()
        print("✓ Cleanup complete")

if __name__ == "__main__":
    import sys
    main()
