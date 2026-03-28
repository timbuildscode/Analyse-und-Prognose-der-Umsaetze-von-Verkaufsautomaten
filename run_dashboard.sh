#!/bin/bash

# Run the Vending Machine Sales Dashboard
echo "Starting Vending Machine Sales Dashboard..."
echo "The dashboard will open in your browser at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""

# Run streamlit with uv
uv run streamlit run dashboard/Home.py