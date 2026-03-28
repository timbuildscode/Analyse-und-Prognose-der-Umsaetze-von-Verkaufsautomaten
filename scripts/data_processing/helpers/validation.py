import os
import pandas as pd

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
manual_validation_file = os.path.join(project_root, "data/manual data/Ergebnis_Plausibilität_Preise_gekürzt.xlsx")

def validate_product_prices(processed_df):
    """
    Validate product-price combinations against manual validation file.
    Mark invalid combinations as 'unknown' product.
    
    Args:
        processed_df: DataFrame with Product and Value columns
        
    Returns:
        DataFrame with validated products
    """
    print("Starting product price validation...")
    
    # Check if validation file exists
    if not os.path.exists(manual_validation_file):
        print(f"Warning: Manual validation file not found at {manual_validation_file}")
        print("Skipping validation - products will remain as-is")
        return processed_df
    
    try:
        # Load validation data
        validation_df = pd.read_excel(manual_validation_file)
        print(f"Loaded validation data with {len(validation_df)} entries")
        
        # Process the validation logic
        try:
            # Create a copy of the processed dataframe to avoid modifying the original
            validated_df = processed_df.copy()
            
            # Print column names to understand the structure
            print("Validation dataframe columns:")
            print(validation_df.columns.tolist())
            print("\nProcessed dataframe columns:")
            print(processed_df.columns.tolist())
            
            # Identify the column names in the validation dataframe
            # Look for relevant columns based on their content rather than names
            product_col = 'Product'  # Default column name
            price_col = 'Value'      # Default column name
            validation_col = None    # Will be determined below
            
            # Find the validation column - looking for columns containing 'Plausi' or 'Prüfung'
            validation_cols = [col for col in validation_df.columns if 'manuelle' in col.lower() and 'prüfung' in col.lower()]
            if validation_cols:
                validation_col = validation_cols[0]
            else:
                validation_cols = [col for col in validation_df.columns if 'plausi' in col.lower()]
                if validation_cols:
                    validation_col = validation_cols[0]
            
            print(f"Using column '{validation_col}' for validation status")
            
            # If we couldn't find a validation column, exit gracefully
            if validation_col is None:
                print("Could not identify a validation column in the validation dataframe.")
                print("Available columns:", validation_df.columns.tolist())
                raise ValueError("No validation column found")
            
            # Create a combination key of product and price in both dataframes
            validation_df['ProductPriceKey'] = validation_df[product_col] + '|' + validation_df[price_col].astype(str)
            validated_df['ProductPriceKey'] = validated_df['Product'] + '|' + validated_df['Value'].astype(str)
            
            # Create a dictionary of product-price combinations and their validation status
            # Check if the validation status indicates the product is not plausible
            validation_dict = {}
            for _, row in validation_df.iterrows():
                key = row['ProductPriceKey']
                # Mark as invalid if validation contains 'nicht plausibel'
                is_invalid = 'nicht plausibel' in str(row[validation_col]).lower()
                validation_dict[key] = is_invalid
            
            print(f"Created validation dictionary with {len(validation_dict)} entries")
            
            # Function to check if a product-price combination is valid
            def validate_product(row):
                key = row['ProductPriceKey']
                # Return True if the product-price combination is marked as invalid
                return validation_dict.get(key, False)
            
            # Mark products for replacement
            validated_df['replace_product'] = validated_df.apply(validate_product, axis=1)

            # Count rows before replacement
            original_rows = len(validated_df)
            invalid_count = validated_df['replace_product'].sum()

            # Create a copy of invalid entries before modification for saving
            if invalid_count > 0:
                invalid_products = validated_df[validated_df['replace_product']].copy()
                
                # Save original invalid entries to separate file
                interim_dir = os.path.join(project_root, "data/interim")
                invalid_file_path = os.path.join(interim_dir, "invalid_product_price_combinations.xlsx")
                
                try:
                    invalid_products.to_excel(invalid_file_path, index=False)
                    print(f"  → Saved {len(invalid_products)} invalid entries to: invalid_product_price_combinations.xlsx")
                except Exception as save_error:
                    print(f"  Warning: Could not save invalid entries file: {save_error}")

            # Replace product and category names with 'Unknown' where validation failed
            validated_df.loc[validated_df['replace_product'], 'Product'] = 'Unknown'
            validated_df.loc[validated_df['replace_product'], 'Category'] = 'Unknown'
            validated_df.loc[validated_df['replace_product'], 'Super-Category'] = 'Unknown'

            # Remove temporary columns
            validated_df.drop(columns=['ProductPriceKey', 'replace_product'], inplace=True)

            # Display results
            print("Validation results:")
            print(f"  Total dataset rows: {original_rows}")
            print(f"  Invalid products renamed to 'Unknown': {invalid_count}")
            print(f"  Valid products remaining unchanged: {original_rows - invalid_count}")

            # Show sample of replaced products
            if invalid_count > 0:
                print("Sample of products renamed to 'Unknown':")
                sample_unknown = validated_df[validated_df['Product'] == 'Unknown'].head(3)
                for _, row in sample_unknown.iterrows():
                    print(f"  Unknown - €{row['Value']} (from {row['SourceFile']})")

            return validated_df
            
        except Exception as e:
            print(f"Error during validation process: {e}")
            print("Consider printing more information about the dataframes:")
            print("Validation DataFrame Info:")
            if 'validation_df' in locals():
                print(validation_df.info())
            return processed_df
            
    except Exception as e:
        print(f"Error loading validation file: {e}")
        print("Skipping validation - products will remain as-is")
        return processed_df