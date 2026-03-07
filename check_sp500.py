import os
import argparse
from data_utils import load_dataframe

def main(csv_path: str = os.path.join('backend', 'sp500_components.csv')):
    df = load_dataframe(csv_path)
    if df is not None:
        print(f"Total rows in sp500_components.csv: {len(df)}")
        print(f"Unique Symbols in sp500_components.csv: {df['Symbol'].nunique()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check row counts in S&P 500 components")
    parser.add_argument("--path", type=str, default=os.path.join('backend', 'sp500_components.csv'),
                        help="Path to sp500_components CSV file")
    args = parser.parse_args()
    main(args.path)
