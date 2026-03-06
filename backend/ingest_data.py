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
        current_e = np.random.uniform(10, 40) # Lower risk is better
        current_s = np.random.uniform(10, 40)
        current_g = np.random.uniform(10, 40)
        current_carbon = np.random.uniform(100, 10000)
        
        for m in range(months):
            year = start_date.year + ((start_date.month - 1 + m) // 12)
            month = ((start_date.month - 1 + m) % 12) + 1
            year_month = f"{year:04d}-{month:02d}"
            
            # Cumulative Random walk
            current_e = max(0, min(100, current_e + np.random.normal(0, 1)))
            current_s = max(0, min(100, current_s + np.random.normal(0, 1)))
            current_g = max(0, min(100, current_g + np.random.normal(0, 1)))
            current_carbon = max(0, current_carbon + np.random.normal(0, 50))
            
            metrics.append({
                'company_id': company_id,
                'year_month': year_month,
                'e_score': round(current_e, 2),
                's_score': round(current_s, 2),
                'g_score': round(current_g, 2),
                'carbon_emissions': round(current_carbon, 2)
            })
    return metrics

def _resolve_row_limit(default: int = 865) -> int:
    try:
        return int(os.getenv("ROW_LIMIT", str(default)))
    except ValueError:
        return default

def ingest_data(max_companies: int | None = None):
    if max_companies is None:
        max_companies = _resolve_row_limit()
        
    engine = create_engine(DATABASE_URL)
    
    print("Loading preprocessed content...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    csv_path = os.path.join(project_root, 'preprocessed_content.csv')
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"preprocessed_content.csv not found at {csv_path}. Ingestion cancelled.")
        return

    # Safety check for production environments
    environment = os.getenv("ENVIRONMENT", "development").lower()
    force_schema_reset = os.getenv("FORCE_SCHEMA_RESET", "false").lower() == "true"
    
    if environment == "production":
        if not force_schema_reset:
            confirm = input("WARNING: This will delete all existing data. Type 'yes' to confirm: ")
            if confirm.lower() != 'yes':
                print("Ingestion cancelled.")
                return

    # Drop existing tables to apply the new schema cleanly
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()

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

    # Extract Companies (Target: max_companies companies)
    print(f"Original CSV has {len(df)} rows. Processing first {max_companies} to reach target metric count...")
    df = df.head(max_companies)
    
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
    import argparse
    parser = argparse.ArgumentParser(description="Ingest ESG Data")
    parser.add_argument("--limit", type=int, default=_resolve_row_limit(), 
                        help="Number of companies to process")
    args = parser.parse_args()
    
    ingest_data(max_companies=args.limit)
