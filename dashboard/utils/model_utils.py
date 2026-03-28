"""
Model loading and prediction utilities
"""
import pandas as pd
import numpy as np
import joblib
import json
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
import xgboost as xgb

from dashboard.config import MODELS_DIR, MODEL_CACHE_TTL, MODEL_FEATURES


@st.cache_resource(ttl=MODEL_CACHE_TTL)
def load_model_artifacts(model_timestamp):
    """Load model artifacts (model, scaler, selector, metadata)"""
    try:
        # File paths - try multiple naming patterns
        # First try the enhanced model name
        model_path = MODELS_DIR / f"xgb_enhanced_{model_timestamp}.joblib"
        if not model_path.exists():
            # Try the pipeline name
            model_path = MODELS_DIR / f"sales_prediction_pipeline_{model_timestamp}.joblib"
        if not model_path.exists():
            # Try the standard name
            model_path = MODELS_DIR / f"xgboost_model_{model_timestamp}.joblib"
        
        scaler_path = MODELS_DIR / f"scaler_{model_timestamp}.joblib"
        selector_path = MODELS_DIR / f"feature_selector_{model_timestamp}.joblib"
        poly_path = MODELS_DIR / f"poly_features_{model_timestamp}.joblib"
        metadata_path = MODELS_DIR / f"model_metadata_{model_timestamp}.json"
        
        # Load artifacts
        artifacts = {}
        
        if model_path.exists():
            artifacts['model'] = joblib.load(model_path)
        
        if scaler_path.exists():
            artifacts['scaler'] = joblib.load(scaler_path)
        
        if selector_path.exists():
            artifacts['selector'] = joblib.load(selector_path)
        
        if poly_path.exists():
            artifacts['poly_features'] = joblib.load(poly_path)
        
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                artifacts['metadata'] = json.load(f)
        
        return artifacts
    except Exception as e:
        st.error(f"Error loading model artifacts: {str(e)}")
        return {}


@st.cache_data(ttl=MODEL_CACHE_TTL)
def get_available_models():
    """Get list of available models with their metadata"""
    models = []
    
    for metadata_file in MODELS_DIR.glob("model_metadata_*.json"):
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            timestamp = metadata_file.stem.replace("model_metadata_", "")
            
            models.append({
                'timestamp': timestamp,
                'display_name': f"{metadata.get('model_type', 'Unknown')} - {timestamp}",
                'performance': metadata.get('performance_metrics', {}),
                'features': metadata.get('selected_features', []),
                'training_period': metadata.get('training_data_period', {})
            })
        except Exception as e:
            continue
    
    # Sort by timestamp (newest first)
    models.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return models


@st.cache_data(ttl=MODEL_CACHE_TTL)
def get_model_artifacts_summary():
    """Get comprehensive summary of all model artifacts"""
    artifacts_summary = {
        'total_models': 0,
        'total_artifacts': 0,
        'artifact_types': {},
        'timestamps': [],
        'model_types': set()
    }
    
    # Count all model-related files
    artifact_patterns = {
        'xgb_enhanced': 'XGBoost Models',
        'sales_prediction_pipeline': 'Prediction Pipelines', 
        'scaler': 'Data Scalers',
        'feature_selector': 'Feature Selectors',
        'poly_features': 'Polynomial Features',
        'model_metadata': 'Model Metadata'
    }
    
    for pattern, description in artifact_patterns.items():
        matching_files = list(MODELS_DIR.glob(f"{pattern}_*.joblib")) + list(MODELS_DIR.glob(f"{pattern}_*.json"))
        count = len(matching_files)
        
        if count > 0:
            artifacts_summary['artifact_types'][description] = count
            artifacts_summary['total_artifacts'] += count
            
            # Extract timestamps
            for file in matching_files:
                timestamp_part = file.stem.split('_')[-1]
                if timestamp_part not in artifacts_summary['timestamps']:
                    artifacts_summary['timestamps'].append(timestamp_part)
    
    # Get model metadata for additional info
    for metadata_file in MODELS_DIR.glob("model_metadata_*.json"):
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            artifacts_summary['total_models'] += 1
            model_type = metadata.get('model_type', 'Unknown')
            artifacts_summary['model_types'].add(model_type)
            
        except Exception:
            continue
    
    # Convert set to list for JSON serialization
    artifacts_summary['model_types'] = list(artifacts_summary['model_types'])
    artifacts_summary['timestamps'] = sorted(list(set(artifacts_summary['timestamps'])), reverse=True)
    
    return artifacts_summary


