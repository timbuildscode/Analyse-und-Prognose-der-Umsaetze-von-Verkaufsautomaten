"""
Utility functions for data processing

This module contains utility functions that are used by formatters and other modules.
These functions are separated to avoid circular imports.
"""

import pandas as pd
from CONSTANTS import SUPER_CATEGORY_MAP, SUPER_PAYMENT_MAP, FEIERTAGE, SCHULFERIEN, VORLESUNGSZEITEN

def safe_str(value):
    """Safely convert a value to string, handling NaN and None"""
    if pd.isna(value) or value is None:
        return ''
    return str(value).strip()


def find_super_category(product, category):
    """Safely find super category from product or category"""
    product_str = safe_str(product)
    category_str = safe_str(category)
    
    # First try to map from product name
    if product_str:
        for key, super_cat in SUPER_CATEGORY_MAP.items():
            if key.lower() in product_str.lower():
                return super_cat
    
    # If not found, try from category
    if category_str:
        for key, super_cat in SUPER_CATEGORY_MAP.items():
            if key.lower() in category_str.lower():
                return super_cat
        # Direct lookup for exact matches
        return SUPER_CATEGORY_MAP.get(category_str, 'Sonstiges')
    
    return 'Sonstiges'


def find_super_payment(payment):
    """Safely find super payment from payment method"""
    payment_str = safe_str(payment)
    
    if payment_str:
        for key, super_pay in SUPER_PAYMENT_MAP.items():
            if key.lower() in payment_str.lower():
                return super_pay
    
    return 'unbekannt'


def sanitize_machine_name(machine_name):
    """Sanitize machine name to handle encoding issues"""
    if pd.isna(machine_name):
        return 'Unknown'
    
    machine_str = str(machine_name).strip()
    if not machine_str:
        return 'Unknown'
    
    # Handle specific encoding issues
    machine_str = machine_str.replace('Ã¼', 'ü')  # Replace specific encoding for ü
    machine_str = machine_str.replace('Ã¤', 'ä')  # Replace specific encoding for ä
    machine_str = machine_str.replace('Ã¶', 'ö')  # Replace specific encoding for ö
    machine_str = machine_str.replace('ÃŸ', 'ß')  # Replace specific encoding for ß
    
    return machine_str


def extract_amount_and_product(product_string):
    """Extract amount and clean product name from product string"""
    if pd.isna(product_string):
        return 1, 'Unknown'
    
    product_str = str(product_string).strip()
    if not product_str:
        return 1, 'Unknown'
    
    # Simple extraction - look for patterns like "2x Product Name"
    import re
    match = re.match(r'(\d+)x?\s*(.+)', product_str, re.IGNORECASE)
    if match:
        amount = int(match.group(1))
        product = match.group(2).strip()
        return amount, product
    
    # Default case - no amount found
    return 1, product_str


def clean_for_mapping(text):
    """Clean text for consistent mapping by removing spaces and lowercasing"""
    if pd.isna(text):
        return ''
    return str(text).lower().replace(' ', '').strip()


def addColumnWeekDayOrHoliday(df):
    """
    Add Holiday and Weekday columns to DataFrame based on Timestamp column.
    
    Args:
        df: DataFrame with 'Timestamp' column
        
    Returns:
        DataFrame with added 'Holiday' and 'Weekday' columns
    """
    import pandas as pd
    from datetime import datetime
    
    # Create a copy to avoid modifying the original
    df = df.copy()
        
    # Convert to datetime objects
    feiertage_dt = [datetime.strptime(tag, '%d.%m.%Y').date() for tag in FEIERTAGE]
    
    # Ensure Timestamp column is datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # Add Holiday column
    df['Public_Holiday'] = df['Timestamp'].dt.date.isin(feiertage_dt)
    
    # Schulferien in datetime umwandeln
    ferien_dateranges = [
        (datetime.strptime(start, '%d.%m.%Y').date(), datetime.strptime(ende, '%d.%m.%Y').date())
        for start, ende in SCHULFERIEN
    ]

    # Schulferien-Spalte
    def ist_ferien_tag(datum):
        return any(start <= datum <= ende for start, ende in ferien_dateranges)

    df['School_Holidays'] = df['Timestamp'].dt.date.apply(ist_ferien_tag)

    # Vorlesungszeiten in datetime umwandeln
    vorlesungszeiten_dateranges = [
        (datetime.strptime(start, '%d.%m.%Y').date(), datetime.strptime(ende, '%d.%m.%Y').date())
        for start, ende in VORLESUNGSZEITEN
    ]

    # Semesterpause-Spalte
    def ist_vorlesungsfreier_tag(datum):
        return not any(start <= datum <= ende for start, ende in vorlesungszeiten_dateranges)

    # Anwendung auf DataFrame
    df['semester_break'] = df['Timestamp'].dt.date.apply(ist_vorlesungsfreier_tag)

    # Add Weekday column - try German locale first, fallback to English
    try:
        df['Weekday'] = df['Timestamp'].dt.day_name(locale='de_DE')
    except:
        # Fallback to English if German locale is not available
        df['Weekday'] = df['Timestamp'].dt.day_name()
    
    print(f"Added Holiday and Weekday columns to {len(df)} rows")
    print(f"Holidays found: {df['Public_Holiday'].sum()} entries")
    
    return df

