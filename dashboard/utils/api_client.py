"""
API Client for vending machine predictions
"""

import requests
import streamlit as st
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Any
import pandas as pd
from ..config import API_BASE_URL, API_ENDPOINTS, API_TIMEOUT


class PredictionAPIClient:
    """Client for interacting with the prediction API"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.timeout = API_TIMEOUT
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[Any, Any]]:
        """Make a request to the API with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError:
            st.error("🔌 Cannot connect to the prediction API. Please ensure the API server is running.")
            return None
        except requests.exceptions.Timeout:
            st.error("⏱️ API request timed out. Please try again.")
            return None
        except requests.exceptions.HTTPError as e:
            st.error(f" API error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            st.error(f" Unexpected error: {str(e)}")
            return None
    
    def health_check(self) -> bool:
        """Check if the API is healthy"""
        response = self._make_request('GET', API_ENDPOINTS['health'])
        return response is not None and response.get('status') == 'healthy'
    
    def get_model_info(self) -> Optional[Dict[Any, Any]]:
        """Get information about the current model"""
        return self._make_request('GET', API_ENDPOINTS['model_info'])
    
    def predict_single_date(self, prediction_date: date, machine_id: Optional[str] = None) -> Optional[Dict[Any, Any]]:
        """Predict sales for a single date"""
        payload = {
            "date": prediction_date.strftime('%Y-%m-%d'),
            "machine_id": machine_id
        }
        
        return self._make_request('POST', API_ENDPOINTS['predict'], json=payload)
    
    def predict_date_range(self, start_date: date, end_date: date, machine_id: Optional[str] = None) -> Optional[Dict[Any, Any]]:
        """Predict sales for a date range"""
        params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
        
        if machine_id:
            params['machine_id'] = machine_id
        
        return self._make_request('GET', API_ENDPOINTS['batch_predict'], params=params)
    
    def predict_to_dataframe(self, start_date: date, end_date: date, machine_id: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Get predictions as a pandas DataFrame"""
        response = self.predict_date_range(start_date, end_date, machine_id)
        
        if response and 'predictions' in response:
            predictions = response['predictions']
            df = pd.DataFrame(predictions)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
            return df
        
        return None
    
    def predict_raw_features(self, features_dict: dict) -> Optional[dict]:
        """Make a raw prediction using custom feature values"""
        return self._make_request('POST', API_ENDPOINTS['raw_predict'], json=features_dict)


# Singleton instance
@st.cache_resource
def get_api_client(version: str = "v1.1") -> PredictionAPIClient:
    """Get a cached API client instance with version support"""
    return PredictionAPIClient()


def format_prediction_confidence(confidence: str) -> str:
    """Format confidence level with appropriate emoji"""
    confidence_map = {
        'high': ' High',
        'medium': ' Medium', 
        'low': ' Low'
    }
    return confidence_map.get(confidence.lower(), f"❓ {confidence}")


def format_currency(value: float) -> str:
    """Format currency values"""
    return f"€{value:.2f}"


def create_prediction_summary_card(prediction: Dict[Any, Any]) -> None:
    """Create a summary card for a single prediction"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label=" Date",
            value=prediction['date']
        )
    
    with col2:
        st.metric(
            label="💰 Predicted Revenue",
            value=format_currency(prediction['predicted_revenue'])
        )
    
    with col3:
        st.metric(
            label=" Confidence",
            value=format_prediction_confidence(prediction['confidence'])
        )


def display_model_info(model_info: Dict[Any, Any]) -> None:
    """Display model information in an organized way"""
    st.subheader(" Model Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Model Details:**")
        st.write(f"- **Type:** {model_info.get('model_type', 'Unknown')}")
        st.write(f"- **Version:** {model_info.get('version', 'Unknown')}")
        st.write(f"- **Features:** {model_info.get('feature_count', 0)}")
    
    with col2:
        st.write("**Performance Metrics:**")
        performance = model_info.get('performance', {})
        st.write(f"- **R² Score:** {performance.get('test_r2', 0):.3f}")
        st.write(f"- **MAE:** €{performance.get('test_mae', 0):.2f}")
        st.write(f"- **RMSE:** €{performance.get('test_rmse', 0):.2f}")
    
    # Training period
    training_period = model_info.get('training_period', {})
    if training_period:
        st.write("**Training Period:**")
        st.write(f"From {training_period.get('start_date', 'Unknown')} to {training_period.get('end_date', 'Unknown')}")
        st.write(f"Total days: {training_period.get('total_days', 'Unknown')}")
    
    # Features
    features = model_info.get('selected_features', [])
    if features:
        with st.expander(" Model Features"):
            # Display features in columns for better readability
            feature_cols = st.columns(3)
            for i, feature in enumerate(features):
                with feature_cols[i % 3]:
                    st.write(f"- {feature}")