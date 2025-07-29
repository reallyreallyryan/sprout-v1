#!/usr/bin/env python3
"""
Sprout v1.0 - Autonomous Plant Care System
Author: Ryan Kelems
Created: July 2025
Repository: https://github.com/reallyreallyryan/sprout-v1

Main controller for autonomous plant monitoring and watering system.
Features auto-reconnection, error recovery, and ML data logging.
"""

import json
import logging
import time
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

from pico_adc import PicoADC
from sprout_data_logger import SproutDataLogger

try:
    import RPi.GPIO as GPIO
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    print("Warning: Hardware libraries not available. Running in simulation mode.")


class SproutRobot:
    """
    Main controller class for the Sprout plant care system.
    
    Manages sensor readings, watering decisions, and data logging
    with robust error handling and automatic recovery.

    """
    def __init__(self, config_file='sprout_manifest.json'):
        """
        Initialize the Sprout robot with configuration.
        
        Args:
            config_file (str): Path to JSON configuration file
        """

        self.config = self._load_config(config_file)
        self.last_watering_time = 0
        self.pico = None
        self.setup_logging()
        
        # Initialize ML data logger
        self.data_logger = SproutDataLogger()
        self.logger.info("ML data logging initialized")
        
        self.logger.info(f"Sprout {self.config['robot_identity']['name']} v{self.config['robot_identity']['version']} starting up...")
        
        if HARDWARE_AVAILABLE:
            self.setup_hardware()
        else:
            self.logger.warning("Running in simulation mode - no hardware control")
    
    def _load_config(self, config_file):
        """Load and validate configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)
    
    def setup_logging(self):
        """Configure rotating file logging and console output"""
        log_config = self.config['logging']
        
        self.logger = logging.getLogger('sprout')
        self.logger.setLevel(logging.INFO)
        
        if log_config['enabled']:
            handler = RotatingFileHandler(
                log_config['file_path'],
                maxBytes=log_config['max_file_size_mb'] * 1024 * 1024,
                backupCount=log_config['rotation_count']
            )
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Console handler for immeditate feedback
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def setup_hardware(self):
        """Initialize GPIO pins and establish Pico connection"""
        try:
            # Setup GPIO for pump control
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.config['pump']['gpio_pin'], GPIO.OUT)
            GPIO.output(self.config['pump']['gpio_pin'], GPIO.LOW)
            
            # Setup LED indicator if configured
            if self.config.get('led', {}).get('enabled', False):
                self.led_pin = self.config['led']['gpio_pin']
                GPIO.setup(self.led_pin, GPIO.OUT)
                GPIO.output(self.led_pin, GPIO.LOW)
                self.logger.info(f"LED indicator initialized on GPIO {self.led_pin}")
                
                # Startup blink
                if self.config['led'].get('startup_blink', True):
                    blink_count = self.config['led'].get('startup_blink_count', 3)
                    for _ in range(blink_count):
                        GPIO.output(self.led_pin, GPIO.HIGH)
                        time.sleep(1.0)
                        GPIO.output(self.led_pin, GPIO.LOW)
                        time.sleep(1.0)
            
            # Setup Pico ADC connection
            self.connect_to_pico()
            
            self.logger.info("Hardware initialized successfully")
        except Exception as e:
            self.logger.error(f"Hardware initialization failed: {e}")
            sys.exit(1)
    
    def connect_to_pico(self):
        """
        Connect or reconnect to Pico ADC with retry logic.
        
        Returns:
            bool: True if connection successful, False otherwise
        """        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if self.pico:
                    self.pico.close()
                    time.sleep(1)
                
                self.pico = PicoADC()
                if self.pico.connect():
                    self.logger.info("Connected to Pico ADC successfully")
                    return True
                else:
                    retry_count += 1
                    self.logger.warning(f"Failed to connect to Pico ADC, retry {retry_count}/{max_retries}")
                    time.sleep(2)
            except Exception as e:
                retry_count += 1
                self.logger.error(f"Error connecting to Pico: {e}, retry {retry_count}/{max_retries}")
                time.sleep(2)
        
        self.logger.error("Failed to connect to Pico ADC after all retries")
        return False
    
    def read_moisture(self):
        """
        Read moisture sensor value with automatic reconnection.
        
        Returns:
            tuple: (raw_value, moisture_percent) or (None, None) on error
        """        
        if HARDWARE_AVAILABLE:
            # First attempt
            raw_value, moisture_percent = self._try_read_moisture()
            
            # If failed, try to reconnect once and read again
            if raw_value is None:
                self.logger.warning("First read attempt failed, trying to reconnect...")
                if self.connect_to_pico():
                    raw_value, moisture_percent = self._try_read_moisture()
            
            return raw_value, moisture_percent
        else:
            # Simulation mode
            import random
            raw = random.randint(600, 800)
            percent = random.randint(20, 80)
            return raw, percent
    
    def _try_read_moisture(self):
        """
        Single attempt to read moisture sensor.
        
        Returns:
            tuple: (raw_value, moisture_percent) or (None, None) on error
        """
        try:
            if not self.pico:
                return None, None
                
            # Get reading from Pico with timeout
            raw_value = self.pico.read_value_blocking(timeout=5)
            
            if raw_value is None:
                return None, None
            
            # Convert to percentage using calibration values
            air_value = self.config['moisture_sensor']['calibration']['air_value']
            water_value = self.config['moisture_sensor']['calibration']['water_value']
            
            # Calculate moisture percentage (capacitive sensor: higher = drier)
            moisture_percent = ((air_value - raw_value) / (air_value - water_value)) * 100
            moisture_percent = max(0, min(100, moisture_percent))
            
            return raw_value, moisture_percent
        except Exception as e:
            self.logger.error(f"Error reading moisture sensor: {e}")
            return None, None
    
    def activate_pump(self, duration):
        """
        Activate water pump for specified duration with safety limits.
        
        Args:
            duration (int): Pump activation time in seconds
        """
        if HARDWARE_AVAILABLE:
            try:
                # Turn on LED if configured
                if hasattr(self, 'led_pin'):
                    GPIO.output(self.led_pin, GPIO.HIGH)
                
                # Safety limit on pump duration
                max_pump_time = self.config['pump'].get('max_pump_time_seconds', 30)
                duration = min(duration, max_pump_time)
                
                self.logger.info(f"Activating pump for {duration} seconds")
                GPIO.output(self.config['pump']['gpio_pin'], GPIO.HIGH)
                time.sleep(duration)
                GPIO.output(self.config['pump']['gpio_pin'], GPIO.LOW)
                self.logger.info("Pump deactivated")
            except Exception as e:
                self.logger.error(f"Error controlling pump: {e}")
                # Always try to turn pump off in case of error
                try:
                    GPIO.output(self.config['pump']['gpio_pin'], GPIO.LOW)
                except:
                    pass
            finally:
                # Always turn off LED even if error occurs
                if hasattr(self, 'led_pin'):
                    GPIO.output(self.led_pin, GPIO.LOW)
        else:
            self.logger.info(f"[SIMULATION] Would activate pump for {duration} seconds")
            time.sleep(duration)
    
    def check_cooldown(self):
        """
        Check if cooldown period has elapsed since last watering.
        
        Returns:
            bool: True if ready to water, False if in cooldown
        """
        current_time = time.time()
        cooldown_period = self.config['pump']['cooldown_period_seconds']
        
        if current_time - self.last_watering_time >= cooldown_period:
            return True
        else:
            remaining = cooldown_period - (current_time - self.last_watering_time)
            self.logger.info(f"Cooldown active: {remaining:.0f} seconds remaining")
            return False
    
    def should_water(self, raw_moisture):
        """
        Determine if plant needs watering based on sensor reading.
        
        Args:
            raw_moisture (int): Raw sensor value
            
        Returns:
            bool: True if watering needed, False otherwise
        """
        if raw_moisture is None:
            return False
        
        dry_threshold = self.config['moisture_sensor']['dry_threshold']
        return raw_moisture > dry_threshold  # Higher values = drier for capacitive sensors
    
    def log_status(self, action, moisture_raw, moisture_percent):
        """Log status in human-friendly format"""
        if moisture_raw is not None:
            if action == "watered":
                message = f"I checked the soil (moisture: {moisture_percent:.1f}%) and it was dry, so I watered the plant."
            elif action == "checked":
                message = f"I checked the soil (moisture: {moisture_percent:.1f}%) and it's doing fine."
            elif action == "cooldown":
                message = f"I checked the soil (moisture: {moisture_percent:.1f}%) and it needs water, but I'm waiting before watering again."
            else:
                message = action
        else:
            message = "I couldn't read the moisture sensor."
        
        self.logger.info(message)
    
    def run(self):
        """
        Main control loop for autonomous plant care.
        
        Continuously monitors moisture and makes watering decisions
        with comprehensive error recovery.
        """
        self.logger.info("Starting main control loop")
        
        # Initial startup delay
        time.sleep(self.config['system']['startup_delay_seconds'])
        
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        try:
            while True:
                # Read moisture sensor
                raw_moisture, moisture_percent = self.read_moisture()
                
                if raw_moisture is not None:
                    # Reset failure counter on successful read
                    consecutive_failures = 0
                    
                    # Check if plant needs water
                    if self.should_water(raw_moisture):
                        # Check cooldown period
                        if self.check_cooldown():
                            # Water the plant
                            self.activate_pump(self.config['pump']['activation_duration_seconds'])
                            self.last_watering_time = time.time()
                            self.log_status("watered", raw_moisture, moisture_percent)
                            
                            # Log to CSV for ML
                            self.data_logger.log_reading(
                                raw_value=raw_moisture,
                                moisture_percent=moisture_percent,
                                action="watered",
                                watered=True,
                                water_duration=self.config['pump']['activation_duration_seconds'],
                                last_watering_time=self.last_watering_time
                            )
                        else:
                            self.log_status("cooldown", raw_moisture, moisture_percent)
                            
                            # Log to CSV for ML
                            self.data_logger.log_reading(
                                raw_value=raw_moisture,
                                moisture_percent=moisture_percent,
                                action="cooldown",
                                watered=False,
                                last_watering_time=self.last_watering_time
                            )
                    else:
                        self.log_status("checked", raw_moisture, moisture_percent)
                        
                        # Log to CSV for ML
                        self.data_logger.log_reading(
                            raw_value=raw_moisture,
                            moisture_percent=moisture_percent,
                            action="checked",
                            watered=False,
                            last_watering_time=self.last_watering_time
                        )
                else:
                    consecutive_failures += 1
                    self.logger.error(f"Failed to read moisture sensor ({consecutive_failures}/{max_consecutive_failures})")
                    
                    # Log error to CSV
                    self.data_logger.log_reading(
                        raw_value=None,
                        moisture_percent=None,
                        action="error",
                        watered=False,
                        notes=f"Read failure {consecutive_failures}"
                    )
                    
                    # If too many failures, try a full reconnection
                    if consecutive_failures >= max_consecutive_failures:
                        self.logger.error("Too many consecutive failures, attempting full reconnection...")
                        time.sleep(10)  # Wait a bit before reconnecting
                        if not self.connect_to_pico():
                            self.logger.error("Reconnection failed, will keep trying...")
                        consecutive_failures = 0  # Reset counter
                
                # Sleep until next check
                time.sleep(self.config['moisture_sensor']['read_interval_seconds'])
                
        except KeyboardInterrupt:
            self.shutdown()
    
    def shutdown(self):
        """Perform clean shutdown of all components"""
        self.logger.info("Shutting down Sprout...")
        self.log_status("I turned off", None, None)
        
        # Log shutdown to CSV
        self.data_logger.log_reading(
            raw_value=None,
            moisture_percent=None,
            action="shutdown",
            watered=False,
            notes="System shutdown"
        )
        
        # Close Pico connection
        if self.pico:
            try:
                self.pico.close()
            except:
                pass
        
        # Clean up GPIO
        if HARDWARE_AVAILABLE:
            try:
                # Ensure pump is off before shutting down
                GPIO.output(self.config['pump']['gpio_pin'], GPIO.LOW)
                
                # Turn off LED if it exists
                if hasattr(self, 'led_pin'):
                    GPIO.output(self.led_pin, GPIO.LOW)
                
                GPIO.cleanup()
            except:
                pass
        
        sys.exit(0)


if __name__ == "__main__":
    robot = SproutRobot()
    robot.run()