def cleanProductNames(df, product_col='Product', category_col='Category', output_analysis=False):
    """
    Comprehensive product name cleaning with fuzzy matching and category standardization.
    
    Args:
        df: DataFrame with product data
        product_col: Column name for products (default: 'Product')
        category_col: Column name for categories (default: 'Category')
        output_analysis: Whether to generate analysis files (default: False)
        
    Returns:
        DataFrame with cleaned product names and categories
    """
    print(f"Starting product name cleaning for {len(df)} rows...")
    
    # Import fuzzywuzzy only when needed
    try:
        from fuzzywuzzy import process
    except ImportError:
        print("Warning: fuzzywuzzy not available. Install with: pip install fuzzywuzzy python-Levenshtein")
        print("Proceeding with basic product mapping only...")
        process = None
    
    # Product name mapping dictionary
    PRODUCTNAME_MAPPING = {
        'Astra o,33': 'Astra 0,33',
        'Astra': 'Astra 0,33',
        'Bier ': 'Bier',
        'Buldak': 'Buldak Carbon\'lara Ramen',
        'Chai 0.33 DPG': 'Chai 0,33',
        'Funny Frish Chipsfrischungarisch 40g': 'Chips Ungarisch',
        'capri Sonne':'Capri Sonne',
        'CocaCola': 'Coca Cola 0,33',
        'Cola 0,33 DPG': 'Coca Cola 0,33',
        'Cola Oreo': 'Coca Cola Oreo',
        'Center Shocks':'Center Shock',
        'Choko Bong Crispy': 'Kinder Schoko Bons Crispy 89g',
        'Drachenzungen': 'Drachenzungen Hitschler',
        'Durstlöscher 0,5l':'Durstlöscher 0,5',
        'e- zigarette':'E-Zigarette',
        'ElfBar ': 'ElfBar',
        'Fanta': 'Fanta 0,33',
        'Fanta 0,33 DPG': 'Fanta 0,33',
        'Fanta Berry/ Mountain Dew': 'Fanta Blau 0,33',
        'Fanta Blau 0,33 DPG': 'Fanta Blau 0,33',
        'Fanta Exotic DPG': 'Fanta Exotic',
        'Fanta Golden Grape 500ml': 'Fanta Grape Japan',
        'Fanta Grape': 'Fanta Grape Japan',
        'Golden Grape Japan': 'Fanta Grape Japan',
        'Fanta Mango Drachefrucht': 'Fanta Mango Drachenfrucht',
        'Fanta White Peach China 500ml': 'Fanta White Peach',
        'Fanta 0.33 Special':'Fanta 0,33 Special',
        'Fanta Pink 0,33 DPG':'Fanta Pink 0,33',
        'Flick\'n Lick Lolli': 'Flick\'n Lick',
        'Giotto 2x5': 'Giotto',
        'Gum Powder':'ZED GUM Powder',
        'Haribo Goldbären 100g': 'Haribo',
        'Haribo Pommes Sauer100g': 'Haribo Pommes Sauer 100g',
        'Haribo sauer': 'Haribo Pommes Sauer 100g',
        'Heineken 250ml': 'Heineken 0,25',
        'Heineken 0,25 Flasche': 'Heineken 0,25',
        'Jelly Stick': 'Jelly Strip 300g',
        'Jelly Stripe': 'Jelly Strip 300g',
        'Kakao ': 'Kakao Bärenmarke',
        'Kakao': 'Kakao Bärenmarke',
        'KitKat normal': 'KitKat',
        'Krombacher 0.5':'Krombacher 0,5',
        'M&M\'s Cookies': 'M&M\'s Cookies',
        'Marmor Kuchen': 'Marmorkuchen Küchenmeister',
        'Mezzo Mix 0,33 DPG':'Mezzo Mix 0,33',
        'Nerds 141 g': 'Nerds rope',
        'ogeez': 'Ogeez',
        'Redbull': 'Red Bull 0,25',
        'Redbull Aprikose Erdbeere': 'Red Bull Aprikose Erdbeere',
        'Red Bull Blueberry': 'Red Bull Blaubeere',
        'Red Bull Peach': 'Red Bull Pfirsich',
        'RedBull Pfirsich': 'Red Bull Pfirsich',
        'RedBull 0.25': 'Red Bull 0,25',
        'Redbull 0,25': 'Red Bull 0,25',
        'Redbull Original': 'Red Bull 0,25',
        'Redbull/Bier ': 'Red Bull 0,25',
        'Redbull/Bier': 'Red Bull 0,25',
        'Redbull Juneberry': 'Red Bull Juneberry',
        'Redbull ': 'Red Bull 0,25',
        'Rocket Balls Brausebälle\nErdbeer sauer':'Rocket Balls Brausebälle Erdbeer sauer',
        'Apfel Feige': 'Red Bull Apfel Feige',
        'Rocket Balls BrausebälleErdbeer sauer': 'Rocket Balls Brausebälle Erdbeer sauer',
        'Schoko Bons Chrispy 66,7gr': 'Schoko Bons Crispy 67,2g',
        'Schoo Bons Crispy 67,2gr': 'Schoko Bons Crispy 67,2g',
        'Swizzels Double Dip\nOrange & Cherry':'Swizzels Double Dip Orange & Cherry',
        'Skittles Tüte': 'Skittles',
        'Snickers cooie dough': 'Snickers Cockie Dough',
        'Sour Madness Crush': 'Sour Madness Crush 60g',
        'Sour Patch Kids 140g': 'Sour Patch',
        'Sour Patch Watermelon 99g': 'Sour Patch',
        'Sour Patch Watermelon 99g / Sour Patch Kids 140g': 'Sour Patch',
        'Spezi DPG': 'Spezi',
        'Sprite 0,33 DPG': 'Sprite 0,33',
        'Sprite': 'Sprite 0,33',
        'Swizzels Double DipOrange & Cherry': 'Swizzels Double Dip Orange & Cherry',
        'Takis': 'Takis 28,4 g',
        'Takis Blue Head': 'Takis Blue Heat 28,4g',
        'Takis Blue Heat 28,4 Gramm': 'Takis Blue Heat 28,4g',
        'Takis Fuego 56 Gramm': 'Takis Fuego 56g',
        'Takis Fuego 56 gramm': 'Takis Fuego 56g',
        'Twix': 'Twix 50g',
        'Warheads': 'Warheads Drink 0,33',
        'WarHeads Drink 0.33': 'WarHeads Drink 0,33',
        'Whisky Cola Dose': 'Whisky-Cola',
        'WhiskyCola': 'Whisky-Cola',
        'fresh Fruit Softdrink': 'Fresh Fruit Softdrink',
        'herr\'s Carolina Reaser': 'Herr\'s Carolina Reaser',
        'jelly Strip 300g': 'Jelly Strip 300g',
        'China Fanta 0.33': 'China Fanta 0,33',
        'Product':'Unknown'
    }
    
    # Category name mapping dictionary
    CATEGORYNAME_MAPPING = {
        'Bier ': 'Bier',
        'Elfbar': 'ElfBar',
        'ElfBar ': 'ElfBar',
        'Gummibärchen ': 'Gummibärchen',
        'Kakao ': 'Kakao',
        'Redbull ': 'Red Bull',
        'Redbull': 'Red Bull',
        'Redbull/Bier ': 'Red Bull',
        'Snacks salzig': 'Snacks',
        'Snacks süß': 'Snacks',
        'Softdrinks ': 'Softdrinks',
    }
    
    # Product-specific category mapping
    PRODUCT_CATEGORY_MAPPING = {
        'Buldak Carbon\'lara Ramen': 'Snacks',
        'Bier':'Bier',
        'Chocomel': 'Milchgetränke',
        'Drachenzungen Hitschler': 'Snacks',
        'Gummibärchen': 'Snacks',
        'E-Zigarette': 'Vapes',
        'Haribo': 'Snacks',
        'Haribo Pommes Sauer 100g': 'Snacks',
        'Kakao Bärenmarke': 'Milchgetränke',
        'Red Bull 0,25': 'Red Bull',
        'Whisky-Cola': 'Mixgetränke',
        'Dr. Sour Gummies': 'Snacks',
        '187 Vape': 'Vapes',
        'ElfBar': 'Vapes',
        'condome': 'Non-Food',
        'Keks': 'Snacks',
        'Booster': 'Softdrinks',
        'Zunder Zahnstocher': 'Non-Food',
        'Vape': 'Vapes',
        'Gemüsesuppe mit Croutons': 'Food',
        'Knorr Hühnersuppe': 'Food',
        'Knorr Gulaschsuppe': 'Food',
        'Tomatensuppe': 'Food',
        'Burdak Carbo': 'Food',
        'Baklava': 'Food',
        'Lion Brownie': 'Snacks',
        'Gum Powder': 'Snacks',
        'Damak': 'Snacks',
        'Hubba Bubba':'Snacks',
        'Balls': 'Snacks',
        'Jake Carrots 100g': 'Snacks',
        'Fini Roller Fizz Erdbeere 20g': 'Snacks',
        'Hot Banger': 'Snacks',
        'Takis Hot Liquid Pickle': 'Snacks',
        'M&M\'s Cookies':'Snacks',
        'Schmorwurst 4er': 'Food',
        'Nackensteaks Las Vegas 4er':'Food',
        'Pizzagriller 4er': 'Food',
        'DingDong':'Snacks',
        'Pepsi':'Softdrinks'
    }
    
    # Pattern-based category mapping
    PATTERN_CATEGORY_MAPPING = {
        'Cola': 'Coca Cola',
        'Fanta': 'Fanta', 
        'Sprite': 'Sprite',
        'Kinder': 'Kinder'
    }
    
    # Create working copy
    df_cleaned = df.copy()
    
    # Step 1: Apply product name mapping
    print("→ Applying product name standardization...")
    df_cleaned[f'{product_col}_clean'] = df_cleaned[product_col].map(PRODUCTNAME_MAPPING).fillna(df_cleaned[product_col])
    mapped_count = len(df_cleaned[df_cleaned[f'{product_col}_clean'] != df_cleaned[product_col]])
    print(f"  Standardized {mapped_count} product names")
    
    # Step 2: Apply base category mapping
    print("→ Applying category standardization...")
    df_cleaned[f'{category_col}_clean'] = df_cleaned[category_col].map(CATEGORYNAME_MAPPING).fillna(df_cleaned[category_col])
    
    # Step 3: Apply pattern-based category mapping
    print("→ Applying pattern-based category mapping...")
    for search_term, new_category in PATTERN_CATEGORY_MAPPING.items():
        mask = df_cleaned[f'{product_col}_clean'].str.contains(search_term, case=False, na=False)
        df_cleaned.loc[mask, f'{category_col}_clean'] = new_category
    
    # Step 4: Apply product-specific category mapping
    print("→ Applying product-specific category mapping...")
    for product_name, new_category in PRODUCT_CATEGORY_MAPPING.items():
        mask = df_cleaned[f'{product_col}_clean'] == product_name
        df_cleaned.loc[mask, f'{category_col}_clean'] = new_category
    
    # Step 5: Fill empty categories based on product history
    print("→ Filling empty categories...")
    empty_mask = (df_cleaned[f'{category_col}_clean'].isna() | 
                  (df_cleaned[f'{category_col}_clean'] == '') | 
                  (df_cleaned[f'{category_col}_clean'].str.strip() == ''))
    
    if empty_mask.any():
        product_categories = (df_cleaned[~empty_mask]
                         .groupby(f'{product_col}_clean')[f'{category_col}_clean']
                         .first()
                         .to_dict())
        df_cleaned.loc[empty_mask, f'{category_col}_clean'] = df_cleaned.loc[empty_mask, f'{product_col}_clean'].map(product_categories)
    
    # Generate analysis if requested and fuzzywuzzy is available
    # if output_analysis and process is not None:
    #     print("→ Generating similarity analysis...")
    #     _generate_similarity_analysis(df_cleaned, f'{product_col}_clean', f'{category_col}_clean', process)
    
    # Update original columns
    df_cleaned[product_col] = df_cleaned[f'{product_col}_clean']
    df_cleaned[category_col] = df_cleaned[f'{category_col}_clean']
    
    # Drop temporary columns
    df_cleaned = df_cleaned.drop(columns=[f'{product_col}_clean', f'{category_col}_clean'])
    
    print(f"✓ Product name cleaning completed for {len(df_cleaned)} rows")
    print(f"  Unique products: {df_cleaned[product_col].nunique()}")
    print(f"  Unique categories: {df_cleaned[category_col].nunique()}")
    
    return df_cleaned


