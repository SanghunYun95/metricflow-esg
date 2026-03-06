import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, Index
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class ESGReport(Base):
    __tablename__ = 'esg_reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String)
    ticker = Column(String, index=True) # Adding index for frequent lookups by ticker
    security_name = Column(String, index=True) # Adding index for frequent lookups by company name
    gics_sector = Column(String, index=True) # Adding index for aggregations by sector
    year = Column(Integer, index=True)
    e_score = Column(Float)
    s_score = Column(Float)
    g_score = Column(Float)
    total_score = Column(Float)

if __name__ == '__main__':
    # This block is for testing the schema generation.
    print("ESGReport schema defined successfully.")
