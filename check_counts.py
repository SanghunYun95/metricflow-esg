import os
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, 'preprocessed_content.csv')

try:
    df = pd.read_csv(csv_path)
    print(f"Total rows: {len(df)}")
    print(f"Unique (ticker, filename): {len(df.drop_duplicates(subset=['ticker', 'filename']))}")
    print(f"Unique tickers: {df['ticker'].nunique()}")
except FileNotFoundError:
    print(f"CSV file not found at: {csv_path}")
