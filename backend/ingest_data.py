import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, ESGReport

# Ensure DATABASE_URL is set or use a default local sqlite for testing
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./esg_data.db")

def ingest_data():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("Loading preprocessed content...")
    df = pd.read_csv('preprocessed_content.csv')
    
    # We don't need 'Unnamed: 0', 'preprocessed_content', 'ner_entities' for the DB table
    cols_to_keep = ['filename', 'ticker', 'year', 'e_score', 's_score', 'g_score', 'total_score']
    df = df[cols_to_keep]

    print("Loading S&P 500 components for mapping...")
    try:
        sp500_df = pd.read_csv('backend/sp500_components.csv')
        # S&P 500 CSV usually has 'Symbol', 'Security', 'GICS Sector'
        sp500_mapping = sp500_df[['Symbol', 'Security', 'GICS Sector']].drop_duplicates()
        
        # Merge to add sector and security name
        df = df.merge(sp500_mapping, left_on='ticker', right_on='Symbol', how='left')
        df.rename(columns={'Security': 'security_name', 'GICS Sector': 'gics_sector'}, inplace=True)
        df.drop(columns=['Symbol'], inplace=True)
    except FileNotFoundError:
        print("sp500_components.csv not found. Proceeding with missing sector/name data.")
        df['security_name'] = None
        df['gics_sector'] = None

    # Handle NaN values
    print("Handling NaNs...")
    # Fill missing scores with 0 conceptually for this MVP, or drop them. 
    # Let's drop rows where essential scores are missing to ensure data quality.
    df.dropna(subset=['e_score', 's_score', 'g_score', 'total_score'], inplace=True)
    
    # For missing mapping data, we can fill with "Unknown"
    df['security_name'] = df['security_name'].fillna('Unknown')
    df['gics_sector'] = df['gics_sector'].fillna('Unknown')

    print(f"Preparing to insert {len(df)} records into the database...")
    
    # Convert DataFrame to list of dictionaries for bulk insert
    records = df.to_dict(orient='records')
    
    try:
        # Optimal way to bulk insert with SQLAlchemy
        session.bulk_insert_mappings(ESGReport, records)
        session.commit()
        print("Data ingestion completed successfully.")
    except Exception as e:
        session.rollback()
        print(f"Failed to ingest data. Error: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    ingest_data()
