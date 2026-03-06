import pandas as pd
df = pd.read_csv('preprocessed_content.csv')
print(f"Total rows: {len(df)}")
print(f"Unique (ticker, filename): {len(df.drop_duplicates(subset=['ticker', 'filename']))}")
print(f"Unique tickers: {df['ticker'].nunique()}")
