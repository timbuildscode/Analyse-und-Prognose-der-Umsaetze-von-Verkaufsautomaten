"""Clean 2022_12 format standardizer for Excel files."""

import pandas as pd
from CONSTANTS import SUPER_CATEGORY_MAP, SUPER_PAYMENT_MAP


def standardize_format_clean2022_12(df):
    """Standardize clean 2022_12 format files"""
    standardized = pd.DataFrame()
    
    # Convert timestamp - this format uses 'Date' column
    standardized['Timestamp'] = pd.to_datetime(df['Date'], errors='coerce')
    
    standardized['Machine'] = df['Machine']
    
    # Define products that should be treated as categories
    category_products = {
        'Softdrinks': 'Softdrinks',
        'Snacks süß': 'Snacks',
        'Gummibärchen': 'Gummibärchen'
    }
    
    # Handle Product and Category mapping
    product_list = []
    category_list = []
    
    for _, row in df.iterrows():
        original_product = str(row['Product']).strip()
        original_category = str(row.get('Category', '')).strip()
        
        # Check if the product is actually a category
        if original_product in category_products:
            # Move product to category and set product as Unknown
            product_list.append('Unknown')
            category_list.append(category_products[original_product])
        else:
            # Keep original product and category
            product_list.append(original_product)
            category_list.append(original_category if original_category else '')
    
    standardized['Product'] = product_list
    standardized['Category'] = category_list
    
    if 'Super-Category' in df.columns and not df['Super-Category'].isna().all():
        standardized['Super-Category'] = df['Super-Category']
    else:
        # Infer from product name if not available
        super_category_list = []
        for i, row in df.iterrows():
            original_product = str(row['Product']).strip()
            
            # Check if product was moved to category
            if original_product in category_products:
                # Use the mapped category for super-category logic
                category_name = category_products[original_product]
                
                # Map category to super-category
                if category_name == 'Softdrinks':
                    found_super = 'Getränke'
                elif category_name == 'Snacks':
                    found_super = 'Snacks'
                elif category_name == 'Gummibärchen':
                    found_super = 'Snacks'
                else:
                    found_super = 'Sonstiges'
            else:
                # Find matching super-category from product name
                found_super = None
                for key, super_cat in SUPER_CATEGORY_MAP.items():
                    if key.lower() in original_product.lower():
                        found_super = super_cat
                        break
                
                if not found_super:
                    found_super = 'Sonstiges'
            
            super_category_list.append(found_super)
        
        standardized['Super-Category'] = super_category_list
    
    # Handle payment
    standardized['Payment'] = df.get('Payment', 'Unknown')
    
    # Handle super-payment
    if 'Super-Payment' in df.columns and not df['Super-Payment'].isna().all():
        standardized['Super-Payment'] = df['Super-Payment']
    else:
        super_payment = []
        for _, row in standardized.iterrows():
            payment = str(row['Payment']).strip()
            found_super = SUPER_PAYMENT_MAP.get(payment, 'unbekannt')
            super_payment.append(found_super)
        
        standardized['Super-Payment'] = super_payment
    
    # Handle remaining columns
    standardized['Tax'] = pd.to_numeric(df.get('Tax', 0), errors='coerce')
    standardized['Column'] = df.get('Column', '')
    standardized['Quantity'] = pd.to_numeric(df.get('Quantity', 1), errors='coerce')
    standardized['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    
    return standardized
