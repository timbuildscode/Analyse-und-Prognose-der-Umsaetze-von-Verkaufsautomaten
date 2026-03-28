"""
Time aggregation utilities for different granularities
"""
import pandas as pd
import numpy as np


def aggregate_by_granularity(df, granularity='Daily', date_column='Date', value_column='Value'):
    """
    Aggregate data by specified time granularity
    
    Parameters:
    - df: DataFrame with transaction data
    - granularity: 'Daily', 'Weekly', or 'Monthly'
    - date_column: Name of the date column
    - value_column: Name of the value column to aggregate
    
    Returns:
    - Aggregated DataFrame with appropriate time periods
    """
    if df.empty:
        return df.copy()
    
    # Ensure date column is datetime
    df = df.copy()
    if date_column not in df.columns:
        return pd.DataFrame()  # Return empty DataFrame instead of original
    
    if value_column not in df.columns:
        return pd.DataFrame()  # Return empty DataFrame if value column missing
    
    df[date_column] = pd.to_datetime(df[date_column])
    
    if granularity == 'Daily':
        # Group by date
        time_key = df[date_column].dt.date
        date_format = '%Y-%m-%d'
        
    elif granularity == 'Weekly':
        # Group by week (Monday as start of week)
        time_key = df[date_column].dt.to_period('W-MON')
        date_format = 'Week of %Y-%m-%d'
        
    elif granularity == 'Monthly':
        # Group by month
        time_key = df[date_column].dt.to_period('M')
        date_format = '%Y-%m'
        
    else:
        # Default to daily
        time_key = df[date_column].dt.date
        date_format = '%Y-%m-%d'
    
    # Build aggregation dictionary with only existing columns
    agg_dict = {}
    
    # Primary value column (always exists if we got this far)
    if value_column in df.columns:
        agg_dict[value_column] = ['sum', 'count']  # Sum for total, count for transactions
    
    # Optional columns - only add if they exist
    if 'Quantity' in df.columns:
        agg_dict['Quantity'] = 'sum'
    
    if 'Machine' in df.columns:
        agg_dict['Machine'] = 'nunique'
    
    if 'Product' in df.columns:
        agg_dict['Product'] = 'nunique'
    
    # Perform aggregation
    aggregated = df.groupby(time_key).agg(agg_dict).reset_index()
    
    # The first column after reset_index() contains our time data
    # Explicitly name it as the date column
    first_col = aggregated.columns[0]
    
    # Flatten multi-level columns if they exist (but preserve the date column)
    if isinstance(aggregated.columns, pd.MultiIndex):
        # Flatten the columns
        new_columns = []
        for i, col in enumerate(aggregated.columns):
            if i == 0:
                # First column is always the date/time column
                new_columns.append(date_column)
            elif isinstance(col, tuple):
                if col[1] == 'sum':
                    new_columns.append(col[0])
                elif col[1] == 'count':
                    new_columns.append('Transactions')
                else:
                    new_columns.append(f"{col[0]}_{col[1]}")
            else:
                new_columns.append(col)
        aggregated.columns = new_columns
    else:
        # Simple columns - just rename the first one to date_column
        new_columns = list(aggregated.columns)
        new_columns[0] = date_column
        aggregated.columns = new_columns
    
    # Format the time column for display (only if the date column exists)
    if date_column in aggregated.columns:
        if granularity == 'Weekly':
            aggregated[date_column] = aggregated[date_column].dt.start_time.dt.strftime('Week of %Y-%m-%d')
        elif granularity == 'Monthly':
            aggregated[date_column] = aggregated[date_column].dt.strftime('%Y-%m')
        else:
            aggregated[date_column] = pd.to_datetime(aggregated[date_column]).dt.strftime('%Y-%m-%d')
    
    # Add derived metrics only if the required columns exist
    if value_column in aggregated.columns and 'Transactions' in aggregated.columns:
        aggregated['AvgTransactionValue'] = np.where(
            aggregated['Transactions'] > 0,
            aggregated[value_column] / aggregated['Transactions'],
            0
        )
    
    return aggregated


def create_time_comparison(df, granularity='Daily', date_column='Date', value_column='Value'):
    """
    Create period-over-period comparison based on granularity
    
    Returns:
    - DataFrame with current and previous period comparisons
    """
    aggregated = aggregate_by_granularity(df, granularity, date_column, value_column)
    
    if aggregated.empty or len(aggregated) < 2:
        return aggregated
    
    # Sort by date
    aggregated = aggregated.sort_values(date_column)
    
    # Calculate period-over-period changes
    aggregated['PreviousPeriod'] = aggregated[value_column].shift(1)
    aggregated['Change'] = aggregated[value_column] - aggregated['PreviousPeriod']
    aggregated['ChangePercent'] = np.where(
        aggregated['PreviousPeriod'] > 0,
        (aggregated['Change'] / aggregated['PreviousPeriod'] * 100).round(2),
        0
    )
    
    return aggregated


def get_period_label(granularity):
    """Get appropriate label for the selected granularity"""
    labels = {
        'Daily': 'Day',
        'Weekly': 'Week', 
        'Monthly': 'Month'
    }
    return labels.get(granularity, 'Period')


def get_date_format(granularity):
    """Get appropriate date format for the selected granularity"""
    formats = {
        'Daily': '%Y-%m-%d',
        'Weekly': 'Week of %Y-%m-%d',
        'Monthly': '%Y-%m'
    }
    return formats.get(granularity, '%Y-%m-%d')