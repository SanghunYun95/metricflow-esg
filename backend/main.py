import os
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, select, func, desc, asc
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
from pydantic import BaseModel
from models import Company, ESGMetric, Base

# Setup Database Connection
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./esg_data.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="MetricFlow ESG API", version="1.0.0")

# Setup CORS to allow Next.js frontend to communicate
# TODO: Restrict allowed origins before production. Currently uses env var or defaults.
allow_origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
allow_origins = [origin.strip() for origin in allow_origins_str.split(",") if origin.strip()]
if not allow_origins:
    allow_origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Response Models
class SectorSummaryResponse(BaseModel):
    sector: str
    avg_e_score: float
    avg_s_score: float
    avg_g_score: float
    avg_total_score: float

class TopCompanyResponse(BaseModel):
    ticker: str
    security_name: str
    e_score: float
    s_score: float
    g_score: float
    total_score: float


@app.get("/api/v1/sectors", response_model=List[str])
def get_sectors(db: Session = Depends(get_db)):
    """
    Returns a distinct list of GICS sectors (industries) from the companies table.
    """
    sectors = db.scalars(select(Company.industry).distinct().where(Company.industry.is_not(None))).all()
    # Filter out empty or "Unknown" if desired
    return [s for s in sectors if s and s != "Unknown"]


@app.get("/api/v1/esg/summary", response_model=List[SectorSummaryResponse])
def get_esg_summary(
    sector: Optional[str] = Query(None, description="Filter by GICS Sector"),
    db: Session = Depends(get_db)
):
    """
    Returns average E, S, G scores grouped by sector natively using SQL JOINs.
    Optimized to aggregate at the DB level, preventing OOM issues with large datasets.
    """
    total_score_calc = (ESGMetric.e_score + ESGMetric.s_score + ESGMetric.g_score) / 3.0

    query = select(
        Company.industry.label("sector"),
        func.avg(ESGMetric.e_score).label("avg_e_score"),
        func.avg(ESGMetric.s_score).label("avg_s_score"),
        func.avg(ESGMetric.g_score).label("avg_g_score"),
        func.avg(total_score_calc).label("avg_total_score"),
    ).join(ESGMetric, Company.id == ESGMetric.company_id)\
     .where(Company.industry.is_not(None), Company.industry != "Unknown")

    if sector:
        query = query.where(Company.industry == sector)

    query = query.group_by(Company.industry)
    
    results = db.execute(query).all()
    
    return [
        SectorSummaryResponse(
            sector=row.sector,
            avg_e_score=round(row.avg_e_score or 0, 2),
            avg_s_score=round(row.avg_s_score or 0, 2),
            avg_g_score=round(row.avg_g_score or 0, 2),
            avg_total_score=round(row.avg_total_score or 0, 2)
        ) for row in results
    ]


@app.get("/api/v1/esg/top-companies", response_model=List[TopCompanyResponse])
def get_top_companies(
    sector: Optional[str] = Query(None, description="Filter by GICS Sector"),
    limit: int = Query(10, le=100, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    """
    Returns top companies with the lowest average Total ESG Risk score across the 60-month window.
    Low score == better risk mitigation.
    """
    total_score_calc = (ESGMetric.e_score + ESGMetric.s_score + ESGMetric.g_score) / 3.0
    total_score_label = func.avg(total_score_calc).label("total_score")

    query = select(
        Company.ticker, 
        Company.security_name, 
        func.avg(ESGMetric.e_score).label("e_score"), 
        func.avg(ESGMetric.s_score).label("s_score"), 
        func.avg(ESGMetric.g_score).label("g_score"), 
        total_score_label
    ).join(ESGMetric, Company.id == ESGMetric.company_id)

    if sector:
        query = query.where(Company.industry == sector)

    query = query.group_by(Company.ticker, Company.security_name)
    query = query.order_by(asc(total_score_label)).limit(limit)
    
    results = db.execute(query).all()
    
    return [
        TopCompanyResponse(
            ticker=row.ticker,
            security_name=row.security_name,
            e_score=round(row.e_score or 0, 2),
            s_score=round(row.s_score or 0, 2),
            g_score=round(row.g_score or 0, 2),
            total_score=round(row.total_score or 0, 2)
        ) for row in results
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
