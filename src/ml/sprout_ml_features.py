#!/usr/bin/env python3
"""
SproutML Feature Engineering
Creates ML-ready features from raw sensor data
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json

class SproutFeatureEngineer:
    def __init__(self, csv_path='sprout_data.csv'):
        """Initialize with raw data"""
        self.df_raw = pd.read_csv(csv_path)
        self.df = self.df_raw.copy()
        self.prepare_base_data()
        
    def prepare_base_data(self):
        """Prepare base data with proper types"""
        # Convert timestamp
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.df = self.df.sort_values('timestamp').reset_index(drop=True)
        
        # Fill missing values
        self.df['moisture_percent'] = self.df['moisture_percent'].fillna(method='ffill')
        self.df['raw_sensor_value'] = self.df['raw_sensor_value'].fillna(method='ffill')
        
        print(f"📊 Loaded {len(self.df)} readings for feature engineering")
    
    def create_temporal_features(self):
        """Create time-based features"""
        print("\n⏰ Creating temporal features...")
        
        # Basic time features
        self.df['hour_sin'] = np.sin(2 * np.pi * self.df['hour_of_day'] / 24)
        self.df['hour_cos'] = np.cos(2 * np.pi * self.df['hour_of_day'] / 24)
        
        # Day of week encoding (0=Monday, 6=Sunday)
        day_map = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 
                   'Friday': 4, 'Saturday': 5, 'Sunday': 6}
        self.df['day_of_week_num'] = self.df['day_of_week'].map(day_map)
        self.df['is_weekend'] = (self.df['day_of_week_num'] >= 5).astype(int)
        
        # Time since epoch (for trend analysis)
        self.df['hours_since_start'] = (
            (self.df['timestamp'] - self.df['timestamp'].min()).dt.total_seconds() / 3600
        )
        
        # Time between readings
        self.df['minutes_since_last_reading'] = (
            self.df['timestamp'].diff().dt.total_seconds() / 60
        ).fillna(0)
        
        print("   ✅ Added: hour_sin/cos, day_of_week_num, is_weekend, hours_since_start")
    
    def create_moisture_features(self):
        """Create moisture-related features"""
        print("\n💧 Creating moisture features...")
        
        # Rolling statistics (different windows)
        for window in [3, 5, 10]:
            self.df[f'moisture_rolling_mean_{window}'] = (
                self.df['moisture_percent'].rolling(window=window, min_periods=1).mean()
            )
            self.df[f'moisture_rolling_std_{window}'] = (
                self.df['moisture_percent'].rolling(window=window, min_periods=1).std()
            ).fillna(0)
        
        # Moisture changes
        self.df['moisture_change'] = self.df['moisture_percent'].diff().fillna(0)
        self.df['moisture_change_abs'] = self.df['moisture_change'].abs()
        
        # Rate of change (per hour)
        hours_diff = self.df['minutes_since_last_reading'] / 60
        self.df['moisture_change_rate'] = (
            self.df['moisture_change'] / hours_diff.replace(0, np.nan)
        ).fillna(0)
        
        # Moisture deviation from daily average
        daily_avg = self.df.groupby(self.df['timestamp'].dt.date)['moisture_percent'].transform('mean')
        self.df['moisture_deviation_daily'] = self.df['moisture_percent'] - daily_avg
        
        # Moisture categories
        self.df['moisture_category'] = pd.cut(
            self.df['moisture_percent'],
            bins=[0, 20, 40, 60, 80, 100],
            labels=['very_dry', 'dry', 'optimal', 'moist', 'very_moist']
        )
        
        print("   ✅ Added: rolling stats, change rates, deviation, categories")
    
    def create_watering_features(self):
        """Create watering-related features"""
        print("\n🚿 Creating watering features...")
        
        # Time since last watering (forward fill)
        self.df['hours_since_watering'] = self.df['hours_since_last_water'].fillna(method='ffill')
        
        # Cumulative watering count
        self.df['cumulative_waterings'] = self.df['watered'].cumsum()
        
        # Watering frequency (last 24 hours)
        # Set timestamp as index temporarily for time-based rolling
        df_temp = self.df.set_index('timestamp')
        self.df['waterings_last_24h'] = (
            df_temp['watered'].rolling('24H').sum().values
        )
        
        # Days since last watering
        last_water_time = pd.NaT
        days_since = []
        
        for idx, row in self.df.iterrows():
            if row['watered'] == 1:
                last_water_time = row['timestamp']
                days_since.append(0)
            elif pd.notna(last_water_time):
                days_diff = (row['timestamp'] - last_water_time).days
                days_since.append(days_diff)
            else:
                days_since.append(np.nan)
        
        self.df['days_since_watering'] = days_since
        self.df['days_since_watering'] = self.df['days_since_watering'].fillna(method='ffill').fillna(0)
        
        print("   ✅ Added: hours/days since watering, cumulative count, frequency")
    
    def create_sensor_features(self):
        """Create sensor-specific features"""
        print("\n🔧 Creating sensor features...")
        
        # Sensor value statistics
        for window in [3, 5, 10]:
            self.df[f'sensor_rolling_mean_{window}'] = (
                self.df['raw_sensor_value'].rolling(window=window, min_periods=1).mean()
            )
        
        # Sensor stability (low std = stable)
        self.df['sensor_stability'] = (
            self.df['raw_sensor_value'].rolling(window=5, min_periods=1).std()
        ).fillna(0)
        
        # Sensor anomaly detection (z-score)
        sensor_mean = self.df['raw_sensor_value'].mean()
        sensor_std = self.df['raw_sensor_value'].std()
        self.df['sensor_zscore'] = (
            (self.df['raw_sensor_value'] - sensor_mean) / sensor_std
        )
        self.df['is_sensor_anomaly'] = (self.df['sensor_zscore'].abs() > 3).astype(int)
        
        print("   ✅ Added: sensor rolling stats, stability, anomaly detection")
    
    def create_target_variables(self):
        """Create target variables for ML models"""
        print("\n🎯 Creating target variables...")
        
        # Target 1: Will water in next hour?
        self.df['will_water_next_hour'] = 0
        for idx in range(len(self.df) - 1):
            current_time = self.df.loc[idx, 'timestamp']
            next_time = self.df.loc[idx + 1, 'timestamp']
            time_diff = (next_time - current_time).total_seconds() / 3600
            
            if time_diff <= 1 and self.df.loc[idx + 1, 'watered'] == 1:
                self.df.loc[idx, 'will_water_next_hour'] = 1
        
        # Target 2: Moisture in next reading
        self.df['next_moisture'] = self.df['moisture_percent'].shift(-1)
        self.df['moisture_change_next'] = self.df['moisture_change'].shift(-1)
        
        # Target 3: Should water? (based on thresholds)
        self.df['should_water'] = (
            (self.df['moisture_percent'] < 25) & 
            (self.df['hours_since_watering'] > 1)
        ).astype(int)
        
        print("   ✅ Added: will_water_next_hour, next_moisture, should_water")
    
    def create_interaction_features(self):
        """Create feature interactions"""
        print("\n🔗 Creating interaction features...")
        
        # Time × Moisture interactions
        self.df['hour_moisture_interaction'] = (
            self.df['hour_of_day'] * self.df['moisture_percent']
        )
        
        # Weekend × Moisture (different patterns on weekends?)
        self.df['weekend_moisture_interaction'] = (
            self.df['is_weekend'] * self.df['moisture_percent']
        )
        
        # Moisture deficit × Time since watering
        moisture_deficit = 100 - self.df['moisture_percent']
        self.df['deficit_time_interaction'] = (
            moisture_deficit * self.df['hours_since_watering']
        )
        
        print("   ✅ Added: time×moisture, weekend×moisture, deficit×time interactions")
    
    def select_ml_features(self):
        """Select and organize features for ML"""
        print("\n📋 Selecting ML features...")
        
        # Define feature groups
        self.temporal_features = [
            'hour_of_day', 'hour_sin', 'hour_cos', 'day_of_week_num', 
            'is_weekend', 'hours_since_start'
        ]
        
        self.moisture_features = [
            'moisture_percent', 'moisture_rolling_mean_3', 'moisture_rolling_mean_10',
            'moisture_change', 'moisture_change_rate', 'moisture_deviation_daily'
        ]
        
        self.watering_features = [
            'hours_since_watering', 'days_since_watering', 
            'cumulative_waterings', 'waterings_last_24h'
        ]
        
        self.sensor_features = [
            'raw_sensor_value', 'sensor_rolling_mean_5', 
            'sensor_stability', 'sensor_zscore'
        ]
        
        self.interaction_features = [
            'hour_moisture_interaction', 'weekend_moisture_interaction',
            'deficit_time_interaction'
        ]
        
        self.all_features = (
            self.temporal_features + self.moisture_features + 
            self.watering_features + self.sensor_features + 
            self.interaction_features
        )
        
        print(f"   ✅ Selected {len(self.all_features)} features for ML")
    
    def save_features(self):
        """Save engineered features"""
        print("\n💾 Saving features...")
        
        # Save full feature dataset
        self.df.to_csv('sprout_features.csv', index=False)
        print("   ✅ Saved: sprout_features.csv")
        
        # Save feature metadata
        metadata = {
            'created_at': datetime.now().isoformat(),
            'total_records': len(self.df),
            'total_features': len(self.df.columns),
            'feature_groups': {
                'temporal': self.temporal_features,
                'moisture': self.moisture_features,
                'watering': self.watering_features,
                'sensor': self.sensor_features,
                'interaction': self.interaction_features
            },
            'target_variables': [
                'will_water_next_hour', 'next_moisture', 'should_water'
            ],
            'feature_stats': {
                'moisture_avg': float(self.df['moisture_percent'].mean()),
                'total_waterings': int(self.df['watered'].sum()),
                'sensor_range': [
                    int(self.df['raw_sensor_value'].min()),
                    int(self.df['raw_sensor_value'].max())
                ]
            }
        }
        
        with open('sprout_features_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        print("   ✅ Saved: sprout_features_metadata.json")
        
        # Create ML-ready subset (no nulls in targets)
        ml_df = self.df[self.all_features + ['will_water_next_hour', 'next_moisture', 'should_water']]
        ml_df = ml_df.dropna()
        ml_df.to_csv('sprout_ml_ready.csv', index=False)
        print(f"   ✅ Saved: sprout_ml_ready.csv ({len(ml_df)} complete records)")
    
    def run_all(self):
        """Run complete feature engineering pipeline"""
        print("🚀 Starting feature engineering pipeline...")
        
        self.create_temporal_features()
        self.create_moisture_features()
        self.create_watering_features()
        self.create_sensor_features()
        self.create_interaction_features()
        self.create_target_variables()
        self.select_ml_features()
        self.save_features()
        
        print("\n✅ Feature engineering complete!")
        print(f"📊 Created {len(self.df.columns)} total features from {len(self.df_raw.columns)} original columns")
        
        return self.df


def main():
    """Run feature engineering"""
    engineer = SproutFeatureEngineer('sprout_data.csv')
    features_df = engineer.run_all()
    
    print("\n📋 Feature Summary:")
    print(f"   Shape: {features_df.shape}")
    print(f"   Memory: {features_df.memory_usage().sum() / 1024**2:.2f} MB")
    print("\n🎯 Ready for ML modeling!")


if __name__ == "__main__":
    main()