def prepare_features_for_prediction(df, selected_features):
    """Prepare features dataframe for model prediction"""
    # Create a copy to avoid modifying original
    df_copy = df.copy()
    
    # Ensure all required features exist
    missing_features = set(selected_features) - set(df_copy.columns)
    for feature in missing_features:
        # Initialize missing features with appropriate defaults
        if 'Lag' in feature or 'MA' in feature or 'Volatility' in feature:
            # For lag and rolling features, use 0 as default
            df_copy[feature] = 0
        else:
            df_copy[feature] = 0
    
    # Select only the features used by the model in the correct order
    return df_copy[selected_features]


def make_predictions(artifacts, input_data):
    """Make predictions using loaded model artifacts"""
    try:
        model = artifacts.get('model')
        scaler = artifacts.get('scaler')
        selector = artifacts.get('selector')
        poly_features = artifacts.get('poly_features')
        
        if model is None:
            return None, "Model not found"
        
        # Get the expected features from metadata
        selected_features = artifacts.get('metadata', {}).get('selected_features', [])
        
        # Ensure input data has all required features in correct order
        X = input_data[selected_features].copy()
        
        # The model expects the features already processed (after polynomial transformation)
        # Since the saved model is the final XGBoost model after all transformations,
        # we can directly predict with it
        
        # Make predictions
        predictions = model.predict(X)
        
        return predictions, None
    except Exception as e:
        return None, str(e)


