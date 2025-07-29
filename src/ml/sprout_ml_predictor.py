#!/usr/bin/env python3
"""
SproutML Moisture Predictor
Trains a model to predict future moisture levels
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import json
from datetime import datetime

class MoisturePredictor:
    def __init__(self):
        """Initialize predictor with data"""
        print("🌱 SproutML Moisture Predictor v1.0\n")
        
        # Load the ML-ready data
        self.df = pd.read_csv('sprout_ml_ready.csv')
        print(f"📊 Loaded {len(self.df)} ML-ready records")
        
        # Load feature metadata
        with open('sprout_features_metadata.json', 'r') as f:
            self.metadata = json.load(f)
        
        self.models = {}
        self.results = {}
        
    def prepare_data(self):
        """Prepare features and targets for training"""
        print("\n🔧 Preparing data for training...")
        
        # Select features (exclude targets and identifiers)
        feature_cols = []
        exclude = ['next_moisture', 'will_water_next_hour', 'should_water', 
                  'moisture_change_next', 'timestamp', 'date', 'time', 
                  'day_of_week', 'action_taken', 'notes']
        
        for col in self.df.columns:
            if col not in exclude and not col.startswith('temperature') and not col.startswith('humidity'):
                feature_cols.append(col)
        
        # Prepare feature matrix and target
        self.X = self.df[feature_cols]
        self.y = self.df['next_moisture']
        
        # Remove rows with missing targets
        mask = ~self.y.isna()
        self.X = self.X[mask]
        self.y = self.y[mask]
        
        print(f"   ✅ Features: {len(feature_cols)} columns")
        print(f"   ✅ Target: next_moisture")
        print(f"   ✅ Samples: {len(self.X)} complete records")
        
        # Split data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42
        )
        
        print(f"   ✅ Training set: {len(self.X_train)} samples")
        print(f"   ✅ Test set: {len(self.X_test)} samples")
        
        return feature_cols
    
    def train_models(self):
        """Train multiple models and compare"""
        print("\n🤖 Training models...")
        
        # Model 1: Linear Regression (simple baseline)
        print("\n1️⃣ Training Linear Regression...")
        lr = LinearRegression()
        lr.fit(self.X_train, self.y_train)
        self.models['linear'] = lr
        
        # Evaluate
        lr_pred = lr.predict(self.X_test)
        lr_mae = mean_absolute_error(self.y_test, lr_pred)
        lr_r2 = r2_score(self.y_test, lr_pred)
        
        self.results['linear'] = {
            'mae': lr_mae,
            'r2': lr_r2,
            'predictions': lr_pred
        }
        print(f"   MAE: {lr_mae:.2f}% moisture")
        print(f"   R²: {lr_r2:.3f}")
        
        # Model 2: Random Forest (more complex)
        print("\n2️⃣ Training Random Forest...")
        rf = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
        rf.fit(self.X_train, self.y_train)
        self.models['random_forest'] = rf
        
        # Evaluate
        rf_pred = rf.predict(self.X_test)
        rf_mae = mean_absolute_error(self.y_test, rf_pred)
        rf_r2 = r2_score(self.y_test, rf_pred)
        
        self.results['random_forest'] = {
            'mae': rf_mae,
            'r2': rf_r2,
            'predictions': rf_pred
        }
        print(f"   MAE: {rf_mae:.2f}% moisture")
        print(f"   R²: {rf_r2:.3f}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.X.columns,
            'importance': rf.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n📊 Top 10 Most Important Features:")
        for idx, row in feature_importance.head(10).iterrows():
            print(f"   {row['feature']}: {row['importance']:.3f}")
        
        self.feature_importance = feature_importance
        
    def visualize_results(self):
        """Create visualizations of model performance"""
        print("\n📈 Creating visualizations...")
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. Predictions vs Actual (Linear)
        ax = axes[0, 0]
        ax.scatter(self.y_test, self.results['linear']['predictions'], alpha=0.5)
        ax.plot([self.y_test.min(), self.y_test.max()], 
                [self.y_test.min(), self.y_test.max()], 'r--', lw=2)
        ax.set_xlabel('Actual Moisture %')
        ax.set_ylabel('Predicted Moisture %')
        ax.set_title(f"Linear Regression (MAE: {self.results['linear']['mae']:.1f}%)")
        ax.grid(True, alpha=0.3)
        
        # 2. Predictions vs Actual (Random Forest)
        ax = axes[0, 1]
        ax.scatter(self.y_test, self.results['random_forest']['predictions'], 
                  alpha=0.5, color='green')
        ax.plot([self.y_test.min(), self.y_test.max()], 
                [self.y_test.min(), self.y_test.max()], 'r--', lw=2)
        ax.set_xlabel('Actual Moisture %')
        ax.set_ylabel('Predicted Moisture %')
        ax.set_title(f"Random Forest (MAE: {self.results['random_forest']['mae']:.1f}%)")
        ax.grid(True, alpha=0.3)
        
        # 3. Feature Importance
        ax = axes[1, 0]
        top_features = self.feature_importance.head(10)
        ax.barh(range(len(top_features)), top_features['importance'])
        ax.set_yticks(range(len(top_features)))
        ax.set_yticklabels(top_features['feature'])
        ax.set_xlabel('Importance')
        ax.set_title('Top 10 Feature Importances')
        ax.grid(True, alpha=0.3)
        
        # 4. Error Distribution
        ax = axes[1, 1]
        rf_errors = self.results['random_forest']['predictions'] - self.y_test
        ax.hist(rf_errors, bins=20, alpha=0.7, color='blue', edgecolor='black')
        ax.axvline(x=0, color='red', linestyle='--', alpha=0.5)
        ax.set_xlabel('Prediction Error (%)')
        ax.set_ylabel('Frequency')
        ax.set_title('Prediction Error Distribution')
        ax.grid(True, alpha=0.3)
        
        plt.suptitle('🌱 Moisture Prediction Model Results', fontsize=16)
        plt.tight_layout()
        plt.savefig('sprout_ml_predictions.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("   ✅ Saved: sprout_ml_predictions.png")
    
    def save_model(self):
        """Save the best model for production use"""
        print("\n💾 Saving model...")
        
        # Select best model based on MAE
        if self.results['random_forest']['mae'] < self.results['linear']['mae']:
            best_model = 'random_forest'
        else:
            best_model = 'linear'
        
        print(f"   🏆 Best model: {best_model}")
        
        # Save model
        joblib.dump(self.models[best_model], 'sprout_moisture_model.pkl')
        print("   ✅ Saved: sprout_moisture_model.pkl")
        
        # Save model info
        model_info = {
            'model_type': best_model,
            'trained_at': datetime.now().isoformat(),
            'performance': {
                'mae': float(self.results[best_model]['mae']),
                'r2': float(self.results[best_model]['r2'])
            },
            'features': list(self.X.columns),
            'training_samples': len(self.X_train),
            'test_samples': len(self.X_test)
        }
        
        with open('sprout_model_info.json', 'w') as f:
            json.dump(model_info, f, indent=2)
        print("   ✅ Saved: sprout_model_info.json")
    
    def test_live_prediction(self):
        """Test prediction with latest data"""
        print("\n🔮 Testing live prediction...")
        
        # Load the best model
        model = joblib.load('sprout_moisture_model.pkl')
        
        # Get latest features
        latest_features = self.X.iloc[-1:].copy()
        
        # Make prediction
        prediction = model.predict(latest_features)[0]
        current_moisture = self.df.iloc[-1]['moisture_percent']
        
        print(f"\n   Current moisture: {current_moisture:.1f}%")
        print(f"   Predicted next moisture: {prediction:.1f}%")
        print(f"   Expected change: {prediction - current_moisture:+.1f}%")
        
        if prediction < current_moisture - 5:
            print("   📉 Moisture expected to decrease significantly")
        elif prediction > current_moisture + 5:
            print("   📈 Moisture expected to increase significantly")
        else:
            print("   ➡️ Moisture expected to remain stable")
    
    def run_all(self):
        """Run complete training pipeline"""
        self.prepare_data()
        self.train_models()
        self.visualize_results()
        self.save_model()
        self.test_live_prediction()
        
        print("\n✅ Model training complete!")
        print("🎯 Your moisture predictor is ready to use!")


def main():
    """Train the moisture prediction model"""
    predictor = MoisturePredictor()
    predictor.run_all()


if __name__ == "__main__":
    main()
