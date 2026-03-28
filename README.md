# Vending Machine Sales Analysis

This project analyzes sales data from vending machines to identify patterns and optimize performance.

## How to use

### Install uv
UV is a fast Python package installer and resolver. Install it first to manage the project dependencies.

#### Windows
```
uv run jupyter
```

#### Mac / Linux
```
uv run jupyter
```

### Run Jupyter Notebook
```
uv run jupyter
```
This installs dependencies and creates a .venv environment.

### Run scripts
```
uv run scripts/data_processing/clean_sales_data.py
uv run scripts/analysis/sales_analysis.py 
uv run main.py
```

## Folder Structure

```
├── data/                      # All data files
│   ├── external/              # Data from external sources
│   ├── interim/               # Intermediate processed data
│   ├── processed/             # Final, cleaned data ready for analysis
│   └── raw/                   # Original, immutable data
├── docs/                      # Documentation
├── notebooks/                 # Jupyter notebooks for exploration and analysis
│   └── vending_machine_analysis.ipynb  # Main analysis notebook
├── scripts/                   # Standalone scripts
│   ├── analysis/              # Scripts for data analysis
│   ├── data_processing/       # Scripts for data processing
│   └── visualization/         # Scripts for creating visualizations
├── tests/                     # Test files
├── pyproject.toml             # Project dependencies and metadata
├── README.md                  # Project overview
└── main.py                    # Main entry point for the project
```

## Data Processing Flow

1. **Raw Data**: Excel files with sales transactions from vending machines
2. **Processing**: Run `clean_sales_data.py` to clean and preprocess the data
3. **Analysis**: Run `sales_analysis.py` or the Jupyter notebook to analyze the data
4. **Results**: Visualizations and insights about sales patterns

## Troubleshooting

If you encounter errors about missing columns (like "Column 'price_eur' does not exist!"), check that:
1. The data processing script has been run first to generate processed data
2. Column names match between processed data and analysis code