import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Company, ESGMetric

# Ensure DATABASE_URL is set or use a default local sqlite for testing
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./esg_data.db")

def generate_synthetic_data(companies, months=60):
    metrics = []
    # Base date: e.g., 5 years starting Jan 2019
    start_date = datetime(2019, 1, 1)
    
    for comp in companies:
        company_id = comp['id']
        base_e = np.random.uniform(10, 40) # Lower risk is better
        base_s = np.random.uniform(10, 40)
        base_g = np.random.uniform(10, 40)
        base_carbon = np.random.uniform(100, 10000)
        
        for m in range(months):
            # Approximate months as 30-day increments
            current_date = start_date + timedelta(days=30*m)
            year_month = current_date.strftime('%Y-%m')
            
            # Random walk
            e_score = max(0, min(100, base_e + np.random.normal(0, 1)))
            s_score = max(0, min(100, base_s + np.random.normal(0, 1)))
            g_score = max(0, min(100, base_g + np.random.normal(0, 1)))
            carbon = max(0, base_carbon + np.random.normal(0, 50))
            
            metrics.append({
                'company_id': company_id,
                'year_month': year_month,
                'e_score': round(e_score, 2),
                's_score': round(s_score, 2),
                'g_score': round(g_score, 2),
                'carbon_emissions': round(carbon, 2)
            })
    return metrics

def ingest_data():
    engine = create_engine(DATABASE_URL)
    
    # Drop existing tables to apply the new schema cleanly
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()

    print("Loading preprocessed content...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    csv_path = os.path.join(project_root, 'preprocessed_content.csv')
    df = pd.read_csv(csv_path)

    print("Loading S&P 500 components for mapping...")
    try:
        sp500_path = os.path.join(script_dir, 'sp500_components.csv')
        sp500_df = pd.read_csv(sp500_path)
        sp500_mapping = sp500_df[['Symbol', 'Security', 'GICS Sector']].drop_duplicates()
        df = df.merge(sp500_mapping, left_on='ticker', right_on='Symbol', how='left')
        df.rename(columns={'Security': 'security_name', 'GICS Sector': 'industry'}, inplace=True)
    except FileNotFoundError:
        print(f"sp500_components.csv not found at {sp500_path}. Proceeding with missing sector/name data.")
        df['security_name'] = None
        df['industry'] = None

    df['security_name'] = df['security_name'].fillna('Unknown')
    df['industry'] = df['industry'].fillna('Unknown')

    # Extract Companies (Target: ~865 companies to reach 51,900 metrics)
    print(f"Original CSV has {len(df)} rows. Processing first 865 to reach target metric count...")
    df = df.head(865)
    
    # Handle duplicate tickers for the unique constraint
    # We'll use ticker + row index if duplicate exists to keep them unique
    df['ticker_orig'] = df['ticker']
    df['ticker'] = df.groupby('ticker').cumcount().astype(str)
    df['ticker'] = df.apply(lambda x: x['ticker_orig'] if x['ticker'] == '0' else f"{x['ticker_orig']}-{x['ticker']}", axis=1)
    
    unique_companies_df = df[['ticker', 'security_name', 'industry']].copy()
    
    print(f"Preparing to insert {len(unique_companies_df)} companies into the database...")
    company_records = unique_companies_df.to_dict(orient='records')
    
    try:
        # Insert Companies and get IDs
        companies_to_insert = [Company(**rec) for rec in company_records]
        session.add_all(companies_to_insert)
        session.flush() # Flush to populate auto-increment IDs
        
        inserted_companies = [{'id': c.id, 'ticker': c.ticker} for c in companies_to_insert]
        
        print(f"Generating synthetic time-series data for {len(inserted_companies)} companies (60 months each)...")
        metric_records = generate_synthetic_data(inserted_companies, months=60)
        
        print(f"Preparing to bulk insert {len(metric_records)} ESG metric records into the database (Total: {len(metric_records)})...")
        session.bulk_insert_mappings(ESGMetric, metric_records)
        
        session.commit()
        print(f"Data ingestion completed successfully. Total Metrics: {len(metric_records)}")
    except Exception as e:
        session.rollback()
        print(f"Failed to ingest data. Error: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    ingest_data()
