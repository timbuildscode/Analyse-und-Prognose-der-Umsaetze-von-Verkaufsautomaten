"""
Reusable filter components for the dashboard
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


def create_date_filter(df, date_column='Date', default_days=None, key_prefix=""):
    """Create date range filter"""
    min_date = df[date_column].min()
    max_date = df[date_column].max()
    
    # Default to full range if default_days is None
    if default_days is None:
        default_start = min_date
    else:
        default_start = max_date - timedelta(days=default_days)
        if default_start < min_date:
            default_start = min_date
    
    date_range = st.date_input(
        "Select Date Range",
        value=(default_start, max_date),
        min_value=min_date,
        max_value=max_date,
        key=f"{key_prefix}_date_range"
    )
    
    # Handle single date selection
    if isinstance(date_range, tuple) and len(date_range) == 2:
        return date_range
    else:
        return (date_range, date_range)


def create_multiselect_filter(df, column, label, default_all=True, key_prefix=""):
    """Create multiselect filter"""
    unique_values = df[column].dropna().unique().tolist()
    
    if default_all:
        default_values = unique_values
    else:
        default_values = []
    
    selected = st.multiselect(
        label,
        options=unique_values,
        default=default_values,
        key=f"{key_prefix}_{column}"
    )
    
    return selected


def create_sidebar_filters(df, filter_config):
    """Create comprehensive sidebar filters"""
    filters = {}
    
    st.sidebar.header("Filters")
    
    # Date filter
    if 'date' in filter_config:
        date_config = filter_config['date']
        filters['date_range'] = create_date_filter(
            df,
            date_column=date_config.get('column', 'Date'),
            default_days=date_config.get('default_days', 30),
            key_prefix="sidebar"
        )
    
    # Machine filter
    if 'machine' in filter_config:
        filters['machines'] = create_multiselect_filter(
            df,
            'Machine',
            "Select Machines",
            default_all=True,
            key_prefix="sidebar"
        )
    
    # Category filter
    if 'category' in filter_config:
        filters['categories'] = create_multiselect_filter(
            df,
            'Super-Category',
            "Select Product Categories",
            default_all=True,
            key_prefix="sidebar"
        )
    
    # Payment filter
    if 'payment' in filter_config:
        filters['payments'] = create_multiselect_filter(
            df,
            'Super-Payment',
            "Select Payment Methods",
            default_all=True,
            key_prefix="sidebar"
        )
    
    # Time granularity
    if 'granularity' in filter_config:
        filters['granularity'] = st.sidebar.selectbox(
            "Time Granularity",
            options=['Daily', 'Weekly', 'Monthly'],
            index=0,
            key="sidebar_granularity"
        )
    
    # Advanced filters in expander
    with st.sidebar.expander("Advanced Filters"):
        # Day of week filter
        if 'day_of_week' in filter_config:
            dow_options = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            filters['day_of_week'] = st.multiselect(
                "Day of Week",
                options=dow_options,
                default=dow_options,
                key="sidebar_dow"
            )
        
        # Hour range filter
        if 'hour_range' in filter_config:
            filters['hour_range'] = st.slider(
                "Hour Range",
                min_value=0,
                max_value=23,
                value=(0, 23),
                key="sidebar_hour"
            )
        
        # Value range filter
        if 'value_range' in filter_config:
            min_val = df['Value'].min()
            max_val = df['Value'].max()
            
            filters['value_range'] = st.slider(
                "Transaction Value Range (€)",
                min_value=float(min_val),
                max_value=float(max_val),
                value=(float(min_val), float(max_val)),
                key="sidebar_value"
            )
    
    return filters


def apply_filters(df, filters):
    """Apply filters to dataframe"""
    filtered_df = df.copy()
    
    # Date filter
    if 'date_range' in filters and len(filters['date_range']) == 2:
        date_column = 'Date' if 'Date' in df.columns else 'Timestamp'
        filtered_df = filtered_df[
            (pd.to_datetime(filtered_df[date_column]).dt.date >= filters['date_range'][0]) &
            (pd.to_datetime(filtered_df[date_column]).dt.date <= filters['date_range'][1])
        ]
    
    # Machine filter
    if 'machines' in filters and filters['machines']:
        filtered_df = filtered_df[filtered_df['Machine'].isin(filters['machines'])]
    
    # Category filter
    if 'categories' in filters and filters['categories']:
        filtered_df = filtered_df[filtered_df['Super-Category'].isin(filters['categories'])]
    
    # Payment filter
    if 'payments' in filters and filters['payments']:
        filtered_df = filtered_df[filtered_df['Super-Payment'].isin(filters['payments'])]
    
    # Day of week filter
    if 'day_of_week' in filters and filters['day_of_week']:
        dow_map = {
            'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
            'Friday': 4, 'Saturday': 5, 'Sunday': 6
        }
        selected_dow = [dow_map[d] for d in filters['day_of_week']]
        
        if 'Timestamp' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Timestamp'].dt.dayofweek.isin(selected_dow)]
        elif 'DayOfWeek' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['DayOfWeek'].isin(selected_dow)]
    
    # Hour range filter
    if 'hour_range' in filters and 'Timestamp' in filtered_df.columns:
        hour_min, hour_max = filters['hour_range']
        filtered_df = filtered_df[
            (filtered_df['Timestamp'].dt.hour >= hour_min) &
            (filtered_df['Timestamp'].dt.hour <= hour_max)
        ]
    
    # Value range filter
    if 'value_range' in filters and 'Value' in filtered_df.columns:
        val_min, val_max = filters['value_range']
        filtered_df = filtered_df[
            (filtered_df['Value'] >= val_min) &
            (filtered_df['Value'] <= val_max)
        ]
    
    return filtered_df


def create_export_section(df, filename_prefix="export"):
    """Create export functionality section"""
    st.markdown("### Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(" Export to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button(" Export to Excel"):
            # Create Excel file in memory
            import io
            buffer = io.BytesIO()
            
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
            
            st.download_button(
                label="Download Excel",
                data=buffer.getvalue(),
                file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col3:
        # Summary statistics
        if st.button(" Generate Report"):
            report = generate_summary_report(df)
            st.download_button(
                label="Download Report",
                data=report,
                file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )


def generate_summary_report(df):
    """Generate summary report from filtered data"""
    report = f"""
Sales Analysis Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== Data Summary ===
Total Records: {len(df):,}
Date Range: {df['Date'].min()} to {df['Date'].max()} if 'Date' in df.columns else 'N/A'

=== Revenue Summary ===
Total Revenue: €{df['Value'].sum():,.2f} if 'Value' in df.columns else 'N/A'
Average Transaction: €{df['Value'].mean():,.2f} if 'Value' in df.columns else 'N/A'
Median Transaction: €{df['Value'].median():,.2f} if 'Value' in df.columns else 'N/A'

=== Machine Summary ===
Active Machines: {df['Machine'].nunique() if 'Machine' in df.columns else 'N/A'}
Top Machine: {df.groupby('Machine')['Value'].sum().idxmax() if 'Machine' in df.columns and 'Value' in df.columns else 'N/A'}

=== Product Summary ===
Unique Products: {df['Product'].nunique() if 'Product' in df.columns else 'N/A'}
Top Product: {df.groupby('Product')['Value'].sum().idxmax() if 'Product' in df.columns and 'Value' in df.columns else 'N/A'}

=== Payment Summary ===
Payment Methods: {df['Super-Payment'].value_counts().to_dict() if 'Super-Payment' in df.columns else 'N/A'}
"""
    
    return report