def update_super_categories(df):
    """
    Updates the Super-Category column in the DataFrame based on the category mapping.
    
    Args:
        df: DataFrame with Category and Super-Category columns
        
    Returns:
        DataFrame with updated Super-Category column
    """

    SUPER_CATEGORY_MAPPING = {
        'Vapes': 'Vapes',
        'Non-Food': 'Sonstiges',
        'Softdrinks': 'Getränke',
        'Food':'Essen & Snacks',
        'Snacks': 'Essen & Snacks',
        'Kinder': 'Essen & Snacks',
        'Unknown': 'Uknown',
        'Red Bull': 'Getränke',
        'Bier': 'Getränke',
        'Fanta': 'Getränke',
        'Milchgetränke': 'Getränke',
        'Mixgetränke': 'Getränke',
    }
    # Create a copy to avoid modifying the original
    df_updated = df.copy()
    
    # Get the category to super category mapping from the global variable
    category_super_map = SUPER_CATEGORY_MAPPING
    
    # Track changes for reporting
    changes_made = {}
    
    # Update super categories based on the mapping
    for category, super_category in category_super_map.items():
        # Find rows with matching category
        mask = df_updated['Category'] == category
        affected_rows = mask.sum()
        
        if affected_rows > 0:
            # Apply the mapping
            df_updated.loc[mask, 'Super-Category'] = super_category
            
            # Track changes
            changes_made[category] = {
                'count': affected_rows,
                'super_category': super_category
            }
    
    # Print results
    print("Super-Category Update Results:")
    print("=" * 50)
    
    if changes_made:
        for category, info in changes_made.items():
            print(f"Category '{category}': {info['count']} rows mapped to '{info['super_category']}'")
    else:
        print("No categories were mapped to super categories.")
    
    # Show remaining unmapped categories
    unmapped = df_updated[df_updated['Super-Category'].isna()]
    if not unmapped.empty:
        print(f"\nUnmapped categories: {len(unmapped)} entries")
        category_counts = unmapped['Category'].value_counts().head(10)
        print("Top unmapped categories:")
        for category, count in category_counts.items():
            print(f"  {category}: {count} occurrences")
    
    return df_updated

