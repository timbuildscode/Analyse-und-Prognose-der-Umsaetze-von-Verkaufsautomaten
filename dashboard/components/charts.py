"""
Reusable chart components using Plotly
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from dashboard.config import COLOR_PALETTE, PLOTLY_THEME, CHART_FONT


def create_time_series_chart(df, x_col, y_col, title, show_ma=True, height=400):
    """Create time series chart with optional moving averages"""
    fig = go.Figure()
    
    # Main line
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode='lines',
        name=y_col,
        line=dict(color=COLOR_PALETTE['primary'], width=2),
        hovertemplate='%{x}<br>%{y:.2f}<extra></extra>'
    ))
    
    # Moving averages
    if show_ma and f'{y_col}_MA7' in df.columns:
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[f'{y_col}_MA7'],
            mode='lines',
            name='7-Day MA',
            line=dict(color=COLOR_PALETTE['secondary'], width=2, dash='dash'),
            hovertemplate='%{x}<br>7-Day MA: %{y:.2f}<extra></extra>'
        ))
    
    if show_ma and f'{y_col}_MA30' in df.columns:
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[f'{y_col}_MA30'],
            mode='lines',
            name='30-Day MA',
            line=dict(color=COLOR_PALETTE['success'], width=2, dash='dot'),
            hovertemplate='%{x}<br>30-Day MA: %{y:.2f}<extra></extra>'
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title=y_col,
        height=height,
        template=PLOTLY_THEME,
        hovermode='x unified',
        font=dict(family=CHART_FONT)
    )
    
    return fig


def create_bar_chart(df, x_col, y_col, title, color=None, orientation='v', height=400):
    """Create bar chart with improved styling and orientation handling"""
    
    # Create the basic bar chart
    if color:
        fig = px.bar(df, x=x_col, y=y_col, color=color, title=title, 
                     orientation=orientation, height=height)
    else:
        fig = px.bar(df, x=x_col, y=y_col, title=title, 
                     orientation=orientation, height=height,
                     color_discrete_sequence=[COLOR_PALETTE['primary']])
    
    # Improved layout based on orientation
    if orientation == 'h':
        # For horizontal charts (good for long labels)
        fig.update_layout(
            template=PLOTLY_THEME,
            font=dict(family=CHART_FONT, size=12),
            showlegend=bool(color),
            margin=dict(l=150, r=50, t=80, b=50),
            height=max(height, len(df) * 30 + 100),  # Dynamic height based on data
            xaxis=dict(
                title=y_col,
                tickformat='€,.0f' if 'revenue' in y_col.lower() or 'value' in y_col.lower() else None
            ),
            yaxis=dict(
                title=None,  # Remove y-axis title for cleaner look
                automargin=True
            )
        )
        
        # Update traces for better visibility
        fig.update_traces(
            hovertemplate='<b>%{y}</b><br>' + 
                         f'{y_col}: %{{x:€,.2f}}<extra></extra>',
            marker=dict(
                color=COLOR_PALETTE['primary'],
                line=dict(color='rgba(50,50,50,0.2)', width=1)
            )
        )
        
    else:
        # For vertical charts
        fig.update_layout(
            template=PLOTLY_THEME,
            font=dict(family=CHART_FONT, size=12),
            showlegend=bool(color),
            margin=dict(l=50, r=50, t=80, b=100),
            xaxis=dict(
                title=x_col,
                tickangle=-45 if len(df) > 5 else 0,
                automargin=True
            ),
            yaxis=dict(
                title=y_col,
                tickformat='€,.0f' if 'revenue' in y_col.lower() or 'value' in y_col.lower() else None
            )
        )
        
        # Update traces for better visibility
        fig.update_traces(
            hovertemplate='<b>%{x}</b><br>' + 
                         f'{y_col}: %{{y:€,.2f}}<extra></extra>',
            marker=dict(
                color=COLOR_PALETTE['primary'],
                line=dict(color='rgba(50,50,50,0.2)', width=1)
            )
        )
    
    return fig


def create_pie_chart(df, values_col, names_col, title, height=400):
    """Create pie chart"""
    fig = px.pie(df, values=values_col, names=names_col, title=title, height=height)
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='%{label}<br>%{value:.2f}<br>%{percent}<extra></extra>'
    )
    
    fig.update_layout(
        template=PLOTLY_THEME,
        font=dict(family=CHART_FONT)
    )
    
    return fig


def create_heatmap(df, title, height=600):
    """Create heatmap"""
    fig = go.Figure(data=go.Heatmap(
        z=df.values,
        x=df.columns,
        y=df.index,
        colorscale='Blues',
        hovertemplate='%{x}<br>%{y}<br>Value: %{z:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        height=height,
        template=PLOTLY_THEME,
        font=dict(family=CHART_FONT)
    )
    
    return fig


def create_scatter_plot(df, x_col, y_col, title, color_col=None, size_col=None, 
                       trendline=False, height=400):
    """Create scatter plot with optional trendline"""
    if trendline:
        trendline_type = "ols"
    else:
        trendline_type = None
    
    fig = px.scatter(
        df, x=x_col, y=y_col, color=color_col, size=size_col,
        title=title, trendline=trendline_type, height=height
    )
    
    fig.update_layout(
        template=PLOTLY_THEME,
        font=dict(family=CHART_FONT)
    )
    
    return fig


def create_box_plot(df, x_col, y_col, title, height=400):
    """Create box plot for distribution analysis"""
    fig = px.box(df, x=x_col, y=y_col, title=title, height=height)
    
    fig.update_layout(
        template=PLOTLY_THEME,
        font=dict(family=CHART_FONT)
    )
    
    return fig


def create_dual_axis_chart(df, x_col, y1_col, y2_col, y1_name, y2_name, title, height=400):
    """Create dual Y-axis chart"""
    fig = go.Figure()
    
    # First Y-axis
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y1_col],
        mode='lines',
        name=y1_name,
        line=dict(color=COLOR_PALETTE['primary'], width=2),
        yaxis='y'
    ))
    
    # Second Y-axis
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y2_col],
        mode='lines',
        name=y2_name,
        line=dict(color=COLOR_PALETTE['secondary'], width=2),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title=title,
        xaxis=dict(title=x_col),
        yaxis=dict(title=y1_name, side='left'),
        yaxis2=dict(title=y2_name, side='right', overlaying='y'),
        height=height,
        template=PLOTLY_THEME,
        hovermode='x unified',
        font=dict(family=CHART_FONT)
    )
    
    return fig


def create_gauge_chart(value, max_value, title, thresholds=None, height=300):
    """Create gauge chart for KPIs"""
    if thresholds is None:
        thresholds = {
            'good': max_value * 0.7,
            'warning': max_value * 0.4
        }
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        delta={'reference': thresholds['good']},
        gauge={
            'axis': {'range': [None, max_value]},
            'bar': {'color': COLOR_PALETTE['primary']},
            'steps': [
                {'range': [0, thresholds['warning']], 'color': COLOR_PALETTE['danger']},
                {'range': [thresholds['warning'], thresholds['good']], 'color': COLOR_PALETTE['warning']},
                {'range': [thresholds['good'], max_value], 'color': COLOR_PALETTE['success']}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    
    fig.update_layout(
        height=height,
        template=PLOTLY_THEME,
        font=dict(family=CHART_FONT)
    )
    
    return fig


def create_funnel_chart(df, stages_col, values_col, title, height=400):
    """Create funnel chart for conversion analysis"""
    fig = px.funnel(df, x=values_col, y=stages_col, title=title, height=height)
    
    fig.update_layout(
        template=PLOTLY_THEME,
        font=dict(family=CHART_FONT)
    )
    
    return fig


def create_waterfall_chart(df, x_col, y_col, title, height=400):
    """Create waterfall chart for cumulative analysis"""
    fig = go.Figure(go.Waterfall(
        x=df[x_col],
        y=df[y_col],
        text=[f"{v:,.0f}" for v in df[y_col]],
        textposition="outside"
    ))
    
    fig.update_layout(
        title=title,
        height=height,
        template=PLOTLY_THEME,
        font=dict(family=CHART_FONT),
        showlegend=False
    )
    
    return fig