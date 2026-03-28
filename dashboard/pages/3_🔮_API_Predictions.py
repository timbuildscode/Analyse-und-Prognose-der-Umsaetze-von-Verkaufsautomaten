"""
API Predictions Page - Interactive predictions using the FastAPI backend
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from typing import Optional

# Import dashboard utilities
from dashboard.utils.api_client import (
    get_api_client, 
    create_prediction_summary_card, 
    display_model_info,
    format_currency,
    format_prediction_confidence
)
from dashboard.config import MACHINES, COLOR_PALETTE

# Page configuration
st.set_page_config(
    page_title="API Predictions",
    page_icon="",
    layout="wide"
)

st.title(" API Predictions")
st.markdown("Interactive predictions using the machine learning API")

# Initialize API client (clear cache if needed)
api_client = get_api_client(version="v1.1")

# Clear cache for development - remove this line in production
if st.sidebar.button(" Clear API Client Cache", help="Use this if API methods are missing"):
    st.cache_resource.clear()
    st.rerun()

# API Health Check
with st.sidebar:
    st.subheader("🔌 API Status")
    
    if st.button("Check API Health", type="primary"):
        with st.spinner("Checking API health..."):
            is_healthy = api_client.health_check()
            
        if is_healthy:
            st.success(" API is healthy and ready!")
        else:
            st.error(" API is not responding")
            st.info(" Make sure to start the API server:\n```bash\ncd api\nuv run uvicorn main:app --reload\n```")

# Create tabs for different prediction modes
tab1, tab2, tab3, tab4, tab5 = st.tabs([" Single Date", "📆 Date Range", " Model Info", " Batch Analysis", "🎛️ Feature Sliders"])

with tab1:
    st.header("Single Date Prediction")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        prediction_date = st.date_input(
            "Select Date for Prediction",
            value=date.today(),
            min_value=date(2023, 1, 1),
            max_value=date.today() + timedelta(days=365)
        )
        
        machine_option = st.selectbox(
            "Machine (Optional)",
            options=[None] + MACHINES,
            format_func=lambda x: "All Machines" if x is None else x
        )
    
    with col2:
        st.write("") # Space
        if st.button(" Make Prediction", type="primary", use_container_width=True):
            with st.spinner("Making prediction..."):
                prediction = api_client.predict_single_date(prediction_date, machine_option)
            
            if prediction:
                st.success(" Prediction completed!")
                create_prediction_summary_card(prediction)
                
                # Additional details
                with st.expander(" Prediction Details"):
                    st.json(prediction)
            else:
                st.error(" Failed to get prediction. Please check API connection.")

with tab2:
    st.header("Date Range Predictions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=date.today(),
            min_value=date(2023, 1, 1),
            max_value=date.today() + timedelta(days=365)
        )
    
    with col2:
        end_date = st.date_input(
            "End Date", 
            value=date.today() + timedelta(days=7),
            min_value=start_date,
            max_value=date.today() + timedelta(days=365)
        )
    
    machine_range_option = st.selectbox(
        "Machine (Optional)",
        options=[None] + MACHINES,
        format_func=lambda x: "All Machines" if x is None else x,
        key="range_machine"
    )
    
    if st.button(" Generate Range Predictions", type="primary"):
        if start_date > end_date:
            st.error(" Start date must be before end date")
        elif (end_date - start_date).days > 30:
            st.error(" Date range cannot exceed 30 days")
        else:
            with st.spinner("Generating predictions..."):
                batch_response = api_client.predict_date_range(start_date, end_date, machine_range_option)
            
            if batch_response and 'predictions' in batch_response:
                predictions = batch_response['predictions']
                
                # Summary metrics
                st.subheader(" Range Summary")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(" Days", len(predictions))
                
                with col2:
                    total_revenue = batch_response.get('total_predicted_revenue', 0)
                    st.metric("💰 Total Revenue", format_currency(total_revenue))
                
                with col3:
                    avg_revenue = total_revenue / len(predictions) if predictions else 0
                    st.metric(" Daily Average", format_currency(avg_revenue))
                
                with col4:
                    high_confidence = sum(1 for p in predictions if p['confidence'] == 'high')
                    confidence_pct = (high_confidence / len(predictions)) * 100 if predictions else 0
                    st.metric(" High Confidence %", f"{confidence_pct:.1f}%")
                
                # Convert to DataFrame for visualization
                df = pd.DataFrame(predictions)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                
                # Time series chart
                st.subheader(" Revenue Prediction Timeline")
                fig = px.line(
                    df, 
                    x='date', 
                    y='predicted_revenue',
                    title="Predicted Daily Revenue",
                    color_discrete_sequence=[COLOR_PALETTE['primary']]
                )
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Predicted Revenue (€)",
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Confidence distribution
                st.subheader(" Confidence Distribution")
                confidence_counts = df['confidence'].value_counts()
                fig_conf = px.pie(
                    values=confidence_counts.values,
                    names=confidence_counts.index,
                    title="Prediction Confidence Levels"
                )
                st.plotly_chart(fig_conf, use_container_width=True)
                
                # Detailed table
                with st.expander(" Detailed Predictions"):
                    # Format the dataframe for display
                    display_df = df.copy()
                    display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
                    display_df['predicted_revenue'] = display_df['predicted_revenue'].apply(lambda x: f"€{x:.2f}")
                    display_df['confidence'] = display_df['confidence'].apply(format_prediction_confidence)
                    
                    st.dataframe(
                        display_df[['date', 'predicted_revenue', 'confidence']],
                        column_config={
                            'date': 'Date',
                            'predicted_revenue': 'Predicted Revenue',
                            'confidence': 'Confidence'
                        },
                        use_container_width=True
                    )
                    
                    # Download button for CSV
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Predictions as CSV",
                        data=csv,
                        file_name=f"predictions_{start_date}_{end_date}.csv",
                        mime="text/csv"
                    )
            else:
                st.error(" Failed to get batch predictions. Please check API connection.")

with tab3:
    st.header("Model Information")
    
    if st.button(" Refresh Model Info", type="secondary"):
        with st.spinner("Fetching model information..."):
            model_info = api_client.get_model_info()
        
        if model_info:
            display_model_info(model_info)
        else:
            st.error(" Failed to fetch model information. Please check API connection.")

with tab4:
    st.header("Batch Analysis & Comparison")
    
    st.markdown("Compare predictions across different time periods and analyze patterns.")
    
    # Analysis period selection
    col1, col2 = st.columns(2)
    
    with col1:
        analysis_type = st.selectbox(
            "Analysis Type",
            ["Weekly Comparison", "Monthly Comparison", "Custom Period"]
        )
    
    with col2:
        base_date = st.date_input(
            "Base Date",
            value=date.today(),
            key="analysis_base"
        )
    
    if st.button(" Run Analysis", type="primary"):
        with st.spinner("Running analysis..."):
            periods = []
            
            if analysis_type == "Weekly Comparison":
                # Compare current week vs last 4 weeks
                for i in range(4):
                    week_start = base_date - timedelta(days=base_date.weekday()) - timedelta(weeks=i)
                    week_end = week_start + timedelta(days=6)
                    periods.append((f"Week -{i}", week_start, week_end))
                    
            elif analysis_type == "Monthly Comparison":
                # Compare current month vs last 3 months
                for i in range(3):
                    month_start = base_date.replace(day=1) - pd.DateOffset(months=i)
                    month_end = (month_start + pd.DateOffset(months=1) - timedelta(days=1)).date()
                    month_start = month_start.date()
                    periods.append((f"Month -{i}", month_start, month_end))
            
            # Fetch predictions for all periods
            comparison_data = []
            
            for period_name, start, end in periods:
                predictions_df = api_client.predict_to_dataframe(start, end)
                if predictions_df is not None:
                    total_revenue = predictions_df['predicted_revenue'].sum()
                    avg_daily = predictions_df['predicted_revenue'].mean()
                    high_conf_pct = (predictions_df['confidence'] == 'high').mean() * 100
                    
                    comparison_data.append({
                        'Period': period_name,
                        'Start Date': start.strftime('%Y-%m-%d'),
                        'End Date': end.strftime('%Y-%m-%d'),
                        'Total Revenue': total_revenue,
                        'Daily Average': avg_daily,
                        'High Confidence %': high_conf_pct,
                        'Days': len(predictions_df)
                    })
            
            if comparison_data:
                comparison_df = pd.DataFrame(comparison_data)
                
                # Display comparison table
                st.subheader(" Period Comparison")
                
                formatted_df = comparison_df.copy()
                formatted_df['Total Revenue'] = formatted_df['Total Revenue'].apply(lambda x: f"€{x:.2f}")
                formatted_df['Daily Average'] = formatted_df['Daily Average'].apply(lambda x: f"€{x:.2f}")
                formatted_df['High Confidence %'] = formatted_df['High Confidence %'].apply(lambda x: f"{x:.1f}%")
                
                st.dataframe(formatted_df, use_container_width=True)
                
                # Visualization
                fig_comparison = go.Figure()
                
                fig_comparison.add_trace(go.Bar(
                    name='Total Revenue',
                    x=comparison_df['Period'],
                    y=comparison_df['Total Revenue'],
                    yaxis='y',
                    offsetgroup=1
                ))
                
                fig_comparison.add_trace(go.Bar(
                    name='Daily Average',
                    x=comparison_df['Period'],
                    y=comparison_df['Daily Average'],
                    yaxis='y2',
                    offsetgroup=2
                ))
                
                fig_comparison.update_layout(
                    title="Revenue Comparison Across Periods",
                    xaxis_title="Period",
                    yaxis=dict(title='Total Revenue (€)', side='left'),
                    yaxis2=dict(title='Daily Average (€)', side='right', overlaying='y'),
                    barmode='group'
                )
                
                st.plotly_chart(fig_comparison, use_container_width=True)
            else:
                st.error(" No data available for analysis periods.")

with tab5:
    st.header("Feature Exploration with Sliders")
    st.markdown("🎛️ **Interactive Feature Testing**: Adjust individual features to see how the raw XGBoost model responds.")
    
    st.info(" **Tip**: The model responds most to **Revenue_MA_30** and **Revenue_MA_7**. Try moving these sliders to extremes (0 or 2000) to see the biggest changes!")
    
    # Add a real-time update option
    auto_update = st.checkbox(" Auto-update predictions as you move sliders", value=False, help="When enabled, predictions update automatically")
    
    # Handle preset modes
    preset_mode = getattr(st.session_state, 'preset_mode', None)
    if preset_mode:
        st.session_state.preset_mode = None  # Clear it after using
    
    # Define preset values
    if preset_mode == "high":
        preset_values = {
            'revenue_ma_30': 1800.0, 'revenue_ma_7': 1800.0, 'revenue_lag_1': 1600.0,
            'revenue_lag_2': 1600.0, 'revenue_lag_3': 1600.0, 'revenue_lag_7': 1600.0,
            'revenue_lag_14': 1600.0, 'revenue_lag_30': 1600.0, 'revenue_vol_7': 100.0, 'revenue_vol_30': 100.0
        }
    elif preset_mode == "low":
        preset_values = {
            'revenue_ma_30': 100.0, 'revenue_ma_7': 100.0, 'revenue_lag_1': 50.0,
            'revenue_lag_2': 50.0, 'revenue_lag_3': 50.0, 'revenue_lag_7': 50.0,
            'revenue_lag_14': 50.0, 'revenue_lag_30': 50.0, 'revenue_vol_7': 5.0, 'revenue_vol_30': 5.0
        }
    elif preset_mode == "random":
        import numpy as np
        np.random.seed(42)  # For reproducible randomness
        preset_values = {
            'revenue_ma_30': float(np.random.uniform(100, 1800)), 'revenue_ma_7': float(np.random.uniform(100, 1800)),
            'revenue_lag_1': float(np.random.uniform(100, 1600)), 'revenue_lag_2': float(np.random.uniform(100, 1600)),
            'revenue_lag_3': float(np.random.uniform(100, 1600)), 'revenue_lag_7': float(np.random.uniform(100, 1600)),
            'revenue_lag_14': float(np.random.uniform(100, 1600)), 'revenue_lag_30': float(np.random.uniform(100, 1600)),
            'revenue_vol_7': float(np.random.uniform(10, 100)), 'revenue_vol_30': float(np.random.uniform(10, 100))
        }
    else:
        preset_values = {}  # Use defaults
    
    # Create two columns for better layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(" Temporal Features")
        
        # Temporal features
        day_of_week = st.slider("Day of Week", 0, 6, 0, help="0=Monday, 6=Sunday")
        month = st.slider("Month", 1, 12, 12, help="1=January, 12=December")
        quarter = st.slider("Quarter", 1, 4, 4)
        is_weekend = st.slider("Is Weekend", 0, 1, 0, help="0=No, 1=Yes")
        is_month_start = st.slider("Is Month Start", 0, 1, 0, help="0=No, 1=Yes") 
        is_month_end = st.slider("Is Month End", 0, 1, 0, help="0=No, 1=Yes")
        
        st.subheader("🌊 Cyclic Features")
        day_of_week_sin = st.slider("DayOfWeek Sin", -1.0, 1.0, 0.0, step=0.1)
        day_of_week_cos = st.slider("DayOfWeek Cos", -1.0, 1.0, 1.0, step=0.1)
        month_sin = st.slider("Month Sin", -1.0, 1.0, 0.0, step=0.1)
        month_cos = st.slider("Month Cos", -1.0, 1.0, 1.0, step=0.1)
        day_of_year_sin = st.slider("DayOfYear Sin", -1.0, 1.0, 0.0, step=0.1)
        day_of_year_cos = st.slider("DayOfYear Cos", -1.0, 1.0, 1.0, step=0.1)
    
    with col2:
        st.subheader(" Revenue Lag Features")
        
        # Revenue lag features - using wider ranges to see bigger effects
        revenue_lag_1 = st.slider("Revenue Lag 1", 0.0, 2000.0, preset_values.get('revenue_lag_1', 495.0), step=25.0, help="Previous day revenue")
        revenue_lag_2 = st.slider("Revenue Lag 2", 0.0, 2000.0, preset_values.get('revenue_lag_2', 495.0), step=25.0, help="2 days ago revenue")
        revenue_lag_3 = st.slider("Revenue Lag 3", 0.0, 2000.0, preset_values.get('revenue_lag_3', 495.0), step=25.0, help="3 days ago revenue")
        revenue_lag_7 = st.slider("Revenue Lag 7", 0.0, 2000.0, preset_values.get('revenue_lag_7', 493.0), step=25.0, help="1 week ago revenue")
        revenue_lag_14 = st.slider("Revenue Lag 14", 0.0, 2000.0, preset_values.get('revenue_lag_14', 491.0), step=25.0, help="2 weeks ago revenue")
        revenue_lag_30 = st.slider("Revenue Lag 30", 0.0, 2000.0, preset_values.get('revenue_lag_30', 486.0), step=25.0, help="1 month ago revenue")
        
        st.subheader(" Moving Averages & Volatility")
        revenue_ma_7 = st.slider("Revenue MA 7", 0.0, 2000.0, preset_values.get('revenue_ma_7', 495.0), step=25.0, help="7-day moving average ⭐ IMPORTANT")
        revenue_ma_30 = st.slider("Revenue MA 30", 0.0, 2000.0, preset_values.get('revenue_ma_30', 492.0), step=25.0, help="30-day moving average ⭐ MOST IMPORTANT")
        revenue_vol_7 = st.slider("Revenue Volatility 7", 0.0, 300.0, preset_values.get('revenue_vol_7', 25.0), step=5.0, help="7-day volatility")
        revenue_vol_30 = st.slider("Revenue Volatility 30", 0.0, 300.0, preset_values.get('revenue_vol_30', 30.0), step=5.0, help="30-day volatility")
    
    # Prediction section
    st.markdown("---")
    
    col_pred1, col_pred2, col_pred3 = st.columns([2, 1, 2])
    
    with col_pred2:
        should_predict = st.button(" Get Raw XGBoost Prediction", type="primary", use_container_width=True) or auto_update
        
        if should_predict:
            with st.spinner("Making raw prediction..."):
                # Prepare features dict
                features = {
                    'DayOfWeek': day_of_week,
                    'Month': month,
                    'Quarter': quarter,
                    'IsWeekend': is_weekend,
                    'IsMonthStart': is_month_start,
                    'IsMonthEnd': is_month_end,
                    'DayOfWeek_sin': day_of_week_sin,
                    'DayOfWeek_cos': day_of_week_cos,
                    'Month_sin': month_sin,
                    'Month_cos': month_cos,
                    'DayOfYear_sin': day_of_year_sin,
                    'DayOfYear_cos': day_of_year_cos,
                    'Revenue_Lag_1': revenue_lag_1,
                    'Revenue_Lag_2': revenue_lag_2,
                    'Revenue_Lag_3': revenue_lag_3,
                    'Revenue_Lag_7': revenue_lag_7,
                    'Revenue_Lag_14': revenue_lag_14,
                    'Revenue_Lag_30': revenue_lag_30,
                    'Revenue_MA_7': revenue_ma_7,
                    'Revenue_MA_30': revenue_ma_30,
                    'Revenue_Volatility_7': revenue_vol_7,
                    'Revenue_Volatility_30': revenue_vol_30
                }
                
                # Make raw prediction - handle potential caching issues
                try:
                    result = api_client.predict_raw_features(features)
                except AttributeError:
                    st.error(" API client cache issue detected. Please click ' Clear API Client Cache' in the sidebar and try again.")
                    st.stop()
                
                if result:
                    st.success(" Raw prediction completed!")
                    
                    # Display result prominently
                    st.markdown("###  Raw XGBoost Prediction")
                    prediction_value = result['raw_prediction']
                    st.metric(
                        label="Predicted Revenue (No Post-Processing)",
                        value=f"€{prediction_value:.2f}",
                        delta=None
                    )
                    
                    # Model info
                    st.info(f" **Model Version**: {result.get('model_version', 'Unknown')}")
                    
                    # Show feature importance hints
                    with st.expander(" Feature Importance Hints"):
                        st.markdown("""
                        **Most Important Features (from XGBoost analysis):**
                        - 🥇 **Revenue_MA_30** (34%): 30-day moving average has the highest impact
                        - 🥈 **Revenue_MA_7** (16%): 7-day moving average is second most important  
                        - 🥉 **Revenue_Lag_2 × Revenue_Lag_7** (12%): Polynomial interaction feature
                        -  **Quarter** (7%): Seasonal patterns matter
                        - ⚡ **Revenue_Lag_1 × Revenue_Lag_7** (5%): Another interaction feature
                        
                        **Try adjusting the moving averages (MA_7, MA_30) to see the biggest changes!**
                        """)
                    
                    # Show raw features used
                    with st.expander(" Input Features Summary"):
                        feature_df = pd.DataFrame([features]).T
                        feature_df.columns = ['Value']
                        feature_df.index.name = 'Feature'
                        st.dataframe(feature_df)
                    
                else:
                    st.error(" Failed to get raw prediction. Please check API connection.")
    
    # Quick preset buttons
    st.markdown("---")
    st.subheader("🎚️ Quick Presets")
    st.markdown("Click these buttons to quickly test different scenarios:")
    
    preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)
    
    with preset_col1:
        if st.button(" High Revenue Scenario", use_container_width=True, help="Set all revenue features to high values"):
            st.session_state.preset_mode = "high"
            st.rerun()
    
    with preset_col2:
        if st.button(" Low Revenue Scenario", use_container_width=True, help="Set all revenue features to low values"):
            st.session_state.preset_mode = "low"
            st.rerun()
    
    with preset_col3:
        if st.button(" Reset to Defaults", use_container_width=True, help="Reset all sliders to default values"):
            st.session_state.preset_mode = "default"
            st.rerun()
    
    with preset_col4:
        if st.button("🎲 Random Values", use_container_width=True, help="Set sliders to random values"):
            st.session_state.preset_mode = "random"
            st.rerun()

# Footer
st.markdown("---")
st.markdown(" **Tip**: Start the API server with `uv run uvicorn api.main:app --reload` to use these features.")