def _generate_similarity_analysis(df, product_col, category_col, process):
    """Generate similarity analysis files for products and categories"""
    
    def find_similar_products(target_product, product_list, threshold=80):
        """Find all products above similarity threshold"""
        similar = process.extract(target_product, product_list, limit=len(product_list))
        return [(product, score) for product, score in similar if score >= threshold]
    
    def analyze_similar_entries(df, column_name, threshold=80):
        """Analyze similar entries in a column"""
        unique_values = df[column_name].dropna().unique().tolist()
        similar_groups = {}
        processed = set()
        
        for value in unique_values:
            if value in processed:
                continue
                
            similar = find_similar_products(value, unique_values, threshold)
            
            if len(similar) > 1:
                group_key = similar[0][0]
                similar_groups[group_key] = similar
                
                for entry, _ in similar:
                    processed.add(entry)
        
        return similar_groups
    
    def write_similarity_analysis(df, column_name, threshold, output_file):
        """Write similarity analysis to file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write(f"ÄHNLICHKEITSANALYSE - SPALTE: {column_name.upper()}\n")
                f.write("="*80 + "\n")
                f.write(f"Ähnlichkeitsschwellenwert: {threshold}%\n\n")
                
                similar_groups = analyze_similar_entries(df, column_name, threshold)
                
                if not similar_groups:
                    f.write("Keine ähnlichen Einträge gefunden.\n")
                    return
                
                total_groups = len(similar_groups)
                total_similar_entries = sum(len(group) for group in similar_groups.values())
                
                f.write(f"Gefundene ähnliche Gruppen: {total_groups}\n")
                f.write(f"Gesamt ähnliche Einträge: {total_similar_entries}\n")
                f.write("\n" + "-"*80 + "\n")
                
                for i, (group_name, similar_entries) in enumerate(sorted(similar_groups.items()), 1):
                    f.write(f"\n{i}. ÄHNLICHE GRUPPE: {group_name}\n")
                    f.write("-" * (len(group_name) + 20) + "\n")
                    
                    for j, (entry, score) in enumerate(similar_entries, 1):
                        count = len(df[df[column_name] == entry])
                        f.write(f"   {j}. {entry:<50} → {score:3d}% ({count:3d}x im Dataset)\n")
                    
                    f.write(f"   {'─' * 70}\n")
                    f.write(f"   Einträge in dieser Gruppe: {len(similar_entries)}\n")
                
                f.write(f"\nÄhnlichkeitsanalyse wurde in '{output_file}' gespeichert.\n")
                
        except Exception as e:
            print(f"Warning: Could not write analysis file {output_file}: {e}")
    
    # Generate analysis files
    try:
        write_similarity_analysis(df, product_col, 85, 'aehnliche_produkte.txt')
        write_similarity_analysis(df, category_col, 80, 'aehnliche_kategorien.txt')
        print("  Analysis files generated: aehnliche_produkte.txt, aehnliche_kategorien.txt")
    except Exception as e:
        print(f"  Warning: Could not generate analysis files: {e}")

def mapUnknownProductsByValue(df):
    """
    Maps unknown products to known products based on their value/price.
    This helps identify products that were marked as 'Unknown' during validation
    but can be identified by their consistent pricing.
    
    Args:
        df: DataFrame with Product, Category, and Value columns
        
    Returns:
        DataFrame with mapped unknown products
    """
    
    # Create a copy to avoid modifying the original
    df_mapped = df.copy()
    
    # Define value-to-product mappings
    value_mappings = {
        13: {
            'Product': 'Unknown',  # Keep as Unknown for value 13
            'Category': 'Vapes'
        },
        14: {
            'Product': 'ElfBar pod Kit',
            'Category': 'Vapes'
        },
        11: {
            'Product': 'Kinder Schoko Bons Crispy 89g',
            'Category': 'Snacks'
        }
    }
    
    # Track changes for reporting
    changes_made = {}
    
    # Only process rows where Product is currently 'Unknown'
    unknown_mask = df_mapped['Product'] == 'Unknown'
    
    for value, mapping in value_mappings.items():
        # Find unknown products with specific value
        condition = unknown_mask & (df_mapped['Value'] == value)
        affected_rows = condition.sum()
        
        if affected_rows > 0:
            # Apply the mapping
            df_mapped.loc[condition, 'Product'] = mapping['Product']
            df_mapped.loc[condition, 'Category'] = mapping['Category']
            
            # Update Super-Category if needed
            if mapping['Category'] == 'Vapes':
                df_mapped.loc[condition, 'Super-Category'] = 'Vapes'
            elif mapping['Category'] == 'Snacks':
                df_mapped.loc[condition, 'Super-Category'] = 'Snacks'
            
            # Track changes
            changes_made[value] = {
                'count': affected_rows,
                'product': mapping['Product'],
                'category': mapping['Category']
            }
    
    # Print results
    print("Unknown Product Value Mapping Results:")
    print("=" * 50)
    
    if changes_made:
        for value, info in changes_made.items():
            print(f"Value €{value}: {info['count']} rows mapped to '{info['product']}' ({info['category']})")
    else:
        print("No unknown products found with specified values.")
    
    # Show remaining unknown products by value
    remaining_unknown = df_mapped[df_mapped['Product'] == 'Unknown']
    if not remaining_unknown.empty:
        print(f"\nRemaining unknown products: {len(remaining_unknown)} entries")
        value_counts = remaining_unknown['Value'].value_counts().head(10)
        print("Top values for remaining unknown products:")
        for value, count in value_counts.items():
            print(f"  €{value}: {count} occurrences")
    
    return df_mapped
 
    


def finde_aehnliche_produkte(zielprodukt, produktliste, schwellenwert=80):
    """Findet alle Produkte über einem bestimmten Ähnlichkeitsschwellenwert"""
    try:
        from fuzzywuzzy import process
        aehnliche = process.extract(zielprodukt, produktliste, limit=len(produktliste))
        return [(produkt, score) for produkt, score in aehnliche if score >= schwellenwert]
    except ImportError:
        print("Warning: fuzzywuzzy not available for similarity analysis")
        return []