import argparse
from data_utils import load_dataframe

def main(csv_path: str = 'preprocessed_content.csv'):
    df = load_dataframe(csv_path)
    if df is not None:
        print(f"Total rows: {len(df)}")
        print(f"Unique (ticker, filename): {len(df.drop_duplicates(subset=['ticker', 'filename']))}")
        print(f"Unique tickers: {df['ticker'].nunique()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check row counts in ESG dataset")
    parser.add_argument("--path", type=str, default='preprocessed_content.csv',
                        help="Path to preprocessed content CSV file")
    args = parser.parse_args()
    main(args.path)
