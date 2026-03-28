# filepath: /home/grtn/projects/fom-verkautsautomaten/scripts/data_processing/formatters/teil3_format.py
"""Teil3 format standardizer for Excel files."""

import pandas as pd
from CONSTANTS import SUPER_CATEGORY_MAP, SUPER_PAYMENT_MAP
from helpers.utils import sanitize_machine_name


def standardize_format_teil3(df):
    """Standardize Teil3 format files"""
    standardized_rows = []
    
    # Check if first row contains headers (typical for Teil3 format)
    if len(df) > 0:
        first_row = df.iloc[0].tolist()
        if any(isinstance(val, str) and any(header in str(val) for header in ['Standort-ID', 'Maschinenname', 'Produktname']) for val in first_row):
            # First row contains headers, use it to map columns
            headers = first_row
            data_start_row = 1
            
            # Create column mapping
            col_mapping = {}
            for i, header in enumerate(headers):
                if 'Maschinen-Begleichszeit' in str(header):
                    col_mapping['timestamp'] = i
                elif 'Maschinenname' in str(header):
                    col_mapping['machine'] = i
                elif 'Produktname' in str(header):
                    col_mapping['product'] = i
                elif 'Payment Method' in str(header):
                    col_mapping['payment'] = i
                elif 'Zu begleichender Wert' in str(header):
                    col_mapping['value'] = i
                elif 'Produktgruppe' in str(header):
                    col_mapping['category'] = i
        else:
            # Fallback - shouldn't happen for Teil3 format
            return pd.DataFrame()
    else:
        return pd.DataFrame()
    
    # Determine end row - exclude last row if it's a total row
    end_row = len(df)
    if len(df) > data_start_row:
        last_row = df.iloc[-1].tolist()
        # Check if last row is a total row (has 'Total' in currency column - typically column 3)
        if len(last_row) > 3 and str(last_row[3]).strip() == 'Total':
            end_row = len(df) - 1
    
    # Process data rows
    for i in range(data_start_row, end_row):
        try:
            row_data = df.iloc[i].tolist()
            
            # Extract data using column mapping
            timestamp = pd.to_datetime(row_data[col_mapping.get('timestamp', 0)], errors='coerce') if 'timestamp' in col_mapping else pd.NaT
            machine = sanitize_machine_name(str(row_data[col_mapping.get('machine', '')]).strip()) if 'machine' in col_mapping else ''
            product = str(row_data[col_mapping.get('product', '')]).strip() if 'product' in col_mapping else ''
            payment = str(row_data[col_mapping.get('payment', 'Unknown')]).strip() if 'payment' in col_mapping else 'Unknown'
            
            # Handle value conversion
            try:
                value = float(row_data[col_mapping.get('value', 0)]) if 'value' in col_mapping else 0.0
            except (ValueError, TypeError, IndexError):
                value = 0.0
            
            # Handle category
            category = str(row_data[col_mapping.get('category', '')]).strip() if 'category' in col_mapping else ''
            
            # Infer super-category from product name
            found_super = None
            for key, super_cat in SUPER_CATEGORY_MAP.items():
                if key.lower() in product.lower():
                    found_super = super_cat
                    break
            
            super_category = found_super or 'Sonstiges'
            
            # Map super-payment from payment
            super_payment = SUPER_PAYMENT_MAP.get(payment, 'unbekannt')
            
            standardized_row = {
                'Timestamp': timestamp,
                'Machine': machine,
                'Product': product,
                'Category': category,
                'Super-Category': super_category,
                'Payment': payment,
                'Super-Payment': super_payment,
                'Tax': 0,  # Default tax value
                'Column': '',  # No column info in this format
                'Quantity': 1,  # Default quantity
                'Value': value
            }
            
            standardized_rows.append(standardized_row)
            
        except Exception as e:
            print(f"Error processing row {i} in Teil3 format: {e}")
            continue
    
    return pd.DataFrame(standardized_rows)
