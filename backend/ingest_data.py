import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text, func, insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import ProgrammingError, OperationalError
from models import Base, Company, ESGMetric
from cache_utils import create_or_refresh_cache

# Ensure DATABASE_URL is set or use a default local sqlite for testing
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./esg_data.db")

def generate_synthetic_data_for_batch(companies: list, months: int = 60):
    metrics = []
    for company in companies:
        company_id = company['id']
        # Initialize scores to be higher, as lower risk is better, so higher score is better
        current_e, current_s, current_g = np.random.uniform(50, 90, 3) 
        current_carbon = np.random.uniform(500, 5000)
        
        for i in range(months):
            # Calculate year and month (last 5 years)
            year = 2024 - (months - 1 - i) // 12
            month = 1 + (i % 12)
            year_month = f"{year}-{month:02d}"
            
            # Subtle random walk for better looking data
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
    # Handle duplicate tickers or duplicate dataset copying 
    # if `max_companies` > len(df)
    companies_data = []
    original_len = len(df)
    
    if original_len == 0:
        print("No source rows found in preprocessed_content.csv. Ingestion cancelled.")
        return
        
    print(f"Original CSV has {original_len} rows. Target: {max_companies} companies.")
    
    for i in range(max_companies):
        row_idx = i % original_len
        row = df.iloc[row_idx].copy()
        
        # Keep original ticker behavior, but ensure uniqueness if we duplicate
        if i >= original_len:
            row['ticker'] = f"{row['ticker']}-{i // original_len}"
            
        companies_data.append(row)
        
    df = pd.DataFrame(companies_data)
    
    # Ensure unique_companies_df is deduplicated by 'ticker'
    # so we don't violate Company(ticker=...) unique constraint when iterating df records
    unique_companies_df = (
        df[['ticker', 'security_name', 'industry']]
        .drop_duplicates(subset=['ticker'], keep='first')
        .copy()
    )
    
    print(f"Preparing to insert {len(unique_companies_df)} companies into the database...")
    company_records = unique_companies_df.to_dict(orient='records')
    
    try:
        # Insert Companies and get IDs
        companies_to_insert = [Company(**rec) for rec in company_records]
        session.add_all(companies_to_insert)
        session.flush() # Flush to populate auto-increment IDs
        
        inserted_companies = [c.id for c in companies_to_insert]
        
        print(f"Generating synthetic time-series data for {len(inserted_companies)} companies (60 months each)...")
        
        # Batch generation and insertion to prevent MemoryError (Chunks of 1000 companies = 60000 records)
        batch_size = 1000
        total_metrics = 0
        for i in range(0, len(inserted_companies), batch_size):
            company_batch = [{'id': cid} for cid in inserted_companies[i:i+batch_size]]
            metric_batch = generate_synthetic_data_for_batch(company_batch, months=60)
            
            # Print progress and insert using Core for max performance
            print(f"[*] Inserting batch: {i//batch_size + 1}/{(len(inserted_companies) + batch_size - 1)//batch_size} ({len(metric_batch)} rows)...")
            session.execute(insert(ESGMetric), metric_batch)
            total_metrics += len(metric_batch)
            
        session.commit()
        print(f"Data ingestion completed successfully. Total Metrics: {total_metrics}")
        
        # Initialize Materialized Views for caching
        print("Initializing Materialized Views / Cache Tables for ultra-fast performance...")
        dialect = engine.dialect.name
        
        try:
            with engine.connect() as conn:
                create_or_refresh_cache(conn, dialect, is_refresh=False)
                conn.commit()
                print("Materialized Views successfully initialized!")
        except Exception as e:
            print(f"WARNING: Failed to initialize Materialized Views: {e}")
            print("Data has been committed successfully, but the caching layer might be incomplete.")
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
