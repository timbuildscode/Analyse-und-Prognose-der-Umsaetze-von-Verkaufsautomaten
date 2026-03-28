"""
Headers in First Row Format Standardizer

Handles files where the actual column headers are in the first row of data
(e.g., 2023_07, 2023_09 Teil 2, 2023_10 Teil 2).
"""

import pandas as pd
from helpers.utils import find_super_category, find_super_payment


def standardize_format_headers_in_first_row(df):
    """Standardize files with headers in the first row"""
    # Get the actual column names from the first row
    new_columns = df.iloc[0].tolist()
    df_clean = df.iloc[1:].copy()
    df_clean.columns = new_columns
    
    standardized = pd.DataFrame()
    
    # Map columns
    timestamp_col = df_clean.get('Maschinen-Begleichszeit')
    if timestamp_col is not None and hasattr(timestamp_col, 'apply'):
        standardized['Timestamp'] = pd.to_datetime(timestamp_col, errors='coerce', dayfirst=True)
    else:
        standardized['Timestamp'] = pd.NaT
    
    standardized['Machine'] = df_clean.get('Maschinenname', '').fillna('')
    standardized['Product'] = df_clean.get('Produktname', '').fillna('')
    
    # Keep original category from product group
    product_group = df_clean.get('Produktgruppe', '')
    if product_group is not None and hasattr(product_group, 'fillna'):
        standardized['Category'] = product_group.fillna('')
    else:
        standardized['Category'] = ''
    
    # Map super-category directly from product or category
    super_category = []
    for _, row in df_clean.iterrows():
        product = row.get('Produktname', '')
        category = row.get('Produktgruppe', '')
        super_category.append(find_super_category(product, category))
    
    standardized['Super-Category'] = super_category
    
    # Payment method
    payment_source = df_clean.get('Payment Method (Source)', '')
    if payment_source is not None and hasattr(payment_source, 'fillna'):
        standardized['Payment'] = payment_source.fillna('')
    else:
        standardized['Payment'] = ''
    
    # Map super-payment directly from payment
    super_payment = []
    for _, row in df_clean.iterrows():
        payment = row.get('Payment Method (Source)', '')
        super_payment.append(find_super_payment(payment))
    
    standardized['Super-Payment'] = super_payment
    
    # Add Tax column - extract from MwSt., MwSt. Betrag, or set to 0
    tax_values = []
    for _, row in df_clean.iterrows():
        # Try MwSt. first (percentage)
        tax_rate = row.get('MwSt.', 0)
        if pd.notna(tax_rate) and tax_rate != 0:
            tax_values.append(float(tax_rate))
        else:
            tax_values.append(0)

    standardized['Tax'] = tax_values
    
    # Add remaining columns
    standardized['Column'] = ''
    standardized['Quantity'] = 1

    # remove the last row
    standardized = standardized[:-1]
    
    value_col = df_clean.get('Zu begleichender Wert', 0)
    if value_col is not None:
        standardized['Value'] = pd.to_numeric(value_col, errors='coerce')
    else:
        standardized['Value'] = 0

    return standardized
