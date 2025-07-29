#!/usr/bin/env python3
"""
LED Test Script for Sprout Robot
Tests the LED indicator on GPIO 27
"""

import RPi.GPIO as GPIO
import time
import sys

def test_led():
    """Test the LED with visual feedback"""
    LED_PIN = 23
    
    try:
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(LED_PIN, GPIO.OUT)
        GPIO.output(LED_PIN, GPIO.LOW)
        
        print("LED Test - GPIO 23")
        print("Press Ctrl+C to stop\n")
        
        # Continuous blink test
        while True:
            GPIO.output(LED_PIN, GPIO.HIGH)
            print("💡 LED ON ", end='\r')
            time.sleep(1)
            
            GPIO.output(LED_PIN, GPIO.LOW)
            print("⚫ LED OFF", end='\r')
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nTest stopped")
        
    except Exception as e:
        print(f"\nError: {e}")
        
    finally:
        # Always cleanup GPIO
        GPIO.output(LED_PIN, GPIO.LOW)
        GPIO.cleanup()
        print("Cleanup complete")

if __name__ == "__main__":
    test_led()
