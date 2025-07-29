#!/usr/bin/env python3
"""
Pico ADC Serial Communication Module
Part of Sprout v1.0 - Autonomous Plant Care System

Handles UART communication between Raspberry Pi and Pico ADC.
Implements robust error handling and automatic reconnection.
"""

import serial
import json
import time
import logging

class PicoADC:
    """
    Serial communication handler for Raspberry Pi Pico ADC.
    
    Manages UART connection and JSON data parsing with
    comprehensive error handling.
    """

    def __init__(self, port='/dev/ttyAMA0', baudrate=9600):
        """
        Initialize Pico ADC communication interface.
        
        Args:
            port (str): Serial port device path
            baudrate (int): Communication speed
        """
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.logger = logging.getLogger('PicoADC')
        
    def connect(self):
        """
        Establish serial connection to Pico.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=2,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            # Clear any old data
            self.serial.reset_input_buffer()
            self.logger.info(f"Connected to Pico on {self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Pico: {e}")
            return False
    
    def read_value(self):
        """
        Read a single moisture value (non-blocking).
        
        Args:
            timeout (float): Maximum time to wait for data
            
        Returns:
            int: Raw ADC value (0-1023) or None on error
        """
        if not self.serial or not self.serial.is_open:
            self.logger.error("Serial port not open")
            return None
            
        try:
            # Read line from serial
            if self.serial.in_waiting > 0:
                line = self.serial.readline().decode('utf-8').strip()
                
                # Parse JSON
                data = json.loads(line)
                
                # Return the 10-bit value (0-1023 range)
                if data.get('status') == 'ok':
                    return data.get('raw_10bit')
                else:
                    self.logger.warning(f"Pico reported error: {data}")
                    return None
                    
        except json.JSONDecodeError as e:
            self.logger.warning(f"Invalid JSON from Pico: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading from Pico: {e}")
            return None
            
        return None
    
    def read_value_blocking(self, timeout=5):
        """
        Read moisture value with multiple attempts (blocking).
        
        Args:
            timeout (float): Total timeout for all attempts
            
        Returns:
            int: Raw ADC value (0-1023) or None on error
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            value = self.read_value()
            if value is not None:
                return value
            time.sleep(0.1)
        
        return None
    
    def close(self):
        """Close serial connection and clean up resources"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.logger.info("Serial connection closed")

# Test function
if __name__ == "__main__":
    print("Testing Pico ADC connection...")
    
    pico = PicoADC()
    if pico.connect():
        print("Connected! Reading 5 values...")
        
        for i in range(5):
            value = pico.read_value_blocking()
            if value is not None:
                print(f"Reading {i+1}: {value}")
            else:
                print(f"Reading {i+1}: No data")
            time.sleep(1)
        
        pico.close()
    else:
        print("Failed to connect to Pico")
