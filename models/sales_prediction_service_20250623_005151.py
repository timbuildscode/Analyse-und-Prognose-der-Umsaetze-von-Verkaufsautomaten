#!/usr/bin/env python3
"""
Vending Machine Sales Prediction Service
Generated on: 2025-06-23 00:51:51
"""

import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

class SalesPredictionService:
    def __init__(self, pipeline_path="../models/sales_prediction_pipeline_20250623_005151.joblib"):
        """Initialize the prediction service"""
        self.pipeline = joblib.load(pipeline_path)
        self.metadata = self.pipeline.get_metadata()
        print(f" Loaded model with R² = {self.metadata['performance_metrics']['test_r2']:.3f}")
    
    def predict_daily_sales(self, date, machine_id=None, product_features=None):
        """
        Predict daily sales for a specific date
        
        Parameters:
        -----------
        date : str or datetime
            Date for prediction
        machine_id : str, optional
            Machine identifier
        product_features : dict, optional
            Additional product features
        
        Returns:
        --------
        dict : Prediction results
        """
        # This is a simplified prediction function
        # In production, you would implement full feature engineering pipeline
        
        # For demonstration, create dummy features
        dummy_features = pd.DataFrame({
            'dayofweek': [pd.to_datetime(date).dayofweek],
            'month': [pd.to_datetime(date).month],
            'is_weekend': [1 if pd.to_datetime(date).dayofweek >= 5 else 0],
            # Add more features as needed...
        })
        
        # Make prediction
        prediction = self.pipeline.predict(dummy_features)[0]
        
        return {
            'date': str(date),
            'predicted_revenue': float(prediction),
            'model_version': self.metadata.get('timestamp', 'unknown'),
            'confidence': 'high' if prediction > 0 else 'low'
        }
    
    def get_model_info(self):
        """Get model information"""
        return {
            'model_type': self.metadata.get('model_type', 'Unknown'),
            'performance': self.metadata.get('performance_metrics', {}),
            'feature_count': self.metadata.get('feature_count', 0),
            'training_period': self.metadata.get('training_data_period', {}),
            'version': self.metadata.get('timestamp', 'unknown')
        }

# Example usage
if __name__ == "__main__":
    # Initialize service
    service = SalesPredictionService()
    
    # Get model info
    info = service.get_model_info()
    print("Model Info:", json.dumps(info, indent=2))
    
    # Make a prediction
    prediction = service.predict_daily_sales("2024-12-01")
    print("Prediction:", json.dumps(prediction, indent=2))
