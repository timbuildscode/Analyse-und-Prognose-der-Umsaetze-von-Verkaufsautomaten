import pandas as pd
from datetime import timedelta, datetime, time
import random


def impute_missing_sales(df, min_gap_days=4, reference_weeks=3, imputation_probability=0.5, random_seed=42):
    """
    Impute missing sales data for periods with no sales activity.
    
    Args:
        df: DataFrame with sales data containing 'Timestamp', 'Value', and other sales columns
        min_gap_days: Minimum number of consecutive days without sales to consider for imputation
        reference_weeks: Number of weeks before/after to use as reference for imputation
        imputation_probability: Probability of including each reference sale in imputation
        random_seed: Random seed for reproducible results (default: 42)
        
    Returns:
        DataFrame with imputed sales data combined with original data
    """
    # Set random seed for reproducible results
    random.seed(random_seed)
    
    # Create a copy to avoid modifying the original
    df = df.copy()
    
    # Ensure Timestamp is datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    # Vollständiger Datumsbereich
    full_dates = pd.date_range(df['Timestamp'].min(), df['Timestamp'].max(), freq='D')

    # Tagesumsatz aggregieren
    daily_sales = df.groupby(df['Timestamp'].dt.date)['Value'].sum()
    daily_sales = daily_sales.reindex(full_dates.date, fill_value=0)

    # Maske: True = kein Verkauf (NaN oder 0)
    no_sales_mask = daily_sales == 0

    # Funktion zur Lückenerkennung
    def find_long_no_sales_periods(mask, min_days=min_gap_days):
        gaps = []
        gap_start = None
        for i, val in enumerate(mask):
            if val:
                if gap_start is None:
                    gap_start = i
            else:
                if gap_start is not None:
                    gap_end = i - 1
                    if (gap_end - gap_start + 1) >= min_days:
                        gaps.append((full_dates[gap_start], full_dates[gap_end]))
                    gap_start = None
        if gap_start is not None:
            gap_end = len(mask) - 1
            if (gap_end - gap_start + 1) >= min_days:
                gaps.append((full_dates[gap_start], full_dates[gap_end]))
        return gaps

    # Lücken mit mind. min_gap_days Tagen ohne Verkäufe
    no_sales_periods = find_long_no_sales_periods(no_sales_mask.values)
    print(f"Zeiträume mit mind. {min_gap_days} Tagen ohne Verkäufe:")
    for start, end in no_sales_periods:
        print(f"Von {start.date()} bis {end.date()}")

    imputed_rows = []

    for start, end in no_sales_periods:
        # Für jeden Tag in der Lücke
        current_date = start
        while current_date <= end:
            # Referenztage bestimmen (reference_weeks Wochen davor und danach)
            before_date = current_date - timedelta(weeks=reference_weeks)
            after_date = current_date + timedelta(weeks=reference_weeks)

            # Verkäufe der Referenztage sammeln
            reference_sales = df[
                ((df['Timestamp'].dt.date == before_date.date()) | 
                 (df['Timestamp'].dt.date == after_date.date()))
            ].copy()

            # Wenn Referenzverkäufe vorhanden sind
            if not reference_sales.empty:
                # Jeden zweiten Eintrag der Referenzliste nehmen
                for idx in range(0, len(reference_sales)):
                    if random.random() < imputation_probability:  # Wahrscheinlichkeit für jeden Eintrag
                        selected_sale = reference_sales.iloc[idx]
                        
                        # Neuen Timestamp erstellen mit Datum des Lückentags und Uhrzeit des Referenzverkaufs
                        new_timestamp = datetime.combine(
                            current_date.date(),
                            selected_sale['Timestamp'].time()
                        )
                        
                        # Verkauf zur Liste hinzufügen
                        imputed_rows.append({
                            'Timestamp': new_timestamp,
                            'Product': selected_sale['Product'],
                            'Category': selected_sale['Category'],
                            'Value': selected_sale['Value'],
                            'Payment': selected_sale['Payment'],
                            'Machine': selected_sale['Machine'],
                            'Tax': selected_sale.get('Tax', 0),
                            'Column': selected_sale.get('Column', ''),
                            'Quantity': selected_sale.get('Quantity', 1),
                            'Super-Category': selected_sale.get('Super-Category', ''),
                            'Super-Payment': selected_sale.get('Super-Payment', ''),
                            'SourceFile': selected_sale.get('SourceFile', 'imputed')
                        })
            
            current_date += timedelta(days=1)

    # Imputierte Zeilen als DataFrame erstellen
    df_imputed = pd.DataFrame(imputed_rows)

    # Originales DataFrame mit imputierten Werten zusammenführen
    df_combined = pd.concat([df, df_imputed], ignore_index=True)

    # Nach Timestamp sortieren
    df_combined = df_combined.sort_values('Timestamp')
    
    print(f"Imputed {len(imputed_rows)} sales records for {len(no_sales_periods)} gap periods.")
    
    return df_combined