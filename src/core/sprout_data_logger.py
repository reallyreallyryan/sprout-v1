#!/usr/bin/env python3
"""
Sprout Data Logger - ML Data Collection Module
Part of Sprout v1.0 - Autonomous Plant Care System

Logs sensor readings and system events to CSV format for
machine learning model training and analysis.
"""

import csv
import json
import os
from datetime import datetime

class SproutDataLogger:
    """
    CSV data logger for machine learning pipeline.
    
    Collects timestamped sensor readings, actions, and system events
    in a format optimized for feature engineering and model training.
    """

    def __init__(self, csv_file='sprout_data.csv'):
        """
        Initialize data logger with CSV file.
        
        Args:
            csv_file (str): Path to CSV file for data storage
        """
        self.csv_file = csv_file
        self.ensure_csv_exists()
    
    def ensure_csv_exists(self):
        """Create CSV with headers if it doesn't exist"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'date',
                    'time',
                    'day_of_week',
                    'hour_of_day',
                    'raw_sensor_value',
                    'moisture_percent',
                    'action_taken',
                    'watered',
                    'water_duration_sec',
                    'hours_since_last_water',
                    'temperature_c',  # For future sensor
                    'humidity_percent',  # For future sensor
                    'light_level',  # For future sensor
                    'soil_temp_c',  # For future sensor
                    'notes'
                ])
    
    def log_reading(self, raw_value, moisture_percent, action, watered=False, 
                   water_duration=0, last_watering_time=None, notes=''):
        """
        Log a sensor reading with associated metadata.
        
        Args:
            raw_value (int): Raw ADC sensor reading
            moisture_percent (float): Calculated moisture percentage
            action (str): Action taken (checked, watered, cooldown, error)
            watered (bool): Whether plant was watered
            water_duration (int): Duration of watering in seconds
            last_watering_time (float): Timestamp of last watering
            notes (str): Additional notes or error messages
        """
        now = datetime.now()
        
        # Calculate hours since last watering
        hours_since_water = None
        if last_watering_time:
            hours_since_water = (now.timestamp() - last_watering_time) / 3600
        
        row = [
            now.isoformat(),  # Full timestamp
            now.strftime('%Y-%m-%d'),  # Date
            now.strftime('%H:%M:%S'),  # Time
            now.strftime('%A'),  # Day of week
            now.hour,  # Hour (0-23)
            raw_value,
            round(moisture_percent, 2),
            action,  # 'checked', 'watered', 'cooldown', 'error'
            1 if watered else 0,  # Binary for ML
            water_duration,
            round(hours_since_water, 2) if hours_since_water else '',
            '',  # Temperature placeholder
            '',  # Humidity placeholder
            '',  # Light level placeholder
            '',  # Soil temp placeholder
            notes
        ]
        
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
    
    def get_ml_ready_data(self):
        """Read CSV and return data ready for ML training"""
        import pandas as pd
        
        try:
            df = pd.read_csv(self.csv_file)
            
            # Add derived features useful for ML
            df['moisture_change'] = df['moisture_percent'].diff()
            df['time_of_day_sin'] = np.sin(2 * np.pi * df['hour_of_day'] / 24)
            df['time_of_day_cos'] = np.cos(2 * np.pi * df['hour_of_day'] / 24)
            
            return df
        except:
            return None


# Modified read_moisture method for sprout.py to include data logging
def read_moisture_with_logging(self):
    """Enhanced moisture reading that logs to CSV"""
    if HARDWARE_AVAILABLE and self.pico:
        try:
            # Get reading from Pico
            raw_value = self.pico.read_value_blocking(timeout=5)
            
            if raw_value is None:
                # Log the error
                self.data_logger.log_reading(None, None, 'error', notes='Failed to read sensor')
                self.logger.error("Failed to read from Pico ADC")
                return None, None
            
            # Convert to percentage (0-100%)
            air_value = self.config['moisture_sensor']['calibration']['air_value']
            water_value = self.config['moisture_sensor']['calibration']['water_value']
            
            moisture_percent = ((air_value - raw_value) / (air_value - water_value)) * 100
            moisture_percent = max(0, min(100, moisture_percent))
            
            # Determine action
            if self.should_water(raw_value):
                if self.check_cooldown():
                    action = 'watered'
                    watered = True
                    duration = self.config['pump']['activation_duration_seconds']
                else:
                    action = 'cooldown'
                    watered = False
                    duration = 0
            else:
                action = 'checked'
                watered = False
                duration = 0
            
            # Log to CSV
            self.data_logger.log_reading(
                raw_value=raw_value,
                moisture_percent=moisture_percent,
                action=action,
                watered=watered,
                water_duration=duration,
                last_watering_time=self.last_watering_time
            )
            
            return raw_value, moisture_percent
        except Exception as e:
            self.data_logger.log_reading(None, None, 'error', notes=str(e))
            self.logger.error(f"Error reading moisture sensor: {e}")
            return None, None


# Example analysis script
if __name__ == "__main__":
    print("Sprout Data Analysis")
    print("===================")
    
    logger = SproutDataLogger()
    
    # Example: Add a manual reading
    logger.log_reading(750, 27.5, 'checked', watered=False)
    
    # Try to load and analyze data
    try:
        import pandas as pd
        df = pd.read_csv('sprout_data.csv')
        
        print(f"\nTotal readings: {len(df)}")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"Average moisture: {df['moisture_percent'].mean():.1f}%")
        print(f"Times watered: {df['watered'].sum()}")
        
        # Show moisture trends
        print("\nMoisture by hour of day:")
        hourly = df.groupby('hour_of_day')['moisture_percent'].mean()
        for hour, moisture in hourly.items():
            print(f"  {hour:02d}:00 - {moisture:.1f}%")
            
    except Exception as e:
        print(f"No data yet or error: {e}")
