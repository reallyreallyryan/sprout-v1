# Sprout v1.0 - Autonomous Plant Care System

An intelligent plant watering system that learns from sensor data to optimize plant care. Built with Raspberry Pi, featuring real-time monitoring, autonomous watering, and predictive ML models.

## 🌟 Key Features

- **Autonomous Operation**: Monitors soil moisture and waters plants automatically
- **Machine Learning**: Predicts moisture levels with 99.2% accuracy (R²=0.992)
- **Robust Hardware**: Auto-reconnection, error recovery, LED status indicators
- **Data Collection**: Comprehensive logging for ML training and analysis
- **Local-First**: No cloud dependencies, fully autonomous operation

## 🏆 Project Achievements

- Successfully trained ML model with only 125 data points
- Achieved 0.16% mean absolute error in moisture prediction
- 100% uptime after implementing reconnection logic
- First autonomous watering within 10 seconds of deployment
- Built complete system from zero hardware experience in 8 days

## 🛠️ Technical Stack

### Hardware
- Raspberry Pi 4 (Controller)
- Raspberry Pi Pico (ADC)
- Capacitive Moisture Sensor v1.2
- Peristaltic Pump with 5V Relay
- Status LED Indicator
- Basil Plant

### Software
- Python 3.9+
- scikit-learn for ML
- pandas, numpy for data processing
- matplotlib, seaborn for visualization
- Custom serial protocol for Pi-Pico communication

## 📊 Results

- **Data Collected**: 700+ readings over 8 days
- **ML Accuracy**: 99.2% variance explained (R²=0.992)
- **Prediction Error**: 0.16% MAE
- **Watering Efficiency**: Maintains optimal 40-50% moisture
- **Response Time**: <10 seconds from detection to action

## 🚀 Quick Start

See [docs/SETUP.md](docs/SETUP.md) for detailed installation instructions.

```bash
# Install dependencies
pip install -r requirements.txt

# Calibrate sensor
python3 src/utils/calibrate_capacitive.py

# Run system
python3 src/core/sprout_robust.py
```

## 📈 Machine Learning Pipeline

Data Collection: Automated logging of sensor readings
Feature Engineering: 50+ features from 16 raw measurements
Model Training: Random Forest achieving 99.2% accuracy
Visualization: Comprehensive analysis of patterns

See ML performance visualizations in the outputs/ directory.
📁 Project Structure
sprout_portfolio_v1/
├── src/              # Source code
│   ├── core/         # Main system components
│   ├── ml/           # Machine learning pipeline
│   └── utils/        # Utility scripts
├── config/           # Configuration files
├── firmware/         # Pico microcontroller code
├── data/             # Sample data and ML models
├── tests/            # Test scripts
├── outputs/          # Visualizations and reports
└── docs/             # Documentation

## 👨‍💻 Developer
Ryan Kelems
Full-stack engineer passionate about IoT, machine learning, and building things that work.
This project showcases rapid learning, problem-solving, and the ability to build complete systems from scratch.

## 📜 License
MIT License - See LICENSE file for details

## Live Demo
- **Website**: [meetsproutbot.com](https://meetsproutbot.com)
- **Source Code**: Available in this repository
- **Documentation**: See [docs/SETUP.md](docs/SETUP.md)

