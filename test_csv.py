import pandas as pd

try:
    df = pd.read_csv('preprocessed_content.csv', nrows=5)
    print('--- Columns ---')
    print(df.columns.tolist())
    print('\n--- Info ---')
    print(df.dtypes)
    print('\n--- Head ---')
    print(df.head())
except Exception as e:
    print(f"Error: {e}")
