"""2024_06 format standardizer for Excel files."""

import pandas as pd
from CONSTANTS import SUPER_CATEGORY_MAP, SUPER_PAYMENT_MAP


def standardize_format_2024_06(df):
    """Standardize 2024_06 format files"""
    standardized = pd.DataFrame()
    
    # Convert timestamp - use existing Timestamp column
    standardized['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    
    standardized['Machine'] = df['Machine']
    standardized['Product'] = df['Product']
    
    # Use existing category if available, otherwise infer from product name
    existing_category = df.get('Category', '')
    
    category_list = []
    super_category_list = []
    
    for _, row in df.iterrows():
        product = str(row['Product']).strip()
        existing_cat = str(row.get('Category', '')).strip()
        
        # Use existing category if it's meaningful, otherwise keep empty
        if existing_cat and existing_cat.lower() not in ['category', 'nan', '']:
            category_list.append(existing_cat)
        else:
            category_list.append('')
        
        # Find matching super-category directly from product name
        found_super = None
        for key, super_cat in SUPER_CATEGORY_MAP.items():
            if key.lower() in product.lower():
                found_super = super_cat
                break
        
        # If not found from product, try from existing category
        if not found_super and existing_cat:
            found_super = SUPER_CATEGORY_MAP.get(existing_cat, None)
        
        super_category_list.append(found_super or 'Sonstiges')
    
    standardized['Category'] = category_list
    standardized['Super-Category'] = super_category_list
    
    standardized['Payment'] = df['Payment']
    
    # Map super-payment from payment
    super_payment = []
    for _, row in df.iterrows():
        payment = str(row['Payment']).strip()
        found_super = SUPER_PAYMENT_MAP.get(payment, 'unbekannt')
        super_payment.append(found_super)
    
    standardized['Super-Payment'] = super_payment
    
    # Add Tax column from Tax Rate
    standardized['Tax'] = pd.to_numeric(df.get('Tax Rate', 0), errors='coerce')
    
    standardized['Column'] = df['Column']
    standardized['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
    standardized['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    
    return standardized
