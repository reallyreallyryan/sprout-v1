#!/usr/bin/env python3
"""
SproutML Data Visualizer
Comprehensive visualization of Sprout's sensor data and watering patterns
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class SproutVisualizer:
    def __init__(self, csv_path='sprout_data.csv'):
        """Initialize visualizer with data"""
        self.df = self.load_and_prep_data(csv_path)
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
        
    def load_and_prep_data(self, csv_path):
        """Load and prepare data for analysis"""
        print("📊 Loading Sprout data...")
        df = pd.read_csv(csv_path)
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Fill missing moisture values with forward fill
        df['moisture_percent'] = df['moisture_percent'].fillna(method='ffill')
        
        # Calculate time since last reading
        df['time_since_last_reading'] = df['timestamp'].diff().dt.total_seconds() / 60  # minutes
        
        print(f"✅ Loaded {len(df)} readings")
        print(f"📅 Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"💧 Total waterings: {df['watered'].sum()}")
        print(f"📈 Avg moisture: {df['moisture_percent'].mean():.1f}%\n")
        
        return df
    
    def plot_moisture_timeline(self):
        """Plot moisture over time with watering events"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                       gridspec_kw={'height_ratios': [3, 1]})
        
        # Main moisture plot
        ax1.plot(self.df['timestamp'], self.df['moisture_percent'], 
                 'b-', alpha=0.7, linewidth=2, label='Moisture %')
        
        # Add watering events
        water_events = self.df[self.df['watered'] == 1]
        ax1.scatter(water_events['timestamp'], water_events['moisture_percent'], 
                   color='cyan', s=200, marker='v', edgecolor='blue', 
                   linewidth=2, label='Watering Event', zorder=5)
        
        # Add threshold lines
        ax1.axhline(y=25, color='red', linestyle='--', alpha=0.5, label='Dry Threshold')
        ax1.axhline(y=45, color='green', linestyle='--', alpha=0.5, label='Wet Threshold')
        
        # Formatting
        ax1.set_ylabel('Moisture %', fontsize=12)
        ax1.set_title('🌱 Sprout Moisture Timeline', fontsize=16, fontweight='bold')
        ax1.legend(loc='upper right')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 100)
        
        # Raw sensor values subplot
        ax2.plot(self.df['timestamp'], self.df['raw_sensor_value'], 
                 'orange', alpha=0.7, linewidth=1)
        ax2.set_ylabel('Raw Sensor', fontsize=10)
        ax2.set_xlabel('Time', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('sprout_moisture_timeline.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_daily_patterns(self):
        """Analyze patterns by hour of day"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. Average moisture by hour
        hourly_moisture = self.df.groupby('hour_of_day')['moisture_percent'].agg(['mean', 'std'])
        ax = axes[0, 0]
        ax.bar(hourly_moisture.index, hourly_moisture['mean'], 
               yerr=hourly_moisture['std'], capsize=5, alpha=0.7)
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Avg Moisture %')
        ax.set_title('📊 Moisture by Hour of Day')
        ax.set_xticks(range(0, 24, 2))
        
        # 2. Watering frequency by hour
        hourly_water = self.df.groupby('hour_of_day')['watered'].sum()
        ax = axes[0, 1]
        ax.bar(hourly_water.index, hourly_water.values, color='cyan', alpha=0.7)
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Watering Count')
        ax.set_title('💧 Watering Events by Hour')
        ax.set_xticks(range(0, 24, 2))
        
        # 3. Moisture by day of week
        daily_moisture = self.df.groupby('day_of_week')['moisture_percent'].mean()
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_moisture = daily_moisture.reindex(day_order)
        ax = axes[1, 0]
        ax.bar(range(len(daily_moisture)), daily_moisture.values, alpha=0.7)
        ax.set_xticklabels([d[:3] for d in day_order], rotation=45)
        ax.set_ylabel('Avg Moisture %')
        ax.set_title('📅 Moisture by Day of Week')
        
        # 4. Action distribution
        action_counts = self.df['action_taken'].value_counts()
        ax = axes[1, 1]
        colors = ['green' if 'checked' in x else 'cyan' if 'watered' in x else 'orange' for x in action_counts.index]
        ax.pie(action_counts.values, labels=action_counts.index, autopct='%1.1f%%',
               colors=colors, startangle=90)
        ax.set_title('🎯 Action Distribution')
        
        plt.suptitle('Sprout Behavioral Patterns', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig('sprout_daily_patterns.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_moisture_dynamics(self):
        """Analyze moisture change dynamics"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Calculate moisture changes
        self.df['moisture_change'] = self.df['moisture_percent'].diff()
        self.df['moisture_change_rate'] = self.df['moisture_change'] / self.df['time_since_last_reading']
        
        # 1. Moisture change distribution
        ax = axes[0, 0]
        self.df['moisture_change'].dropna().hist(bins=50, ax=ax, alpha=0.7, color='purple')
        ax.set_xlabel('Moisture Change %')
        ax.set_ylabel('Frequency')
        ax.set_title('📉 Moisture Change Distribution')
        ax.axvline(x=0, color='red', linestyle='--', alpha=0.5)
        
        # 2. Moisture vs Time Since Watering
        ax = axes[0, 1]
        # Create a scatter plot with color gradient for time since watering
        scatter = ax.scatter(self.df['hours_since_last_water'], 
                           self.df['moisture_percent'],
                           c=self.df['hour_of_day'], 
                           cmap='viridis', alpha=0.6)
        ax.set_xlabel('Hours Since Last Watering')
        ax.set_ylabel('Moisture %')
        ax.set_title('⏱️ Moisture vs Time Since Watering')
        plt.colorbar(scatter, ax=ax, label='Hour of Day')
        
        # 3. Moisture before and after watering
        ax = axes[1, 0]
        water_indices = self.df[self.df['watered'] == 1].index
        before_after = []
        
        for idx in water_indices:
            if idx > 0 and idx < len(self.df) - 1:
                before = self.df.loc[idx-1, 'moisture_percent']
                after = self.df.loc[idx+1, 'moisture_percent'] if idx+1 < len(self.df) else before
                before_after.append([before, after])
        
        if before_after:
            before_after = np.array(before_after)
            x = ['Before', 'After']
            for i, (b, a) in enumerate(before_after):
                ax.plot(x, [b, a], 'o-', alpha=0.5, color='blue')
            ax.set_ylabel('Moisture %')
            ax.set_title('💧 Moisture Before/After Watering')
            ax.grid(True, alpha=0.3)
        
        # 4. Correlation heatmap
        ax = axes[1, 1]
        corr_columns = ['hour_of_day', 'moisture_percent', 'raw_sensor_value', 
                       'watered', 'hours_since_last_water']
        corr_data = self.df[corr_columns].dropna()
        correlation = corr_data.corr()
        sns.heatmap(correlation, annot=True, fmt='.2f', cmap='coolwarm', 
                   center=0, ax=ax, square=True)
        ax.set_title('🔗 Feature Correlations')
        
        plt.suptitle('Moisture Dynamics Analysis', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig('sprout_moisture_dynamics.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_sensor_calibration(self):
        """Visualize sensor calibration and response"""
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        # 1. Raw vs Moisture % relationship
        ax = axes[0]
        scatter = ax.scatter(self.df['raw_sensor_value'], self.df['moisture_percent'],
                           c=self.df['watered'], cmap='coolwarm', alpha=0.6)
        ax.set_xlabel('Raw Sensor Value')
        ax.set_ylabel('Moisture %')
        ax.set_title('🔧 Sensor Calibration Curve')
        ax.grid(True, alpha=0.3)
        
        # Add calibration line
        if len(self.df) > 2:
            z = np.polyfit(self.df['raw_sensor_value'].dropna(), 
                          self.df['moisture_percent'].dropna(), 1)
            p = np.poly1d(z)
            x_line = np.linspace(self.df['raw_sensor_value'].min(), 
                               self.df['raw_sensor_value'].max(), 100)
            ax.plot(x_line, p(x_line), "r--", alpha=0.8, label=f'y={z[0]:.2f}x+{z[1]:.2f}')
            ax.legend()
        
        # 2. Sensor value distribution
        ax = axes[1]
        self.df['raw_sensor_value'].hist(bins=30, ax=ax, alpha=0.7, color='green')
        ax.set_xlabel('Raw Sensor Value')
        ax.set_ylabel('Frequency')
        ax.set_title('📊 Sensor Value Distribution')
        ax.axvline(x=700, color='red', linestyle='--', alpha=0.5, label='Dry Threshold')
        ax.axvline(x=600, color='blue', linestyle='--', alpha=0.5, label='Wet Threshold')
        ax.legend()
        
        plt.tight_layout()
        plt.savefig('sprout_sensor_calibration.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_summary_report(self):
        """Generate a text summary of findings"""
        report = []
        report.append("=" * 50)
        report.append("SPROUT DATA ANALYSIS SUMMARY")
        report.append("=" * 50)
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Readings: {len(self.df)}")
        report.append(f"Date Range: {self.df['timestamp'].min()} to {self.df['timestamp'].max()}")
        report.append("")
        
        # Moisture statistics
        report.append("MOISTURE STATISTICS:")
        report.append(f"  Average: {self.df['moisture_percent'].mean():.1f}%")
        report.append(f"  Std Dev: {self.df['moisture_percent'].std():.1f}%")
        report.append(f"  Min: {self.df['moisture_percent'].min():.1f}%")
        report.append(f"  Max: {self.df['moisture_percent'].max():.1f}%")
        report.append("")
        
        # Watering statistics
        water_events = self.df[self.df['watered'] == 1]
        if len(water_events) > 0:
            report.append("WATERING STATISTICS:")
            report.append(f"  Total Events: {len(water_events)}")
            report.append(f"  Total Duration: {water_events['water_duration_sec'].sum()}s")
            report.append(f"  Avg Duration: {water_events['water_duration_sec'].mean():.1f}s")
            report.append("")
        
        # Time patterns
        report.append("TIME PATTERNS:")
        most_active_hour = self.df.groupby('hour_of_day').size().idxmax()
        report.append(f"  Most Active Hour: {most_active_hour}:00")
        
        if len(water_events) > 0:
            most_water_hour = water_events.groupby('hour_of_day').size().idxmax()
            report.append(f"  Most Common Watering Hour: {most_water_hour}:00")
        report.append("")
        
        # Save report
        report_text = "\n".join(report)
        with open('sprout_analysis_report.txt', 'w') as f:
            f.write(report_text)
        
        print(report_text)
        return report_text


def main():
    """Run all visualizations"""
    print("🌱 SproutML Data Visualizer\n")
    
    # Initialize visualizer
    viz = SproutVisualizer('sprout_data.csv')
    
    print("Generating visualizations...")
    
    # Generate all plots
    print("\n1️⃣ Creating moisture timeline...")
    viz.plot_moisture_timeline()
    
    print("\n2️⃣ Analyzing daily patterns...")
    viz.plot_daily_patterns()
    
    print("\n3️⃣ Studying moisture dynamics...")
    viz.plot_moisture_dynamics()
    
    print("\n4️⃣ Examining sensor calibration...")
    viz.plot_sensor_calibration()
    
    print("\n5️⃣ Generating summary report...")
    viz.generate_summary_report()
    
    print("\n✅ All visualizations complete!")
    print("📁 Output files:")
    print("   - sprout_moisture_timeline.png")
    print("   - sprout_daily_patterns.png")
    print("   - sprout_moisture_dynamics.png")
    print("   - sprout_sensor_calibration.png")
    print("   - sprout_analysis_report.txt")


if __name__ == "__main__":
    main()
