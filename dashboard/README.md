# Vending Machine Sales Dashboard

A comprehensive analytics dashboard for vending machine sales data with machine learning model performance tracking.

## Features

###  Sales Analytics
- Real-time KPIs (revenue, transactions, average values)
- Time series analysis with moving averages
- Product performance metrics and rankings
- Machine utilization and performance comparison
- Payment method distribution
- Advanced analytics (seasonality, hourly patterns, holiday impact)

###  Model Performance
- Model selection and comparison
- Performance metrics (MAE, RMSE, R²)
- Sales predictions with confidence intervals
- Feature importance analysis
- Model diagnostics and hyperparameters

###  Interactive Features
- Date range selection
- Machine and product category filters
- Payment method filtering
- Advanced filters (day of week, hour range, value range)
- Export functionality (CSV, Excel, reports)

## Running the Dashboard

### Local Development

```bash
# From project root
./run_dashboard.sh

# Or manually with uv
uv run streamlit run dashboard/Home.py

# Or with regular pip/python
streamlit run dashboard/Home.py
```

The dashboard will open in your default web browser at `http://localhost:8501`

### Streamlit Cloud Deployment

1. **Push to GitHub**: Ensure your repository is pushed to GitHub
2. **Deploy**: Go to [share.streamlit.io](https://share.streamlit.io) and connect your repository
3. **Main file**: Set main file path as `dashboard/Home.py`
4. **Dependencies**: The project uses `requirements.txt` for Streamlit Cloud (optimized for dashboard only)

**Note**: The `requirements.txt` contains only dashboard dependencies to avoid TensorFlow installation issues on Streamlit Cloud. For full local development, use `pyproject.toml` with `uv`.

## File Structure

```
dashboard/
├── app.py                    # Main dashboard entry point
├── config.py                 # Configuration settings
├── pages/
│   ├── 01_Sales_Analytics.py    # Sales analysis page
│   └── 02_Model_Performance.py  # Model performance page
├── components/
│   ├── charts.py            # Reusable chart components
│   ├── kpi_cards.py        # KPI display components
│   └── filters.py          # Filter components
└── utils/
    ├── data_loader.py      # Data loading with caching
    ├── calculations.py     # Metric calculations
    └── model_utils.py      # Model loading and predictions
```

## Navigation

1. **Home Page**: Overview and quick stats
2. **Sales Analytics**: Comprehensive sales analysis with multiple tabs
   - Time Series: Revenue trends and patterns
   - Products: Product performance and Pareto analysis
   - Machines: Machine-wise performance metrics
   - Payments: Payment method analysis
   - Advanced: Seasonality and pattern detection
3. **Model Performance**: ML model insights
   - Predictions: Future sales forecasts
   - Feature Analysis: Important features
   - Model Comparison: Compare multiple models
   - Diagnostics: Model details and monitoring

## Data Requirements

The dashboard expects:
- Processed data in `data/processed/daily_sales_features.csv`
- Transaction data in `data/interim/all_standardized_validated.xlsx`
- Trained models in `models/` directory

## Customization

Edit `config.py` to modify:
- Chart themes and colors
- KPI thresholds
- Cache settings
- Default values