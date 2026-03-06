import os
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, 'backend', 'sp500_components.csv')

try:
    df = pd.read_csv(csv_path)
    print(f"Total rows in sp500_components.csv: {len(df)}")
    print(f"Unique Symbols in sp500_components.csv: {df['Symbol'].nunique()}")
except FileNotFoundError:
    print(f"CSV file not found at: {csv_path}")
