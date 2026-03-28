"""
Sales Analytics Page
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from dashboard.utils.data_loader import (
    load_transaction_data, calculate_kpis, aggregate_daily_sales,
    get_product_sales, get_machine_performance, get_payment_distribution
)
from dashboard.utils.calculations import (
    get_period_comparison, calculate_seasonality_index,
    calculate_pareto_analysis, calculate_hourly_patterns
)
from dashboard.utils.time_aggregation import (
    aggregate_by_granularity, get_period_label, create_time_comparison
)
from dashboard.components.charts import (
    create_time_series_chart, create_bar_chart, create_pie_chart,
    create_heatmap, create_scatter_plot, create_dual_axis_chart
)
from dashboard.components.kpi_cards import create_kpi_row, create_info_card
from dashboard.components.filters import create_sidebar_filters, apply_filters, create_export_section
from dashboard.config import MACHINES, PRODUCT_CATEGORIES

# Page configuration
st.set_page_config(
    page_title="Sales Analytics - Vending Machine Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        padding-left: 20px;
        padding-right: 20px;
    }
</style>
""", unsafe_allow_html=True)


def main():
    st.title(" Sales Analytics Dashboard")
    
    # Load data
    with st.spinner("Loading transaction data..."):
        df = load_transaction_data(use_validated=True)
    
    if df.empty:
        st.error("No data available. Please check if the data files exist.")
        return
    
    # Sidebar filters
    filter_config = {
        'date': {'column': 'Date', 'default_days': None},  # Full range by default
        'machine': True,
        'category': True,
        'payment': True,
        'granularity': True,
        'day_of_week': True,
        'hour_range': True,
        'value_range': True
    }
    
    filters = create_sidebar_filters(df, filter_config)
    
    # Apply filters
    filtered_df = apply_filters(df, filters)
    
    # Calculate KPIs
    current_kpis = calculate_kpis(filtered_df)
    
    # Previous period for comparison
    if 'date_range' in filters and len(filters['date_range']) == 2:
        period_length = (filters['date_range'][1] - filters['date_range'][0]).days
        previous_start = filters['date_range'][0] - timedelta(days=period_length)
        previous_end = filters['date_range'][0] - timedelta(days=1)
        
        # Apply same filters to previous period
        previous_filters = filters.copy()
        previous_filters['date_range'] = (previous_start, previous_end)
        previous_df = apply_filters(df, previous_filters)
        previous_kpis = calculate_kpis(previous_df)
    else:
        previous_kpis = current_kpis
    
    # KPI Cards
    st.markdown("### Key Performance Indicators")
    
    kpi_configs = {
        'total_revenue': {'label': 'Total Revenue', 'value': current_kpis['total_revenue'], 'format': 'currency'},
        'total_transactions': {'label': 'Total Transactions', 'value': current_kpis['total_transactions'], 'format': 'integer'},
        'avg_transaction_value': {'label': 'Avg Transaction Value', 'value': current_kpis['avg_transaction_value'], 'format': 'currency'},
        'active_machines': {'label': 'Active Machines', 'value': current_kpis['active_machines'], 'format': 'integer'},
        'unique_products': {'label': 'Unique Products', 'value': current_kpis['unique_products'], 'format': 'integer'}
    }
    
    previous_kpi_configs = {
        'total_revenue': {'value': previous_kpis['total_revenue']},
        'total_transactions': {'value': previous_kpis['total_transactions']},
        'avg_transaction_value': {'value': previous_kpis['avg_transaction_value']},
        'active_machines': {'value': previous_kpis['active_machines']},
        'unique_products': {'value': previous_kpis['unique_products']}
    }
    
    create_kpi_row(kpi_configs, previous_kpi_configs)
    
    # Tabs for different analyses
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Time Series", "Products", "Machines", "Payments", "Advanced"])
    
    # Tab 1: Time Series Analysis
    with tab1:
        st.markdown("### Revenue Trend Analysis")
        
        # Get selected granularity
        granularity = filters.get('granularity', 'Daily')
        period_label = get_period_label(granularity)
        
        # Aggregate data based on selected granularity
        if granularity == 'Daily':
            time_series_data = aggregate_daily_sales(filtered_df)
            date_col = 'Date'
            value_col = 'Revenue'
        else:
            time_series_data = aggregate_by_granularity(
                filtered_df, granularity, 'Date', 'Value'
            )
            date_col = 'Date'
            value_col = 'Value'
            
            # If aggregation failed, fall back to daily
            if time_series_data.empty:
                st.warning(f"No data available for {granularity} aggregation. Showing daily data instead.")
                time_series_data = aggregate_daily_sales(filtered_df)
                date_col = 'Date'
                value_col = 'Revenue'
        
        if not time_series_data.empty:
            # Time series chart with appropriate title
            chart_title = f'{period_label}ly Revenue Trend'
            if granularity == 'Daily':
                chart_title += ' with Moving Averages'
            
            fig = create_time_series_chart(
                time_series_data, 
                date_col, 
                value_col,
                chart_title,
                show_ma=(granularity == 'Daily')  # Only show MA for daily data
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Period comparison and additional charts
            col1, col2 = st.columns(2)
            
            with col1:
                if granularity == 'Daily':
                    # Day of week analysis (only for daily granularity)
                    dow_revenue = filtered_df.groupby(filtered_df['Timestamp'].dt.day_name())['Value'].sum()
                    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    dow_revenue = dow_revenue.reindex(dow_order)
                    
                    fig_dow = create_bar_chart(
                        pd.DataFrame({'Day': dow_revenue.index, 'Revenue': dow_revenue.values}),
                        'Day', 'Revenue', 'Revenue by Day of Week'
                    )
                    st.plotly_chart(fig_dow, use_container_width=True)
                else:
                    # Period-over-period comparison for weekly/monthly
                    comparison_data = create_time_comparison(filtered_df, granularity, 'Date', 'Value')
                    if not comparison_data.empty and len(comparison_data) > 1:
                        recent_data = comparison_data.tail(10)  # Show last 10 periods
                        
                        fig_comparison = create_bar_chart(
                            recent_data,
                            'Date', 'ChangePercent', 
                            f'{period_label}-over-{period_label} Change (%)'
                        )
                        st.plotly_chart(fig_comparison, use_container_width=True)
            
            with col2:
                # Always show monthly trend for context
                monthly_revenue = filtered_df.groupby(filtered_df['Timestamp'].dt.to_period('M'))['Value'].sum()
                monthly_df = pd.DataFrame({
                    'Month': monthly_revenue.index.astype(str),
                    'Revenue': monthly_revenue.values
                })
                
                fig_monthly = create_bar_chart(
                    monthly_df, 'Month', 'Revenue', 'Monthly Revenue Overview'
                )
                st.plotly_chart(fig_monthly, use_container_width=True)
    
    # Tab 2: Product Analysis
    with tab2:
        st.markdown("### Product Performance Analysis")
        
        # Top products
        product_sales = get_product_sales(filtered_df, top_n=15)
        
        if not product_sales.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Sort products by revenue for better display
                top_products = product_sales.head(10).sort_values('Revenue', ascending=True)
                
                fig_products = create_bar_chart(
                    top_products,
                    'Revenue', 'Product', 'Top 10 Products by Revenue',
                    orientation='h',
                    height=500
                )
                st.plotly_chart(fig_products, use_container_width=True)
            
            with col2:
                # Category distribution
                category_sales = filtered_df.groupby('Super-Category')['Value'].sum().reset_index()
                fig_categories = create_pie_chart(
                    category_sales, 'Value', 'Super-Category',
                    'Revenue by Product Category'
                )
                st.plotly_chart(fig_categories, use_container_width=True)
            
            # Product details table
            st.markdown("### Product Details")
            product_table = product_sales[['Product', 'Revenue', 'Quantity', 'Transactions', 'AvgPrice']]
            product_table['Revenue'] = product_table['Revenue'].map('€{:,.2f}'.format)
            product_table['AvgPrice'] = product_table['AvgPrice'].map('€{:,.2f}'.format)
            st.dataframe(product_table, use_container_width=True)
            
            # Pareto analysis
            pareto_df = calculate_pareto_analysis(product_sales, 'Product', 'Revenue')
            create_info_card(
                "Pareto Analysis",
                f"{len(pareto_df[pareto_df['ABC_Class'] == 'A'])} products (Class A) generate 80% of revenue",
                "",
                "info"
            )
    
    # Tab 3: Machine Analysis
    with tab3:
        st.markdown("### Machine Performance Analysis")
        
        machine_perf = get_machine_performance(filtered_df)
        
        if not machine_perf.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig_machine_revenue = create_bar_chart(
                    machine_perf, 'Machine', 'TotalRevenue',
                    'Total Revenue by Machine'
                )
                st.plotly_chart(fig_machine_revenue, use_container_width=True)
            
            with col2:
                fig_machine_util = create_bar_chart(
                    machine_perf, 'Machine', 'UtilizationRate',
                    'Machine Utilization Rate'
                )
                st.plotly_chart(fig_machine_util, use_container_width=True)
            
            # Machine comparison metrics
            st.markdown("### Machine Comparison")
            for _, machine in machine_perf.iterrows():
                with st.expander(f"📍 {machine['Machine']}"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    col1.metric("Total Revenue", f"€{machine['TotalRevenue']:,.2f}")
                    col2.metric("Transactions", f"{machine['Transactions']:,}")
                    col3.metric("Daily Avg Revenue", f"€{machine['DailyAvgRevenue']:,.2f}")
                    col4.metric("Utilization", f"{machine['UtilizationRate']*100:.1f}%")
    
    # Tab 4: Payment Analysis
    with tab4:
        st.markdown("### Payment Method Analysis")
        
        payment_dist = get_payment_distribution(filtered_df)
        
        if not payment_dist.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig_payment = create_pie_chart(
                    payment_dist, 'Revenue', 'PaymentMethod',
                    'Revenue by Payment Method'
                )
                st.plotly_chart(fig_payment, use_container_width=True)
            
            with col2:
                # Payment trend over time
                payment_trend = filtered_df.groupby([
                    filtered_df['Timestamp'].dt.to_period('M'), 
                    'Super-Payment'
                ])['Value'].sum().reset_index()
                payment_trend['Month'] = payment_trend['Timestamp'].astype(str)
                
                fig_payment_trend = px.line(
                    payment_trend, x='Month', y='Value', color='Super-Payment',
                    title='Payment Method Trend Over Time'
                )
                st.plotly_chart(fig_payment_trend, use_container_width=True)
    
    # Tab 5: Advanced Analytics
    with tab5:
        st.markdown("### Advanced Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Hourly patterns heatmap
            hourly_patterns = calculate_hourly_patterns(filtered_df)
            if not hourly_patterns.empty:
                fig_heatmap = create_heatmap(
                    hourly_patterns,
                    'Sales Patterns by Hour and Day'
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
        
        with col2:
            # Holiday impact
            holiday_sales = filtered_df.groupby('IsHoliday')['Value'].agg(['sum', 'mean', 'count']).reset_index()
            holiday_sales['IsHoliday'] = holiday_sales['IsHoliday'].map({True: 'Holiday', False: 'Regular Day'})
            
            fig_holiday = create_bar_chart(
                holiday_sales, 'IsHoliday', 'mean',
                'Average Daily Revenue: Holiday vs Regular Days'
            )
            st.plotly_chart(fig_holiday, use_container_width=True)
        
        # Seasonality analysis - always use daily aggregation for seasonality
        daily_sales_for_seasonality = aggregate_daily_sales(filtered_df)
        seasonality = calculate_seasonality_index(daily_sales_for_seasonality)
        if seasonality:
            st.markdown("### Seasonality Indices")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'day_of_week' in seasonality:
                    dow_seasonality = pd.DataFrame(
                        list(seasonality['day_of_week'].items()),
                        columns=['DayOfWeek', 'Index']
                    )
                    dow_seasonality['Day'] = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                    
                    fig_dow_season = create_bar_chart(
                        dow_seasonality, 'Day', 'Index',
                        'Day of Week Seasonality Index (100 = Average)'
                    )
                    st.plotly_chart(fig_dow_season, use_container_width=True)
            
            with col2:
                if 'month' in seasonality:
                    month_seasonality = pd.DataFrame(
                        list(seasonality['month'].items()),
                        columns=['Month', 'Index']
                    )
                    month_seasonality['MonthName'] = pd.to_datetime(
                        month_seasonality['Month'], format='%m'
                    ).dt.strftime('%B')
                    
                    fig_month_season = create_bar_chart(
                        month_seasonality, 'MonthName', 'Index',
                        'Monthly Seasonality Index (100 = Average)'
                    )
                    st.plotly_chart(fig_month_season, use_container_width=True)
    
    # Export Section
    st.markdown("---")
    create_export_section(filtered_df, "sales_analytics")


if __name__ == "__main__":
    main()