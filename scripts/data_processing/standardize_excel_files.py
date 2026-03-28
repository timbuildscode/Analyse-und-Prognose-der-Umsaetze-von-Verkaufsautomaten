#!/usr/bin/env python3
"""
Excel File Standardization Script

This script standardizes all Excel files in the raw data directory to have
a consistent column structure that matches the target format.

Target columns: ['Timestamp', 'Machine', 'Product', 'Category', 'Super-Category', 'Payment', 'Super-Payment', 'Tax', 'Column', 'Quantity', 'Value']
"""

import pandas as pd
import os
import warnings
from helpers.helpers import process_file
from helpers.validation import validate_product_prices
from helpers.imputing import impute_missing_sales
from helpers.utils import addColumnWeekDayOrHoliday, cleanProductNames, mapUnknownProductsByValue, update_super_categories
from helpers.sales_trend import plot_sales_trend

warnings.filterwarnings('ignore')

# Define paths
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
raw_data_path = os.path.join(project_root, "data/raw")
interim_data_path = os.path.join(project_root, "data/interim")
os.makedirs(interim_data_path, exist_ok=True)

def main():
    """Main function to process all Excel files"""
    print("Starting Excel file standardization...")
    print(f"Raw data directory: {raw_data_path}")
    print(f"Interim data directory: {interim_data_path}")
    
    # Get all Excel files
    excel_files = [f for f in os.listdir(raw_data_path) 
                   if f.endswith('.xlsx')]
    
    print(f"Found {len(excel_files)} Excel files to process")
    
    all_standardized = []
    processed_count = 0
    
    for filename in sorted(excel_files):
        filepath = os.path.join(raw_data_path, filename)
        standardized_df = process_file(filepath)
        
        if standardized_df is not None and len(standardized_df) > 0:
            all_standardized.append(standardized_df)
            processed_count += 1
            
            # Save individual standardized file
            output_filename = f"standardized_{filename}"
            output_path = os.path.join(interim_data_path, output_filename)
            standardized_df.to_excel(output_path, index=False)
            print(f"  → Saved to {output_filename}")
    
    # Combine all standardized files
    if all_standardized:
        combined_df = pd.concat(all_standardized, ignore_index=True)
        
        final_rows = len(combined_df)
        
        print(f"\nCombined dataset:")
        print(f"  Total rows: {final_rows}")
        print(f"  Date range: {combined_df['Timestamp'].min()} to {combined_df['Timestamp'].max()}")
        print(f"  Total value: {combined_df['Value'].sum():.2f}")
        
        # Apply product price validation
        combined_df = validate_product_prices(combined_df)

        # Apply product name cleaning and category standardization
        print("\nCleaning product names and categories...")
        combined_df = cleanProductNames(combined_df, output_analysis=True)

        combined_df = mapUnknownProductsByValue(combined_df)
        combined_df = update_super_categories(combined_df)



        combined_df = impute_missing_sales(
            combined_df, 
            min_gap_days=4, 
            reference_weeks=3, 
            imputation_probability=0.5,
            random_seed=42
        )
        combined_df = addColumnWeekDayOrHoliday(combined_df)
        

        # Save combined file
        combined_output = os.path.join(interim_data_path, "all_standardized_combined.xlsx")
        combined_df.to_excel(combined_output, index=False)
        print(f"  → Saved combined data to all_standardized_combined.xlsx")
        
        # Save validated file with different name
        validated_output = os.path.join(interim_data_path, "all_standardized_validated.xlsx")
        combined_df.to_excel(validated_output, index=False)
        print(f"  → Saved validated data to all_standardized_validated.xlsx")
        
        # Display sample
        print(f"\nSample of standardized data:")
        print("Columns:", list(combined_df.columns))
        print("First 3 rows:")
        for i, row in combined_df.head(3).iterrows():
            print(f"Row {i}:")
            for col in combined_df.columns[:11]:  # Show only target columns
                print(f"  {col}: {row[col]}")
            print()
        
    else:
        print("No files were successfully processed.")
    
    print(f"\nProcessing complete! Successfully processed {processed_count}/{len(excel_files)} files.")

if __name__ == "__main__":
    main()