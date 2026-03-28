"""
Calculation utilities for metrics and statistics
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats


def calculate_growth_rate(current, previous):
    """Calculate growth rate percentage"""
    if previous == 0:
        return 0 if current == 0 else 100
    return ((current - previous) / previous) * 100


def calculate_trend(series, window=7):
    """Calculate trend using linear regression"""
    if len(series) < window:
        return 0
    
    recent_data = series.tail(window)
    x = np.arange(len(recent_data))
    
    # Handle NaN values
    mask = ~np.isnan(recent_data.values)
    if mask.sum() < 2:
        return 0
    
    slope, _, _, _, _ = stats.linregress(x[mask], recent_data.values[mask])
    return slope


def calculate_seasonality_index(df, column='Revenue', date_column='Date'):
    """Calculate seasonality indices for different time periods"""
    if df.empty:
        return {}
    
    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column])
    
    # Day of week seasonality
    dow_seasonality = df.groupby(df[date_column].dt.dayofweek)[column].mean()
    dow_seasonality = (dow_seasonality / dow_seasonality.mean() * 100).to_dict()
    
    # Month seasonality
    month_seasonality = df.groupby(df[date_column].dt.month)[column].mean()
    month_seasonality = (month_seasonality / month_seasonality.mean() * 100).to_dict()
    
    return {
        'day_of_week': dow_seasonality,
        'month': month_seasonality
    }


def detect_anomalies(series, threshold=3):
    """Detect anomalies using z-score method"""
    if len(series) < 10:
        return pd.Series([False] * len(series), index=series.index)
    
    z_scores = np.abs(stats.zscore(series.fillna(series.mean())))
    return z_scores > threshold


def calculate_forecast_accuracy(actual, predicted):
    """Calculate various forecast accuracy metrics"""
    if len(actual) == 0 or len(predicted) == 0:
        return {
            'mae': np.nan,
            'rmse': np.nan,
            'mape': np.nan,
            'r2': np.nan
        }
    
    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    
    # MAPE (avoiding division by zero)
    mask = actual != 0
    if mask.sum() > 0:
        mape = np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100
    else:
        mape = np.nan
    
    # R-squared
    if len(actual) > 1 and actual.std() > 0:
        r2 = 1 - (np.sum((actual - predicted) ** 2) / np.sum((actual - actual.mean()) ** 2))
    else:
        r2 = np.nan
    
    return {
        'mae': mae,
        'rmse': rmse,
        'mape': mape,
        'r2': r2
    }


def calculate_revenue_volatility(series, window=30):
    """Calculate revenue volatility using rolling standard deviation"""
    if len(series) < window:
        return pd.Series([np.nan] * len(series), index=series.index)
    
    return series.rolling(window=window, min_periods=1).std()


def get_period_comparison(df, date_column='Date', value_column='Revenue', period='month'):
    """Compare current period with previous period"""
    if df.empty:
        return {
            'current': 0,
            'previous': 0,
            'change': 0,
            'change_pct': 0
        }
    
    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column])
    
    # Get current date
    latest_date = df[date_column].max()
    
    if period == 'day':
        current_start = latest_date
        previous_start = latest_date - timedelta(days=1)
        previous_end = previous_start
    elif period == 'week':
        current_start = latest_date - timedelta(days=6)
        previous_start = current_start - timedelta(days=7)
        previous_end = latest_date - timedelta(days=7)
    elif period == 'month':
        current_start = latest_date - timedelta(days=29)
        previous_start = current_start - timedelta(days=30)
        previous_end = latest_date - timedelta(days=30)
    else:  # year
        current_start = latest_date - timedelta(days=364)
        previous_start = current_start - timedelta(days=365)
        previous_end = latest_date - timedelta(days=365)
    
    # Calculate values
    current_mask = (df[date_column] >= current_start) & (df[date_column] <= latest_date)
    previous_mask = (df[date_column] >= previous_start) & (df[date_column] <= previous_end)
    
    current_value = df.loc[current_mask, value_column].sum()
    previous_value = df.loc[previous_mask, value_column].sum()
    
    change = current_value - previous_value
    change_pct = calculate_growth_rate(current_value, previous_value)
    
    return {
        'current': current_value,
        'previous': previous_value,
        'change': change,
        'change_pct': change_pct
    }


def calculate_pareto_analysis(df, category_column='Product', value_column='Revenue'):
    """Perform Pareto analysis (80/20 rule)"""
    if df.empty:
        return pd.DataFrame()
    
    # Sort by value
    sorted_df = df.sort_values(value_column, ascending=False).copy()
    
    # Calculate cumulative percentage
    sorted_df['Cumulative_Value'] = sorted_df[value_column].cumsum()
    sorted_df['Cumulative_Percentage'] = (sorted_df['Cumulative_Value'] / sorted_df[value_column].sum() * 100)
    
    # Classify items
    sorted_df['ABC_Class'] = pd.cut(
        sorted_df['Cumulative_Percentage'],
        bins=[0, 80, 95, 100],
        labels=['A', 'B', 'C']
    )
    
    return sorted_df


def calculate_hourly_patterns(df, date_column='Timestamp', value_column='Value'):
    """Calculate hourly sales patterns"""
    if df.empty or date_column not in df.columns:
        return pd.DataFrame()
    
    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column])
    df['Hour'] = df[date_column].dt.hour
    df['DayOfWeek'] = df[date_column].dt.dayofweek
    
    # Hourly average by day of week
    hourly_pattern = df.groupby(['DayOfWeek', 'Hour'])[value_column].mean().reset_index()
    
    # Pivot for heatmap
    hourly_heatmap = hourly_pattern.pivot(index='Hour', columns='DayOfWeek', values=value_column)
    hourly_heatmap.columns = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    return hourly_heatmap