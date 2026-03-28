"""
Data Loading and Caching Module
"""
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from dashboard.config import (
    DAILY_SALES_FILE, COMBINED_DATA_FILE, VALIDATED_DATA_FILE,
    CACHE_TTL, DATE_FORMAT, DATETIME_FORMAT
)
from scripts.data_processing.CONSTANTS import (
    TARGET_COLUMNS, SUPER_CATEGORY_MAP, SUPER_PAYMENT_MAP,
    MACHINE_MAPPING, FEIERTAGE, SCHULFERIEN, VORLESUNGSZEITEN
)


@st.cache_data(ttl=CACHE_TTL)
def load_daily_sales_data():
    """Load and cache daily sales features data"""
    try:
        df = pd.read_csv(DAILY_SALES_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Fill missing values for specific columns
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error loading daily sales data: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL)
def load_transaction_data(use_validated=True):
    """Load and cache transaction-level data"""
    try:
        file_path = VALIDATED_DATA_FILE if use_validated else COMBINED_DATA_FILE
        
        if not file_path.exists():
            st.warning(f"File not found: {file_path}")
            return pd.DataFrame()
        
        df = pd.read_excel(file_path)
        
        # Ensure all required columns exist
        for col in TARGET_COLUMNS:
            if col not in df.columns:
                df[col] = None
        
        # Convert timestamp
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
        # Standardize machine names
        df['Machine'] = df['Machine'].map(lambda x: MACHINE_MAPPING.get(x, x))
        
        # Add derived columns
        df['Date'] = df['Timestamp'].dt.date
        df['Hour'] = df['Timestamp'].dt.hour
        df['DayOfWeek'] = df['Timestamp'].dt.dayofweek
        df['Month'] = df['Timestamp'].dt.month
        df['Year'] = df['Timestamp'].dt.year
        
        # Add holiday/vacation flags
        df['IsHoliday'] = df['Date'].astype(str).isin(
            [datetime.strptime(d, '%d.%m.%Y').strftime('%Y-%m-%d') for d in FEIERTAGE]
        )
        
        # Add school vacation flag
        df['IsSchoolVacation'] = False
        for start, end in SCHULFERIEN:
            start_date = datetime.strptime(start, '%d.%m.%Y')
            end_date = datetime.strptime(end, '%d.%m.%Y')
            mask = (df['Timestamp'] >= start_date) & (df['Timestamp'] <= end_date)
            df.loc[mask, 'IsSchoolVacation'] = True
        
        # Add university lecture period flag
        df['IsLecturePeriod'] = False
        for start, end in VORLESUNGSZEITEN:
            start_date = datetime.strptime(start, '%d.%m.%Y')
            end_date = datetime.strptime(end, '%d.%m.%Y')
            mask = (df['Timestamp'] >= start_date) & (df['Timestamp'] <= end_date)
            df.loc[mask, 'IsLecturePeriod'] = True
        
        return df
    except Exception as e:
        st.error(f"Error loading transaction data: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL)
def get_date_range(df):
    """Get min and max dates from dataframe"""
    if 'Timestamp' in df.columns:
        return df['Timestamp'].min(), df['Timestamp'].max()
    elif 'Date' in df.columns:
        return df['Date'].min(), df['Date'].max()
    else:
        return None, None


@st.cache_data(ttl=CACHE_TTL)
def calculate_kpis(df, start_date=None, end_date=None):
    """Calculate key performance indicators"""
    if df.empty:
        return {
            'total_revenue': 0,
            'total_transactions': 0,
            'total_products': 0,
            'avg_transaction_value': 0,
            'active_machines': 0,
            'unique_products': 0
        }
    
    # Filter by date range if provided
    if start_date or end_date:
        if 'Timestamp' in df.columns:
            date_col = 'Timestamp'
        elif 'Date' in df.columns:
            date_col = 'Date'
        else:
            date_col = None
        
        if date_col:
            if start_date:
                df = df[df[date_col] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df[date_col] <= pd.to_datetime(end_date)]
    
    kpis = {
        'total_revenue': df['Value'].sum() if 'Value' in df.columns else 0,
        'total_transactions': len(df),
        'total_products': df['Quantity'].sum() if 'Quantity' in df.columns else len(df),
        'avg_transaction_value': df['Value'].mean() if 'Value' in df.columns else 0,
        'active_machines': df['Machine'].nunique() if 'Machine' in df.columns else 0,
        'unique_products': df['Product'].nunique() if 'Product' in df.columns else 0
    }
    
    return kpis


@st.cache_data(ttl=CACHE_TTL)
def aggregate_daily_sales(df):
    """Aggregate transaction data to daily level"""
    if df.empty or 'Date' not in df.columns:
        return pd.DataFrame()
    
    daily_agg = df.groupby('Date').agg({
        'Value': 'sum',
        'Quantity': 'sum',
        'Machine': 'nunique',
        'Product': 'nunique',
        'Timestamp': 'count'
    }).reset_index()
    
    daily_agg.columns = ['Date', 'Revenue', 'Quantity', 'ActiveMachines', 'UniqueProducts', 'Transactions']
    
    # Add moving averages
    daily_agg['Revenue_MA7'] = daily_agg['Revenue'].rolling(window=7, min_periods=1).mean()
    daily_agg['Revenue_MA30'] = daily_agg['Revenue'].rolling(window=30, min_periods=1).mean()
    
    return daily_agg


@st.cache_data(ttl=CACHE_TTL)
def get_product_sales(df, top_n=10):
    """Get product sales summary"""
    if df.empty or 'Product' not in df.columns:
        return pd.DataFrame()
    
    product_sales = df.groupby('Product').agg({
        'Value': 'sum',
        'Quantity': 'sum',
        'Timestamp': 'count'
    }).reset_index()
    
    product_sales.columns = ['Product', 'Revenue', 'Quantity', 'Transactions']
    
    # Calculate average price, handling division by zero
    product_sales['AvgPrice'] = np.where(
        product_sales['Quantity'] > 0,
        product_sales['Revenue'] / product_sales['Quantity'],
        np.nan
    )
    
    # Add category
    product_sales['Category'] = df.groupby('Product')['Category'].first().values
    product_sales['SuperCategory'] = df.groupby('Product')['Super-Category'].first().values
    
    return product_sales.sort_values('Revenue', ascending=False).head(top_n)


@st.cache_data(ttl=CACHE_TTL)
def get_machine_performance(df):
    """Get machine performance metrics"""
    if df.empty or 'Machine' not in df.columns:
        return pd.DataFrame()
    
    machine_perf = df.groupby('Machine').agg({
        'Value': ['sum', 'mean', 'count'],
        'Quantity': 'sum',
        'Date': lambda x: (x.max() - x.min()).days + 1 if len(x) > 0 else 0
    }).reset_index()
    
    machine_perf.columns = ['Machine', 'TotalRevenue', 'AvgTransactionValue', 
                           'Transactions', 'TotalQuantity', 'ActiveDays']
    
    # Safe division to avoid division by zero
    machine_perf['DailyAvgRevenue'] = np.where(
        machine_perf['ActiveDays'] > 0,
        machine_perf['TotalRevenue'] / machine_perf['ActiveDays'],
        0
    )
    
    total_unique_dates = df['Date'].nunique()
    machine_perf['UtilizationRate'] = np.where(
        total_unique_dates > 0,
        machine_perf['ActiveDays'] / total_unique_dates,
        0
    )
    
    return machine_perf


@st.cache_data(ttl=CACHE_TTL)
def get_payment_distribution(df):
    """Get payment method distribution"""
    if df.empty or 'Super-Payment' not in df.columns:
        return pd.DataFrame()
    
    payment_dist = df.groupby('Super-Payment').agg({
        'Value': 'sum',
        'Timestamp': 'count'
    }).reset_index()
    
    payment_dist.columns = ['PaymentMethod', 'Revenue', 'Transactions']
    
    # Safe percentage calculation
    total_revenue = payment_dist['Revenue'].sum()
    payment_dist['Percentage'] = np.where(
        total_revenue > 0,
        (payment_dist['Revenue'] / total_revenue * 100).round(2),
        0
    )
    
    return payment_dist