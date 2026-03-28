"""
KPI Card Components for Dashboard
"""
import streamlit as st
from dashboard.utils.calculations import calculate_growth_rate


def create_kpi_card(label, value, delta=None, delta_color="normal", format_type="number"):
    """Create a single KPI card"""
    if format_type == "currency":
        value_str = f"€{value:,.2f}"
    elif format_type == "percentage":
        value_str = f"{value:.1f}%"
    elif format_type == "integer":
        value_str = f"{int(value):,}"
    else:
        value_str = f"{value:,.2f}"
    
    if delta is not None:
        if isinstance(delta, (int, float)):
            if delta > 0:
                delta_str = f"+{delta:.1f}%"
            else:
                delta_str = f"{delta:.1f}%"
        else:
            delta_str = str(delta)
        
        st.metric(label=label, value=value_str, delta=delta_str, delta_color=delta_color)
    else:
        st.metric(label=label, value=value_str)


def create_kpi_row(kpis, previous_kpis=None):
    """Create a row of KPI cards"""
    cols = st.columns(len(kpis))
    
    for i, (key, kpi_config) in enumerate(kpis.items()):
        with cols[i]:
            value = kpi_config['value']
            label = kpi_config['label']
            format_type = kpi_config.get('format', 'number')
            
            # Calculate delta if previous values provided
            delta = None
            delta_color = "normal"
            
            if previous_kpis and key in previous_kpis:
                prev_value = previous_kpis[key].get('value', 0)
                if prev_value != 0:
                    delta = calculate_growth_rate(value, prev_value)
                    # Determine color based on metric type
                    if kpi_config.get('inverse_color', False):
                        delta_color = "inverse"
            
            create_kpi_card(label, value, delta, delta_color, format_type)


def create_comparison_cards(current_data, previous_data, metrics_config):
    """Create comparison cards with period-over-period changes"""
    for metric_name, config in metrics_config.items():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        current_value = current_data.get(metric_name, 0)
        previous_value = previous_data.get(metric_name, 0)
        
        with col1:
            st.subheader(config['label'])
        
        with col2:
            st.metric(
                label="Current Period",
                value=format_value(current_value, config.get('format', 'number'))
            )
        
        with col3:
            change = current_value - previous_value
            change_pct = calculate_growth_rate(current_value, previous_value)
            
            st.metric(
                label="Change",
                value=format_value(change, config.get('format', 'number')),
                delta=f"{change_pct:.1f}%",
                delta_color="normal" if not config.get('inverse_color', False) else "inverse"
            )


def format_value(value, format_type):
    """Format value based on type"""
    if format_type == "currency":
        return f"€{value:,.2f}"
    elif format_type == "percentage":
        return f"{value:.1f}%"
    elif format_type == "integer":
        return f"{int(value):,}"
    else:
        return f"{value:,.2f}"


def create_info_card(title, content, icon=None, color="info"):
    """Create an information card"""
    color_map = {
        'info': '#17a2b8',
        'success': '#28a745',
        'warning': '#ffc107',
        'danger': '#dc3545',
        'primary': '#007bff'
    }
    
    card_html = f"""
    <div style="
        background-color: {color_map.get(color, '#17a2b8')}20;
        border-left: 4px solid {color_map.get(color, '#17a2b8')};
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    ">
        <h4 style="margin: 0; color: {color_map.get(color, '#17a2b8')};">
            {icon + ' ' if icon else ''}{title}
        </h4>
        <p style="margin: 0.5rem 0 0 0; color: #333;">
            {content}
        </p>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)


def create_trend_indicator(value, threshold_good=5, threshold_bad=-5):
    """Create a trend indicator with arrow and color"""
    if value > threshold_good:
        arrow = "↑"
        color = "green"
        text = "Strong Growth"
    elif value > 0:
        arrow = "↗"
        color = "lightgreen"
        text = "Growth"
    elif value > threshold_bad:
        arrow = "→"
        color = "orange"
        text = "Stable"
    else:
        arrow = "↓"
        color = "red"
        text = "Decline"
    
    return f'<span style="color: {color}; font-size: 1.5rem;">{arrow}</span> <span style="color: {color};">{text} ({value:.1f}%)</span>'