def create_future_features(last_date, n_days, historical_data):
    """Create feature dataframe for future predictions"""
    future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=n_days, freq='D')
    
    future_df = pd.DataFrame({
        'Date': future_dates,
        'Year': future_dates.year,
        'Month': future_dates.month,
        'DayOfWeek': future_dates.dayofweek,
        'WeekOfYear': future_dates.isocalendar().week,
        'Quarter': future_dates.quarter,
        'DayOfYear': future_dates.dayofyear
    })
    
    # Add binary features
    future_df['IsWeekend'] = (future_df['DayOfWeek'] >= 5).astype(int)
    future_df['IsMonthStart'] = (future_dates.day == 1).astype(int)
    # Calculate IsMonthEnd properly
    future_df['IsMonthEnd'] = (future_dates.day == pd.Series(future_dates).dt.days_in_month).astype(int)
    
    # Add cyclical features
    future_df['DayOfWeek_sin'] = np.sin(2 * np.pi * future_df['DayOfWeek'] / 7)
    future_df['DayOfWeek_cos'] = np.cos(2 * np.pi * future_df['DayOfWeek'] / 7)
    future_df['Month_sin'] = np.sin(2 * np.pi * future_df['Month'] / 12)
    future_df['Month_cos'] = np.cos(2 * np.pi * future_df['Month'] / 12)
    future_df['DayOfYear_sin'] = np.sin(2 * np.pi * future_df['DayOfYear'] / 365)
    future_df['DayOfYear_cos'] = np.cos(2 * np.pi * future_df['DayOfYear'] / 365)
    
    # Initialize all lag and rolling features with appropriate values
    # Get historical revenue data
    if historical_data is not None and not historical_data.empty:
        # Get the last 30 days of revenue for lag calculations
        recent_revenue = historical_data['Daily_Revenue'].tail(30).values
        
        # Initialize lag features using recent historical data
        for i in range(n_days):
            for lag in [1, 2, 3, 7, 14, 30]:
                if i == 0:  # First prediction day
                    if len(recent_revenue) >= lag:
                        future_df.loc[i, f'Revenue_Lag_{lag}'] = recent_revenue[-lag]
                    else:
                        future_df.loc[i, f'Revenue_Lag_{lag}'] = 0
                else:
                    # For subsequent days, we would need to use predictions
                    # For now, use the average of recent data
                    future_df.loc[i, f'Revenue_Lag_{lag}'] = recent_revenue.mean() if len(recent_revenue) > 0 else 0
        
        # Set moving averages using recent historical data
        if len(recent_revenue) >= 7:
            future_df['Revenue_MA_7'] = recent_revenue[-7:].mean()
        else:
            future_df['Revenue_MA_7'] = recent_revenue.mean() if len(recent_revenue) > 0 else 0
            
        if len(recent_revenue) >= 30:
            future_df['Revenue_MA_30'] = recent_revenue.mean()
        else:
            future_df['Revenue_MA_30'] = recent_revenue.mean() if len(recent_revenue) > 0 else 0
        
        # Set volatility features
        if len(recent_revenue) >= 7:
            future_df['Revenue_Volatility_7'] = recent_revenue[-7:].std()
        else:
            future_df['Revenue_Volatility_7'] = 0
            
        if len(recent_revenue) >= 30:
            future_df['Revenue_Volatility_30'] = recent_revenue.std()
        else:
            future_df['Revenue_Volatility_30'] = 0
    else:
        # If no historical data, initialize with zeros
        for lag in [1, 2, 3, 7, 14, 30]:
            future_df[f'Revenue_Lag_{lag}'] = 0
        future_df['Revenue_MA_7'] = 0
        future_df['Revenue_MA_30'] = 0
        future_df['Revenue_Volatility_7'] = 0
        future_df['Revenue_Volatility_30'] = 0
    
    # Add polynomial interaction features with space-separated names
    future_df['Revenue_Lag_1 Revenue_Lag_2'] = future_df['Revenue_Lag_1'] * future_df['Revenue_Lag_2']
    future_df['Revenue_Lag_1 Revenue_Lag_3'] = future_df['Revenue_Lag_1'] * future_df['Revenue_Lag_3']
    future_df['Revenue_Lag_1 Revenue_Lag_7'] = future_df['Revenue_Lag_1'] * future_df['Revenue_Lag_7']
    future_df['Revenue_Lag_2 Revenue_Lag_3'] = future_df['Revenue_Lag_2'] * future_df['Revenue_Lag_3']
    future_df['Revenue_Lag_2 Revenue_Lag_7'] = future_df['Revenue_Lag_2'] * future_df['Revenue_Lag_7']
    future_df['Revenue_Lag_3 Revenue_Lag_7'] = future_df['Revenue_Lag_3'] * future_df['Revenue_Lag_7']
    
    return future_df


def calculate_prediction_intervals(predictions, model_mae, confidence=0.95):
    """Calculate prediction intervals based on model MAE"""
    # Simple approach using MAE
    z_score = 1.96 if confidence == 0.95 else 2.58  # 95% or 99% confidence
    
    lower_bound = predictions - (z_score * model_mae)
    upper_bound = predictions + (z_score * model_mae)
    
    # Ensure non-negative predictions
    lower_bound = np.maximum(lower_bound, 0)
    
    return lower_bound, upper_bound


def get_feature_importance(model, feature_names):
    """Extract feature importance from model"""
    if hasattr(model, 'feature_importances_'):
        importance = model.feature_importances_
        
        # Create dataframe
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        # Normalize to percentage
        importance_df['importance_pct'] = (importance_df['importance'] / importance_df['importance'].sum() * 100)
        
        return importance_df
    
    return pd.DataFrame()


def evaluate_model_on_test_data(model, X_test, y_test):
    """Evaluate model performance on test data"""
    predictions = model.predict(X_test)
    
    mae = np.mean(np.abs(y_test - predictions))
    rmse = np.sqrt(np.mean((y_test - predictions) ** 2))
    r2 = 1 - (np.sum((y_test - predictions) ** 2) / np.sum((y_test - y_test.mean()) ** 2))
    
    # MAPE
    mask = y_test != 0
    if mask.sum() > 0:
        mape = np.mean(np.abs((y_test[mask] - predictions[mask]) / y_test[mask])) * 100
    else:
        mape = np.nan
    
    return {
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'mape': mape
    }