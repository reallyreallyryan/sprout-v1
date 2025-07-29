#!/usr/bin/env python3
"""
Calibration utility for capacitive moisture sensors with Pico ADC
Designed specifically for sensors that don't respond well to pure water
"""

import time
import json
import sys
from pico_adc import PicoADC


def read_sensor_average(pico, samples=10):
    """Read sensor value, averaging multiple samples"""
    readings = []
    print("Reading", end="", flush=True)
    
    for _ in range(samples):
        value = pico.read_value_blocking(timeout=2)
        if value is not None:
            readings.append(value)
            print(".", end="", flush=True)
        time.sleep(0.5)
    
    print(" Done!")
    
    if not readings:
        return None, None, None
    
    avg_reading = sum(readings) / len(readings)
    return avg_reading, min(readings), max(readings)


def get_plant_watering_info():
    """Get information about the plant's watering needs"""
    print("\n=== Plant Information ===")
    print("What type of plant are you monitoring?")
    print("1. Herbs (Basil, Mint, Cilantro) - likes consistently moist soil")
    print("2. Succulents (Cactus, Aloe) - likes dry periods between watering")
    print("3. Tropical (Ferns, Peace Lily) - likes very moist soil")
    print("4. Standard Houseplant - moderate moisture")
    print("5. Custom")
    
    choice = input("\nSelect (1-5): ").strip()
    
    # Returns (name, dry_percentage, wet_percentage)
    plant_profiles = {
        '1': ("Herbs", 0.25, 0.45),  # Water at 25% moisture, stop at 45%
        '2': ("Succulents", 0.10, 0.25),  # Very dry tolerant
        '3': ("Tropical", 0.40, 0.60),  # Keep quite moist
        '4': ("Houseplant", 0.20, 0.40),  # Standard range
        '5': ("Custom", None, None)
    }
    
    if choice in plant_profiles:
        return plant_profiles[choice]
    else:
        return plant_profiles['4']  # Default to houseplant


def main():
    print("=== Capacitive Moisture Sensor Calibration ===")
    print("This calibration is designed for capacitive sensors that measure soil moisture.\n")
    
    # Connect to Pico
    pico = PicoADC()
    if not pico.connect():
        print("Failed to connect to Pico ADC. Check connections.")
        sys.exit(1)
    
    print("Connected to Pico ADC successfully!\n")
    time.sleep(2)
    
    # Get plant type
    plant_name, dry_pct, wet_pct = get_plant_watering_info()
    
    print(f"\n=== Calibrating for {plant_name} ===\n")
    
    # Step 1: Dry reference (air)
    print("Step 1: Dry Reference (Air)")
    print("Hold the sensor in the air - this is our 0% moisture reference.")
    input("Press Enter when ready...")
    
    air_avg, air_min, air_max = read_sensor_average(pico)
    if air_avg is None:
        print("Failed to read sensor. Check connections.")
        sys.exit(1)
    
    print(f"Air reading: {air_avg:.0f} (range: {air_min}-{air_max})\n")
    
    # Step 2: Very wet soil reference
    print("Step 2: Wet Soil Reference")
    print("Place the sensor in VERY WET soil (just watered, almost muddy).")
    print("This is our 100% moisture reference.")
    input("Press Enter when ready...")
    
    wet_avg, wet_min, wet_max = read_sensor_average(pico)
    if wet_avg is None:
        print("Failed to read sensor. Check connections.")
        sys.exit(1)
    
    print(f"Wet soil reading: {wet_avg:.0f} (range: {wet_min}-{wet_max})\n")
    
    # Validate readings
    if wet_avg >= air_avg:
        print("⚠️  WARNING: Wet soil reading should be lower than air reading!")
        print("Check sensor placement and try again.")
        sys.exit(1)
    
    # Step 3: Current soil test
    print("Step 3: Current Soil Test")
    print("Place the sensor in your plant's soil at normal watering depth.")
    input("Press Enter when ready...")
    
    soil_avg, soil_min, soil_max = read_sensor_average(pico)
    if soil_avg is None:
        print("Failed to read sensor. Check connections.")
        sys.exit(1)
    
    # Calculate moisture percentage
    moisture_range = air_avg - wet_avg
    current_moisture = air_avg - soil_avg
    moisture_percent = (current_moisture / moisture_range) * 100
    moisture_percent = max(0, min(100, moisture_percent))  # Clamp to 0-100%
    
    print(f"Current soil reading: {soil_avg:.0f} (range: {soil_min}-{soil_max})")
    print(f"Current moisture level: {moisture_percent:.1f}%\n")
    
    # Calculate thresholds
    if dry_pct and wet_pct:
        dry_threshold = air_avg - (moisture_range * dry_pct)
        wet_threshold = air_avg - (moisture_range * wet_pct)
    else:
        # Custom mode - ask for percentages
        print("At what moisture percentage should watering start?")
        dry_pct = float(input("Dry threshold (e.g., 25 for 25%): ")) / 100
        print("At what moisture percentage should watering stop?")
        wet_pct = float(input("Wet threshold (e.g., 45 for 45%): ")) / 100
        
        dry_threshold = air_avg - (moisture_range * dry_pct)
        wet_threshold = air_avg - (moisture_range * wet_pct)
    
    # Display results
    print("\n=== Calibration Results ===")
    print(f"Sensor range: {wet_avg:.0f} (wet) to {air_avg:.0f} (dry)")
    print(f"Total range: {moisture_range:.0f} units")
    print(f"Current soil: {soil_avg:.0f} ({moisture_percent:.1f}% moisture)")
    
    print(f"\nRecommended thresholds for {plant_name}:")
    print(f"Start watering when reading > {dry_threshold:.0f} ({dry_pct*100:.0f}% moisture)")
    print(f"Stop watering when reading < {wet_threshold:.0f} ({wet_pct*100:.0f}% moisture)")
    
    # Moisture scale
    print("\nYour moisture scale:")
    print(f"{air_avg:.0f} = Bone dry (0%)")
    print(f"{dry_threshold:.0f} = Time to water ({dry_pct*100:.0f}%)")
    print(f"{wet_threshold:.0f} = Well watered ({wet_pct*100:.0f}%)")
    print(f"{wet_avg:.0f} = Saturated (100%)")
    
    # Update config
    print("\nWould you like to update sprout_manifest.json with these values? (y/n)")
    if input().lower() == 'y':
        try:
            with open('sprout_manifest.json', 'r') as f:
                config = json.load(f)
            
            config['moisture_sensor']['calibration']['air_value'] = int(air_avg)
            config['moisture_sensor']['calibration']['water_value'] = int(wet_avg)
            config['moisture_sensor']['dry_threshold'] = int(dry_threshold)
            config['moisture_sensor']['wet_threshold'] = int(wet_threshold)
            
            with open('sprout_manifest.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            print("Configuration updated successfully!")
            print(f"Sprout will water when moisture drops below {dry_pct*100:.0f}%")
            print(f"and stop when it reaches {wet_pct*100:.0f}%")
        except Exception as e:
            print(f"Error updating configuration: {e}")
    
    print("\nCalibration complete!")
    pico.close()


if __name__ == "__main__":
    main()
