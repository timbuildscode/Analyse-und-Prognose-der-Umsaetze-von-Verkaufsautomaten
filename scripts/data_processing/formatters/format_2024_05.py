"""2024_05 format standardizer for Excel files."""

import pandas as pd
from CONSTANTS import SUPER_CATEGORY_MAP, SUPER_PAYMENT_MAP
from helpers.utils import sanitize_machine_name, extract_amount_and_product


def standardize_format_2024_05(df):
    """Standardize 2024_05 format files"""
    standardized_rows = []
    
    for _, row in df.iterrows():
        try:
            # Use 'Unnamed: 0' for timestamp
            timestamp = pd.to_datetime(row['Unnamed: 0'], errors='coerce')
            
            # Use 'Automat' for machine name
            machine = sanitize_machine_name(str(row['Automat']).strip())
            
            # Use 'Art' for product name
            product = str(row['Art']).strip()
            
            # Use 'Unnamed: 11' for value/amount
            try:
                amount = float(str(row['Unnamed: 13']).strip())
            except (ValueError, TypeError):
                amount = 0.0
            
            # Infer category from product name
            found_super = None
            for key, super_cat in SUPER_CATEGORY_MAP.items():
                if key.lower() in product.lower():
                    found_super = super_cat
                    break
            
            super_category = found_super or 'Sonstiges'
            
            # Payment method from 'Cash/card' column
            payment = str(row.get('Cash/card', 'Unknown')).strip()
            super_payment = SUPER_PAYMENT_MAP.get(payment, 'unbekannt')
            
            standardized_row = {
                'Timestamp': timestamp,
                'Machine': machine,
                'Product': product,
                'Category': '',  # Keep empty for this format
                'Super-Category': super_category,
                'Payment': payment,
                'Super-Payment': super_payment,
                'Tax': 0,  # Default tax value
                'Column': '',  # No column info in this format
                'Quantity': 1,  # Default quantity
                'Value': amount
            }
            
            standardized_rows.append(standardized_row)
        
        except Exception as e:
            print(f"Error processing row in 2024_05 format: {e}")
            continue
    
    return pd.DataFrame(standardized_rows)
