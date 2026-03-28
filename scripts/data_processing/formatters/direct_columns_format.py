"""Direct columns format standardizer for Excel files."""

import pandas as pd
from CONSTANTS import SUPER_CATEGORY_MAP, SUPER_PAYMENT_MAP


def standardize_format_direct_columns(df):
    """Standardize files that already have the standardized column format"""
    standardized = pd.DataFrame()
    
    # Direct column mapping - these files already have the correct structure
    standardized['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    standardized['Machine'] = df['Machine']
    standardized['Product'] = df['Product']
    standardized['Category'] = df.get('Category', '')
    
    # Handle super-category - if not present, infer from product
    if 'Super-Category' in df.columns:
        standardized['Super-Category'] = df['Super-Category']
    else:
        # Infer from product name
        super_category_list = []
        for _, row in df.iterrows():
            product = str(row['Product']).strip()
            
            # Find matching super-category from product name
            found_super = None
            for key, super_cat in SUPER_CATEGORY_MAP.items():
                if key.lower() in product.lower():
                    found_super = super_cat
                    break
            
            super_category_list.append(found_super or 'Sonstiges')
        
        standardized['Super-Category'] = super_category_list
    
    standardized['Payment'] = df.get('Payment', 'Unknown')
    
    # Handle super-payment - if not present, derive from payment
    if 'Super-Payment' in df.columns:
        standardized['Super-Payment'] = df['Super-Payment']
    else:
        super_payment = []
        for _, row in standardized.iterrows():
            payment = str(row['Payment']).strip()
            found_super = SUPER_PAYMENT_MAP.get(payment, 'unbekannt')
            super_payment.append(found_super)
        
        standardized['Super-Payment'] = super_payment
    
    standardized['Tax'] = pd.to_numeric(df.get('Tax', 0), errors='coerce')
    standardized['Column'] = df.get('Column', '')
    standardized['Quantity'] = pd.to_numeric(df.get('Quantity', 1), errors='coerce')
    standardized['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    
    return standardized
