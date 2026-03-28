"""
Standard Format Standardizer

Handles files that already have the standard format (most 2024 files).
These files have columns: Timestamp, Machine, Product, Category, etc.
"""

import pandas as pd
from CONSTANTS import SUPER_CATEGORY_MAP, SUPER_PAYMENT_MAP
from helpers.utils import find_super_payment


def standardize_format_standard(df):
    """Standardize files that already have the standard format"""
    standardized = pd.DataFrame()
    
    # Map existing columns to target columns
    standardized['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    standardized['Machine'] = df['Machine']
    standardized['Product'] = df['Product']
    standardized['Category'] = df.get('Category', '')
    
    # Map super-category directly from product name or existing category
    super_category = []
    for _, row in df.iterrows():
        product = str(row.get('Product', '')).strip()
        category = str(row.get('Category', '')).strip()
        
        # First try to map from product name
        found_super = None
        for key, super_cat in SUPER_CATEGORY_MAP.items():
            if key.lower() in product.lower():
                found_super = super_cat
                break
        
        # If not found, try from category
        if not found_super:
            found_super = SUPER_CATEGORY_MAP.get(category, 'Sonstiges')
        
        super_category.append(found_super)
    
    standardized['Super-Category'] = super_category
    
    standardized['Payment'] = df.get('Payment', '')
    
    # Map super-payment directly from payment
    super_payment = []
    for _, row in df.iterrows():
        payment = str(row.get('Payment', '')).strip()
        super_payment.append(find_super_payment(payment))
    
    standardized['Super-Payment'] = super_payment
    
    # Add Tax column - extract from Tax Rate, Tax Value, or set to 0
    tax_values = []
    for _, row in df.iterrows():
        # Try Tax Rate first (percentage)
        tax_rate = row.get('Tax Rate', 0)
        if pd.notna(tax_rate) and tax_rate != 0:
            tax_values.append(float(tax_rate))
        # Try Tax Value (actual tax amount)
        elif pd.notna(row.get('Tax Value', 0)) and row.get('Tax Value', 0) != 0:
            tax_values.append(float(row.get('Tax Value', 0)))
        else:
            tax_values.append(0)
    
    standardized['Tax'] = tax_values
    
    # Add remaining columns
    standardized['Column'] = df.get('Column', '')
    standardized['Quantity'] = pd.to_numeric(df.get('Quantity', 1), errors='coerce')
    standardized['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    
    return standardized
