"""
Dashboard Configuration Settings
"""
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Data paths
RAW_DATA_PATH = DATA_DIR / "raw"
INTERIM_DATA_PATH = DATA_DIR / "interim"
PROCESSED_DATA_PATH = DATA_DIR / "processed"

# File paths
DAILY_SALES_FILE = PROCESSED_DATA_PATH / "daily_sales_features.csv"
COMBINED_DATA_FILE = INTERIM_DATA_PATH / "all_standardized_combined.xlsx"
VALIDATED_DATA_FILE = INTERIM_DATA_PATH / "all_standardized_validated.xlsx"

# Cache settings
CACHE_TTL = 3600  # 1 hour cache for data
MODEL_CACHE_TTL = 86400  # 24 hour cache for models

# Visualization settings
PLOT_HEIGHT = 400
PLOT_WIDTH = 800
COLOR_PALETTE = {
    'primary': '#1f77b4',
    'secondary': '#ff7f0e',
    'success': '#2ca02c',
    'danger': '#d62728',
    'warning': '#ff9800',
    'info': '#17a2b8',
    'light': '#f8f9fa',
    'dark': '#343a40'
}

# Chart themes
PLOTLY_THEME = 'plotly_white'
CHART_FONT = 'Arial, sans-serif'

# Date formats
DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DISPLAY_DATE_FORMAT = '%d.%m.%Y'

# Machine names
MACHINES = ['Kleine Dammstraße', 'Harzblick']

# Product categories
PRODUCT_CATEGORIES = ['Getränke', 'Essen & Snacks', 'Vapes']

# Payment types
PAYMENT_TYPES = ['cash', 'card']

# Model settings
MODEL_FEATURES = [
    'DayOfWeek', 'Month', 'Quarter', 'IsWeekend', 'IsMonthStart', 'IsMonthEnd',
    'DayOfWeek_sin', 'DayOfWeek_cos', 'Month_sin', 'Month_cos',
    'DayOfYear_sin', 'DayOfYear_cos', 'Revenue_Lag_1', 'Revenue_Lag_2',
    'Revenue_Lag_3', 'Revenue_Lag_7', 'Revenue_Lag_14', 'Revenue_Lag_30',
    'Revenue_MA_7', 'Revenue_MA_30', 'Revenue_Volatility_7', 'Revenue_Volatility_30'
]

# API settings
API_BASE_URL = "http://localhost:8000"
API_ENDPOINTS = {
    'predict': '/predict',
    'batch_predict': '/predict/batch',
    'raw_predict': '/predict/raw',
    'model_info': '/model/info',
    'health': '/health'
}
API_TIMEOUT = 30  # seconds

# KPI thresholds
KPI_THRESHOLDS = {
    'daily_revenue_good': 100,
    'daily_revenue_warning': 50,
    'daily_transactions_good': 20,
    'daily_transactions_warning': 10,
    'model_r2_good': 0.7,
    'model_r2_warning': 0.5,
    'model_mae_good': 50,
    'model_mae_warning': 100
}