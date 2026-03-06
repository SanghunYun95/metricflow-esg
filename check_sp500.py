import pandas as pd
df = pd.read_csv('backend/sp500_components.csv')
print(f"Total rows in sp500_components.csv: {len(df)}")
print(f"Unique Symbols in sp500_components.csv: {df['Symbol'].nunique()}")
