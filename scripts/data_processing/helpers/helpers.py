import pandas as pd
import os
from CONSTANTS import TARGET_COLUMNS, MACHINE_MAPPING
from .utils import clean_for_mapping

from formatters import (
    standardize_format_standard,
    standardize_format_headers_in_first_row,
    standardize_format_2024_06,
    standardize_format_direct_columns,
    standardize_format_2024_05,
    standardize_format_teil3,
    standardize_format_clean2022_12
)

def filter_unwanted_rows(df):
    """
    Filter out unwanted rows from standardized DataFrame.
    
    Removes:
    - Test Vend and Token payments
    - Transactions with value < 1
    - Transactions with quantity != 1 (unless quantity is NaN)
    
    Args:
        df: Standardized DataFrame with required columns
        
    Returns:
        Filtered DataFrame with Quantity column removed
    """
    initial_rows = len(df)
    
    # Filter out Test Vend and Token payments
    df_filtered = df[~df['Payment'].str.contains('Test Vend|Token', case=False, na=False)]
    
    # Filter out transactions with value < 1
    df_filtered = df_filtered[df_filtered['Value'] >= 1]
        
    # Remove the Quantity column since it's no longer needed
    df_filtered = df_filtered.drop(columns=['Quantity'])
    
    filtered_rows = initial_rows - len(df_filtered)
    if filtered_rows > 0:
        print(f"  → Filtered out {filtered_rows} rows with unmatching data")
    
    return df_filtered

def process_file(filepath):
    """Process a single Excel file and return standardized DataFrame"""
    filename = os.path.basename(filepath)
    print(f"Processing {filename}...")
    
    try:
        df = pd.read_excel(filepath)
        format_type = detect_file_format(df, filename)
        
        print(f"  Detected format: {format_type}")
        print(f"  Original columns: {df.columns.tolist()}")
        print(f"  Shape: {df.shape}")
        
        if format_type == 'standard':
            standardized = standardize_format_standard(df)
        elif format_type == 'headers_in_first_row':
            standardized = standardize_format_headers_in_first_row(df)
        elif format_type == 'format_2024_05':
            standardized = standardize_format_2024_05(df)
        elif format_type == 'teil3_format':
            standardized = standardize_format_teil3(df)
        elif format_type == 'clean2022_12_format':
            standardized = standardize_format_clean2022_12(df)
        elif format_type == 'clean2023_01-06_format':
            standardized = standardize_format_direct_columns(df)
        elif format_type == 'clean2024_06_format':
            standardized = standardize_format_2024_06(df)
        else:
            print(f"  WARNING: Unknown format for {filename}")
            return None
        
        
        
        # Ensure all target columns exist
        for col in TARGET_COLUMNS:
            if col not in standardized.columns:
                if col == 'Timestamp':
                    standardized[col] = pd.NaT
                elif col in ['Value', 'Quantity']:
                    standardized[col] = 0
                else:
                    standardized[col] = ''
        
        # Add source file information
        standardized['SourceFile'] = filename
        
        # Reorder columns
        final_columns = TARGET_COLUMNS + ['SourceFile']
        standardized = standardized[final_columns]
        
        standardized = filter_unwanted_rows(standardized)

        # Create a cleaned version of MACHINE_MAPPING
        cleaned_mapping = {clean_for_mapping(k): v for k, v in MACHINE_MAPPING.items()}

        # Apply mapping with cleaned keys
        standardized['Machine_Clean'] = standardized['Machine'].apply(clean_for_mapping)
        standardized['Machine'] = standardized['Machine_Clean'].map(cleaned_mapping).fillna(standardized['Machine'])
        standardized = standardized.drop(columns=['Machine_Clean'])
              
        
        print(f"  ✓ Standardized to {len(standardized)} rows")
        return standardized
        
    except Exception as e:
        print(f"  ✗ Error processing {filename}: {str(e)}")
        return None


def detect_file_format(df, filename=""):
    """Detect the format of the Excel file"""
    columns = df.columns.tolist()
    
    # First check filename-specific formats before general pattern matching
    # Special format: 2023 Teil 3 format (from clean_part3.py)
    if filename in ["2023_11 Teil 3.xlsx", "2023_09 Teil 3.xlsx"]:
        return 'teil3_format'
    
    # Special format: 2022_12 format (from clean2022_12.py)
    if filename == "2022_12.xlsx":
        return 'clean2022_12_format'
    
    # Special format: 2024_06 format (needs custom category mapping)
    if filename == "2024_06.xlsx":
        return 'clean2024_06_format'
    
    # Special format: 2023_01-06 format variations - only if not standard format
    if "2023_01-06.xlsx" == filename:
        return 'clean2023_01-06_format'
    
    # Format 1: Standard format (2024 files) - CHECK AFTER filename-specific formats
    if 'Timestamp' in columns and 'Machine' in columns and 'Product' in columns:
        return 'standard'
    
    
    # Format 2: Headers in first row (2023_07 type)
    if len(columns) > 5 and any('Unnamed' in col for col in columns):
        first_row = df.iloc[0].tolist()
        if any('Maschinenname' in str(val) for val in first_row):
            return 'headers_in_first_row'
        
    # Format 6: 2024_05 format with specific column pattern
    if 'Automat' in columns and 'Cash/card' in columns and 'Art' in columns:
        return 'format_2024_05'
    
    return 'unknown'



