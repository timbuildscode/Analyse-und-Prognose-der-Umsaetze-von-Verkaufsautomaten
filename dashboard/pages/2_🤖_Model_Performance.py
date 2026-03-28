"""
Model Performance Page
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from dashboard.utils.data_loader import load_daily_sales_data
from dashboard.utils.model_utils import (
    load_model_artifacts, get_available_models, make_predictions,
    create_future_features, calculate_prediction_intervals,
    get_feature_importance, prepare_features_for_prediction,
    get_model_artifacts_summary
)
from dashboard.components.charts import (
    create_time_series_chart, create_bar_chart, create_scatter_plot,
    create_gauge_chart, create_dual_axis_chart
)
from dashboard.components.kpi_cards import create_kpi_row, create_info_card
from dashboard.config import KPI_THRESHOLDS, MODELS_DIR

# Page configuration
st.set_page_config(
    page_title="Model Performance - Vending Machine Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    st.title(" Model Performance Dashboard")
    
    # Load available models
    available_models = get_available_models()
    
    if not available_models:
        st.error("No trained models found. Please train a model first.")
        return
    
    # Model selection
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_model = st.selectbox(
            "Select Model",
            options=[m['timestamp'] for m in available_models],
            format_func=lambda x: next(m['display_name'] for m in available_models if m['timestamp'] == x)
        )
    
    with col2:
        st.write("")  # Spacing
        if st.button(" Refresh Models"):
            st.cache_resource.clear()
            st.rerun()
    
    # Get selected model details
    model_info = next(m for m in available_models if m['timestamp'] == selected_model)
    
    # Load model artifacts
    with st.spinner("Loading model..."):
        artifacts = load_model_artifacts(selected_model)
    
    if not artifacts:
        st.error("Failed to load model artifacts.")
        return
    
    # Model Information Section
    st.markdown("### Model Information")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        create_info_card(
            "Model Type",
            artifacts['metadata'].get('model_type', 'Unknown'),
            "",
            "primary"
        )
    
    with col2:
        training_period = artifacts['metadata'].get('training_data_period', {})
        if training_period:
            period_text = f"{training_period.get('start_date', 'N/A')} to {training_period.get('end_date', 'N/A')}"
        else:
            period_text = "N/A"
        create_info_card(
            "Training Period",
            period_text,
            "",
            "info"
        )
    
    with col3:
        create_info_card(
            "Features Used",
            f"{artifacts['metadata'].get('feature_count', 0)} features",
            "",
            "success"
        )
    
    # Performance Metrics
    st.markdown("### Performance Metrics")
    
    perf_metrics = artifacts['metadata'].get('performance_metrics', {})
    
    kpi_configs = {
        'mae': {
            'label': 'Mean Absolute Error',
            'value': perf_metrics.get('test_mae', 0),
            'format': 'number',
            'inverse_color': True
        },
        'rmse': {
            'label': 'Root Mean Square Error',
            'value': perf_metrics.get('test_rmse', 0),
            'format': 'number',
            'inverse_color': True
        },
        'r2': {
            'label': 'R² Score',
            'value': perf_metrics.get('test_r2', 0),
            'format': 'percentage'
        }
    }
    
    create_kpi_row(kpi_configs)
    
    # Performance gauges
    col1, col2, col3 = st.columns(3)
    
    with col1:
        mae_gauge = create_gauge_chart(
            perf_metrics.get('test_mae', 0),
            200,  # Max value
            "MAE Performance",
            thresholds={
                'good': KPI_THRESHOLDS['model_mae_good'],
                'warning': KPI_THRESHOLDS['model_mae_warning']
            }
        )
        st.plotly_chart(mae_gauge, use_container_width=True)
    
    with col2:
        r2_gauge = create_gauge_chart(
            perf_metrics.get('test_r2', 0),
            1,  # Max value
            "R² Score",
            thresholds={
                'good': KPI_THRESHOLDS['model_r2_good'],
                'warning': KPI_THRESHOLDS['model_r2_warning']
            }
        )
        st.plotly_chart(r2_gauge, use_container_width=True)
    
    with col3:
        # Feature importance preview
        feature_names = artifacts['metadata'].get('selected_features', [])
        if feature_names and artifacts.get('model'):
            importance_df = get_feature_importance(artifacts['model'], feature_names)
            if not importance_df.empty:
                top_features = importance_df.head(5)
                
                fig = go.Figure(go.Bar(
                    x=top_features['importance_pct'],
                    y=top_features['feature'],
                    orientation='h'
                ))
                fig.update_layout(
                    title="Top 5 Important Features",
                    xaxis_title="Importance %",
                    yaxis_title="",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs(["Predictions", "Feature Analysis", "Model Comparison", "Diagnostics"])
    
    # Tab 1: Predictions
    with tab1:
        st.markdown("### Sales Predictions")
        
        # Load historical data
        historical_data = load_daily_sales_data()
        
        if historical_data.empty:
            st.warning("No historical data available for predictions.")
        else:
            # Prediction horizon
            col1, col2 = st.columns([2, 1])
            
            with col1:
                prediction_days = st.slider(
                    "Prediction Horizon (days)",
                    min_value=1,
                    max_value=30,
                    value=7
                )
            
            with col2:
                confidence_level = st.select_slider(
                    "Confidence Level",
                    options=[0.90, 0.95, 0.99],
                    value=0.95,
                    format_func=lambda x: f"{int(x*100)}%"
                )
            
            # Create future features
            last_date = historical_data['Date'].max()
            future_features = create_future_features(
                last_date,
                prediction_days,
                historical_data
            )
            
            # Prepare features for prediction
            selected_features = artifacts['metadata'].get('selected_features', [])
            X_future = prepare_features_for_prediction(future_features, selected_features)
            
            # Make predictions
            predictions, error = make_predictions(artifacts, X_future)
            
            if error:
                st.error(f"Prediction error: {error}")
            else:
                # Calculate prediction intervals
                model_mae = perf_metrics.get('test_mae', 50)
                lower_bound, upper_bound = calculate_prediction_intervals(
                    predictions,
                    model_mae,
                    confidence_level
                )
                
                # Create prediction dataframe
                prediction_df = pd.DataFrame({
                    'Date': future_features['Date'],
                    'Predicted_Revenue': predictions,
                    'Lower_Bound': lower_bound,
                    'Upper_Bound': upper_bound
                })
                
                # Combine with historical data for visualization
                recent_historical = historical_data.tail(30)[['Date', 'Daily_Revenue']]
                recent_historical.columns = ['Date', 'Actual_Revenue']
                
                # Visualization
                fig = go.Figure()
                
                # Historical data
                fig.add_trace(go.Scatter(
                    x=recent_historical['Date'],
                    y=recent_historical['Actual_Revenue'],
                    mode='lines+markers',
                    name='Actual',
                    line=dict(color='blue', width=2)
                ))
                
                # Predictions
                fig.add_trace(go.Scatter(
                    x=prediction_df['Date'],
                    y=prediction_df['Predicted_Revenue'],
                    mode='lines+markers',
                    name='Predicted',
                    line=dict(color='red', width=2, dash='dash')
                ))
                
                # Confidence interval
                fig.add_trace(go.Scatter(
                    x=prediction_df['Date'].tolist() + prediction_df['Date'].tolist()[::-1],
                    y=prediction_df['Upper_Bound'].tolist() + prediction_df['Lower_Bound'].tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(255, 0, 0, 0.2)',
                    line=dict(color='rgba(255, 0, 0, 0)'),
                    name=f'{int(confidence_level*100)}% Confidence Interval'
                ))
                
                fig.update_layout(
                    title=f"Revenue Forecast - Next {prediction_days} Days",
                    xaxis_title="Date",
                    yaxis_title="Revenue (€)",
                    height=500,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Prediction summary
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Total Predicted Revenue",
                        f"€{prediction_df['Predicted_Revenue'].sum():,.2f}",
                        f"Next {prediction_days} days"
                    )
                
                with col2:
                    st.metric(
                        "Average Daily Prediction",
                        f"€{prediction_df['Predicted_Revenue'].mean():,.2f}",
                        f"±€{model_mae:.2f}"
                    )
                
                with col3:
                    st.metric(
                        "Peak Day Prediction",
                        f"€{prediction_df['Predicted_Revenue'].max():,.2f}",
                        prediction_df.loc[prediction_df['Predicted_Revenue'].idxmax(), 'Date'].strftime('%Y-%m-%d')
                    )
                
                # Detailed predictions table
                with st.expander("View Detailed Predictions"):
                    display_df = prediction_df.copy()
                    display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
                    display_df['Predicted_Revenue'] = display_df['Predicted_Revenue'].map('€{:,.2f}'.format)
                    display_df['Lower_Bound'] = display_df['Lower_Bound'].map('€{:,.2f}'.format)
                    display_df['Upper_Bound'] = display_df['Upper_Bound'].map('€{:,.2f}'.format)
                    
                    st.dataframe(display_df, use_container_width=True)
    
    # Tab 2: Feature Analysis
    with tab2:
        st.markdown("### Feature Importance Analysis")
        
        feature_names = artifacts['metadata'].get('selected_features', [])
        
        if feature_names and artifacts.get('model'):
            importance_df = get_feature_importance(artifacts['model'], feature_names)
            
            if not importance_df.empty:
                # Full feature importance chart
                fig_importance = create_bar_chart(
                    importance_df.head(20),
                    'feature',
                    'importance_pct',
                    'Feature Importance (%)',
                    orientation='h',
                    height=600
                )
                st.plotly_chart(fig_importance, use_container_width=True)
                
                # Feature categories
                st.markdown("### Feature Categories")
                
                col1, col2, col3 = st.columns(3)
                
                # Categorize features
                time_features = [f for f in feature_names if any(x in f.lower() for x in ['day', 'week', 'month', 'year', 'quarter'])]
                lag_features = [f for f in feature_names if 'lag' in f.lower()]
                other_features = [f for f in feature_names if f not in time_features + lag_features]
                
                with col1:
                    create_info_card(
                        "Time-based Features",
                        f"{len(time_features)} features",
                        "",
                        "info"
                    )
                    if time_features:
                        st.write("Examples:", ", ".join(time_features[:3]))
                
                with col2:
                    create_info_card(
                        "Lag Features",
                        f"{len(lag_features)} features",
                        "",
                        "warning"
                    )
                    if lag_features:
                        st.write("Examples:", ", ".join(lag_features[:3]))
                
                with col3:
                    create_info_card(
                        "Other Features",
                        f"{len(other_features)} features",
                        "",
                        "success"
                    )
                    if other_features:
                        st.write("Examples:", ", ".join(other_features[:3]))
    
    # Tab 3: Model Comparison
    with tab3:
        st.markdown("### Model Comparison")
        
        if len(available_models) > 1:
            # Select models to compare
            models_to_compare = st.multiselect(
                "Select models to compare",
                options=[m['timestamp'] for m in available_models],
                default=[m['timestamp'] for m in available_models[:3]],
                format_func=lambda x: next(m['display_name'] for m in available_models if m['timestamp'] == x)
            )
            
            if len(models_to_compare) >= 2:
                # Create comparison dataframe
                comparison_data = []
                
                for model_ts in models_to_compare:
                    model_info = next(m for m in available_models if m['timestamp'] == model_ts)
                    perf = model_info['performance']
                    
                    comparison_data.append({
                        'Model': model_info['display_name'],
                        'MAE': perf.get('test_mae', np.nan),
                        'RMSE': perf.get('test_rmse', np.nan),
                        'R²': perf.get('test_r2', np.nan),
                        'Features': len(model_info['features'])
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                
                # Comparison charts
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_mae = create_bar_chart(
                        comparison_df,
                        'Model',
                        'MAE',
                        'Mean Absolute Error Comparison'
                    )
                    st.plotly_chart(fig_mae, use_container_width=True)
                
                with col2:
                    fig_r2 = create_bar_chart(
                        comparison_df,
                        'Model',
                        'R²',
                        'R² Score Comparison'
                    )
                    st.plotly_chart(fig_r2, use_container_width=True)
                
                # Detailed comparison table
                st.markdown("### Detailed Comparison")
                
                display_comparison = comparison_df.copy()
                display_comparison['MAE'] = display_comparison['MAE'].map('{:.2f}'.format)
                display_comparison['RMSE'] = display_comparison['RMSE'].map('{:.2f}'.format)
                display_comparison['R²'] = display_comparison['R²'].map('{:.4f}'.format)
                
                st.dataframe(display_comparison, use_container_width=True)
        else:
            st.info("Train more models to enable comparison.")
    
    # Tab 4: Diagnostics
    with tab4:
        st.markdown("### Model Diagnostics")
        
        # Model Artifacts Section
        st.markdown("#### Model Artifacts")
        
        # Show artifacts for this specific model
        col1, col2, col3, col4 = st.columns(4)
        
        # Check which artifacts exist for this model
        artifacts_status = {
            'XGBoost Model': bool(artifacts.get('model')),
            'Feature Selector': bool(artifacts.get('selector')),
            'Polynomial Features': bool(artifacts.get('poly_features')),
            'Data Scaler': bool(artifacts.get('scaler'))
        }
        
        # Check for additional files
        model_files = {
            'Sales Pipeline': (MODELS_DIR / f"sales_prediction_pipeline_{selected_model}.joblib").exists(),
            'Service File': (MODELS_DIR / f"sales_prediction_service_{selected_model}.py").exists(),
            'Monitoring': (MODELS_DIR / f"model_monitoring_{selected_model}.md").exists(),
            'Metadata': (MODELS_DIR / f"model_metadata_{selected_model}.json").exists()
        }
        
        artifacts_status.update(model_files)
        
        # Display artifact status in cards
        artifact_items = list(artifacts_status.items())
        
        for i, (artifact_name, exists) in enumerate(artifact_items):
            col = [col1, col2, col3, col4][i % 4]
            with col:
                if exists:
                    create_info_card(
                        artifact_name,
                        " Available",
                        "📁",
                        "success"
                    )
                else:
                    create_info_card(
                        artifact_name,
                        " Missing",
                        "📁",
                        "error"
                    )
        
        # Model artifacts summary for all models
        st.markdown("#### All Model Artifacts Summary")
        
        artifacts_summary = get_model_artifacts_summary()
        
        if artifacts_summary['total_artifacts'] > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Total Artifacts by Type:**")
                for artifact_type, count in artifacts_summary['artifact_types'].items():
                    st.write(f"- {artifact_type}: {count}")
            
            with col2:
                st.markdown("**Model Timestamps:**")
                for timestamp in artifacts_summary['timestamps'][:10]:  # Show first 10
                    st.write(f"- {timestamp}")
                if len(artifacts_summary['timestamps']) > 10:
                    st.write(f"... and {len(artifacts_summary['timestamps']) - 10} more")
        
        # Hyperparameters
        if 'hyperparameters' in artifacts['metadata']:
            st.markdown("#### Hyperparameters")
            
            hyperparams = artifacts['metadata']['hyperparameters']
            
            cols = st.columns(4)
            for i, (param, value) in enumerate(hyperparams.items()):
                with cols[i % 4]:
                    st.metric(param.replace('_', ' ').title(), value)
        
        # Model monitoring notes
        monitoring_file = f"model_monitoring_{selected_model}.md"
        monitoring_path = Path(st.session_state.get('MODELS_DIR', MODELS_DIR)) / monitoring_file
        
        if monitoring_path.exists():
            st.markdown("#### Monitoring Notes")
            with open(monitoring_path, 'r') as f:
                monitoring_content = f.read()
            st.text_area("", monitoring_content, height=200, disabled=True)
        
        # Feature list
        with st.expander("View All Features"):
            feature_names = artifacts['metadata'].get('selected_features', [])
            if feature_names:
                # Display in columns
                n_cols = 3
                cols = st.columns(n_cols)
                
                for i, feature in enumerate(feature_names):
                    with cols[i % n_cols]:
                        st.write(f"- {feature}")


if __name__ == "__main__":
    main()