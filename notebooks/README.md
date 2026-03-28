# Notebooks

This directory contains Jupyter notebooks for exploratory data analysis and visualization of the vending machine sales data.

## Main Notebooks

- **vending_machine_analysis.ipynb**: The primary notebook for analyzing sales patterns, product popularity, and payment preferences across different locations.

## How to Run

To run these notebooks:

1. Make sure dependencies are installed:
   ```
   uv pip install pandas matplotlib seaborn jupyter notebook
   ```

2. Start Jupyter Notebook server:
   ```
   jupyter notebook
   ```

3. Navigate to this directory in the Jupyter interface and open the desired notebook.

## Notebook Structure

Each notebook typically follows this structure:

1. **Setup and Data Loading**: Import libraries and load data
2. **Data Preprocessing**: Clean and transform the data
3. **Exploratory Analysis**: Initial data exploration and visualization
4. **Detailed Analysis**: In-depth analysis of specific aspects
5. **Conclusions**: Summary of insights and recommendations

## Best Practices

- Execute cells in order, from top to bottom
- Clear all outputs before committing to version control
- Document findings and interpretations within markdown cells
- Use relative paths (e.g., `../data/processed/`) for data access
- Save important visualizations to the `figures/` directory