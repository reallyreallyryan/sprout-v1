# Sprout Setup Guide

Complete installation instructions for the Sprout autonomous plant care system.

## Prerequisites

### Hardware Requirements
- Raspberry Pi 4 (2GB+ RAM)
- Raspberry Pi Pico
- Capacitive Soil Moisture Sensor v1.2
- 5V Peristaltic Pump
- 5V Single-Channel Relay Module
- LED + 330Ω Resistor (optional)
- Jumper wires and breadboard

### Software Requirements
- Raspberry Pi OS (64-bit recommended)
- Python 3.9 or higher
- Git

## Hardware Assembly

### Wiring Connections

#### Pi 4 to Pico (Serial Communication)
```
Raspberry Pi 4          Raspberry Pi Pico
Pin 4 (5V)      -----> Pin 39 (VSYS)
Pin 6 (GND)     -----> Pin 38 (GND)
Pin 8 (TX)      -----> Pin 2 (RX)
Pin 10 (RX)     -----> Pin 1 (TX)
```

#### Moisture Sensor to Pico
```
Pico                    Moisture Sensor
Pin 31 (ADC0)   -----> Signal (Yellow)
Pin 36 (3.3V)   -----> VCC (Red)
Pin 38 (GND)    -----> GND (Black)
```

#### Pump Control
```
Raspberry Pi 4          Relay Module
Pin 11 (GPIO17) -----> IN
Pin 2 (5V)      -----> VCC
Pin 9 (GND)     -----> GND

Relay                   Water Pump
NO              -----> Positive Wire
COM             -----> 5V Power Supply (+)
                       Negative Wire -> Power Supply (-)
```

#### Status LED (Optional)
```
Raspberry Pi 4
Pin 16 (GPIO23) -----> LED Anode (through 330Ω resistor)
Pin 14 (GND)    -----> LED Cathode
```

## Software Installation

### 1. Enable Serial Communication

```bash
# Disable serial console
sudo systemctl stop serial-getty@ttyAMA0.service
sudo systemctl disable serial-getty@ttyAMA0.service
sudo systemctl mask serial-getty@ttyAMA0.service

# Add user to dialout group
sudo usermod -a -G dialout $USER

# Edit boot config
sudo nano /boot/config.txt
# Add these lines:
enable_uart=1
dtoverlay=disable-bt

# Reboot
sudo reboot
```

### 2. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python packages
pip3 install -r requirements.txt
```

### 3. Program the Pico

1. Download MicroPython firmware from https://micropython.org/download/rp2-pico/
2. Hold BOOTSEL button while connecting Pico to computer
3. Copy the .uf2 file to the RPI-RP2 drive
4. Upload `firmware/pico/main.py` to the Pico using Thonny or similar

### 4. Configure Sprout

```bash
# Edit configuration
nano config/sprout_manifest.json
```

Key settings to adjust:
- `dry_threshold`: When to water (higher = drier for capacitive sensors)
- `wet_threshold`: Target moisture level
- `activation_duration_seconds`: How long to run pump
- `cooldown_period_seconds`: Minimum time between waterings

### 5. Calibrate Sensor

```bash
python3 src/utils/calibrate_capacitive.py
```

Follow the prompts:
1. Place sensor in dry air
2. Place sensor in dry soil
3. Place sensor in wet soil
4. Save calibration values

### 6. Test Components

```bash
# Test LED (if installed)
python3 tests/test_led.py

# Test pump - have water ready!
python3 tests/test_watering.py

# Monitor sensor readings
python3 src/utils/monitor_sensor.py
```

## Running Sprout

### Manual Start
```bash
cd sprout_portfolio_v1
python3 src/core/sprout_robust.py
```

### Using Screen (Recommended)
```bash
screen -S sprout
python3 src/core/sprout_robust.py
# Detach: Ctrl+A, D
# Reattach: screen -r sprout
```

### Systemd Service (Production)

Create service file:
```bash
sudo nano /etc/systemd/system/sprout.service
```

Add:

[Unit]
Description=Sprout Plant Watering System
After=multi-user.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/sprout_portfolio_v1
ExecStart=/usr/bin/python3 /home/pi/sprout_portfolio_v1/src/core/sprout_robust.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target


## Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable sprout
sudo systemctl start sprout
sudo systemctl status sprout
```

## Machine Learning Pipeline

After collecting data for several days:

```bash
# Visualize data patterns
python3 src/ml/sprout_ml_visualizer.py

# Engineer features
python3 src/ml/sprout_ml_features.py

# Train predictive model
python3 src/ml/sprout_ml_predictor.py
```

## Troubleshooting

### Serial Connection Issues
```bash
# Check permissions
ls -la /dev/ttyAMA0

# Test serial port
cat /dev/ttyAMA0

# Check for conflicts
sudo lsof /dev/ttyAMA0
```

### No Sensor Readings
1. Verify Pico is powered (LED should be on)
2. Check TX/RX connections (must be crossed)
3. Ensure sensor is connected to correct ADC pin
4. Test with `monitor_sensor.py`

### Pump Not Working
1. Check relay LED when activated
2. Listen for relay clicking sound
3. Verify pump power supply
4. Test pump directly with 5V

### Data Collection Issues
1. Check CSV file permissions
2. Ensure data directory exists
3. Review logs for write errors

## Maintenance

- **Daily**: Check water reservoir level
- **Weekly**: Review logs and data quality
- **Monthly**: Clean sensor, check connections
- **As needed**: Retrain ML model with new data