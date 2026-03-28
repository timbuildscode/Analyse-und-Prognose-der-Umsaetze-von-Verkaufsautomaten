import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from dashboard.utils.data_loader import load_transaction_data, calculate_kpis
from dashboard.utils.model_utils import get_available_models, get_model_artifacts_summary

# Page configuration
st.set_page_config(
    page_title="Vending Machine Sales Dashboard",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main page styling */
    .main {
        padding-top: 2rem;
    }
    
    /* Metric cards styling */
    div[data-testid="metric-container"] {
        background-color: #f0f2f6;
        border: 1px solid #e0e2e6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Header styling */
    h1 {
        color: #1f2937;
        font-weight: 700;
        margin-bottom: 2rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        padding-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# Main App
def main():
    # Header
    col1, col2 = st.columns([8, 2])
    with col1:
        st.title("🏪 Vending Machine Sales Dashboard")
    with col2:
        st.write(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Load actual data for KPIs
    with st.spinner("Loading dashboard data..."):
        df = load_transaction_data(use_validated=True)
        available_models = get_available_models()
        artifacts_summary = get_model_artifacts_summary()
    
    # Calculate actual KPIs
    if not df.empty:
        kpis = calculate_kpis(df)
        
        # Get data insights
        date_range = df['Date'].agg(['min', 'max'])
        unique_machines = df['Machine'].nunique()
        unique_categories = df['Super-Category'].dropna().nunique()
        unique_products = df['Product'].nunique()
        total_days = (date_range['max'] - date_range['min']).days
        total_years = round(total_days / 365.25, 1)
        
        # Quick stats preview
        st.markdown("###  Quick Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Active Machines",
                value=f"{unique_machines}",
                delta="Locations",
                delta_color="normal"
            )
        
        with col2:
            st.metric(
                label="Total Revenue",
                value=f"€{kpis['total_revenue']:,.0f}",
                delta=f"{total_years} years data"
            )
        
        with col3:
            st.metric(
                label="Total Products",
                value=f"{unique_products:,}",
                delta=f"{unique_categories} categories"
            )
        
        with col4:
            st.metric(
                label="Transactions",
                value=f"{kpis['total_transactions']:,}",
                delta=f"€{kpis['avg_transaction_value']:.2f} avg"
            )
    else:
        # Fallback if no data
        st.warning("No data available. Please check data files.")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(label="Active Machines", value="0", delta="No data")
        with col2:
            st.metric(label="Total Revenue", value="€0", delta="No data")
        with col3:
            st.metric(label="Total Products", value="0", delta="No data")
        with col4:
            st.metric(label="Transactions", value="0", delta="No data")
    
    st.markdown("---")

    # Data Quality Summary
    st.markdown("###  Data Quality Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not df.empty:
            # Dynamic data coverage
            category_names = df['Super-Category'].dropna().unique()
            payment_methods = df['Super-Payment'].dropna().unique()
            
            st.info(f"""
            ** Data Coverage**
            - Period: {date_range['min'].strftime('%B %Y')} - {date_range['max'].strftime('%B %Y')}
            - Machines: {unique_machines} active locations
            - Categories: {', '.join(category_names)}
            - Payment Methods: {', '.join(payment_methods)}
            """)
        else:
            st.info("""
            ** Data Coverage**
            - No data available
            - Please check data files
            """)
    
    with col2:
        # Dynamic model status with comprehensive artifacts
        if artifacts_summary['total_models'] > 0:
            # Get latest model performance if available
            latest_model = available_models[0] if available_models else None
            
            if latest_model:
                perf = latest_model.get('performance', {})
                r2 = perf.get('test_r2', 0)
                mae = perf.get('test_mae', 0)
                performance_info = f"Latest model R²: {r2:.3f} (MAE: {mae:.1f})"
            else:
                performance_info = "Model performance metrics available"
            
            # Build artifact type summary
            artifact_types = artifacts_summary.get('artifact_types', {})
            artifact_info = []
            for artifact_type, count in artifact_types.items():
                artifact_info.append(f"{count} {artifact_type}")
            
            st.success(f"""
            ** Model Status**
            - {artifacts_summary['total_models']} trained models available
            - {performance_info}
            - Total artifacts: {artifacts_summary['total_artifacts']}
            - Components: {', '.join(artifact_info[:3])}{'...' if len(artifact_info) > 3 else ''}
            - Predictions: Up to 30-day forecasts
            """)
        else:
            st.warning("""
            ** Model Status**
            - No trained models found
            - Please train models first
            """)

    st.markdown("---")
    
    # Welcome message
    st.markdown("""
    ## Welcome to the Vending Machine Analytics Platform
    
    This dashboard provides comprehensive insights into vending machine sales data and model performance tracking.
    
    ###  Available Sections:
    
    ####  Sales Analytics
    - **KPIs & Metrics**: Real-time revenue, transactions, and performance indicators
    - **Time Series**: Daily, weekly, and monthly revenue trends with moving averages
    - **Product Analysis**: Top products, category breakdown, and Pareto analysis
    - **Machine Performance**: Utilization rates and revenue by machine
    - **Payment Insights**: Cash vs card distribution and trends
    - **Advanced Analytics**: Seasonality patterns, hourly heatmaps, and holiday impact
    
    ####  Model Performance
    - **Predictions**: 1-30 day sales forecasts with confidence intervals
    - **Model Metrics**: MAE, RMSE, R² scores with visual gauges
    - **Feature Analysis**: Importance rankings and category breakdowns
    - **Model Comparison**: Side-by-side performance evaluation
    - **Diagnostics**: Hyperparameters and monitoring insights
    
    ###  Getting Started:
    
    1. **Navigate** using the page selector in the sidebar
    2. **Filter** data using interactive controls on each page
    3. **Export** results as CSV, Excel, or summary reports
    4. **Explore** different time periods and product categories
    
    ###  Key Features:
    
    - **Interactive Filtering**: Date ranges, machines, categories, payment methods
    - **Real-time Caching**: Fast data loading with automatic refresh
    - **Export Options**: Download data and reports in multiple formats
    - **Responsive Design**: Optimized for analytics workflows
    - **Error Handling**: Graceful handling of missing data
    """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>🏗️ Built with Streamlit | 🐍 Python + Pandas |  XGBoost |  Plotly</p>
            <p><small>Data Processing Pipeline: Automated ETL with standardization and validation</small></p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()