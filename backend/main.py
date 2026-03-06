import os
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, select, func, desc
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
from pydantic import BaseModel
from models import ESGReport, Base

# Setup Database Connection
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./esg_data.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="MetricFlow ESG API", version="1.0.0")

# Setup CORS to allow Next.js frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For MVP purposes. Restrict in production.
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
    Returns a distinct list of GICS sectors from the database.
    """
    sectors = db.scalars(select(ESGReport.gics_sector).distinct().where(ESGReport.gics_sector.is_not(None))).all()
    # Filter out empty or "Unknown" if desired, but returning all found distinct values for now
    return [s for s in sectors if s and s != "Unknown"]


@app.get("/api/v1/esg/summary", response_model=List[SectorSummaryResponse])
def get_esg_summary(
    sector: Optional[str] = Query(None, description="Filter by GICS Sector"),
    db: Session = Depends(get_db)
):
    """
    Returns average E, S, G scores grouped by sector.
    Optimized to aggregate at the DB level, preventing OOM issues with large datasets.
    """
    query = select(
        ESGReport.gics_sector.label("sector"),
        func.avg(ESGReport.e_score).label("avg_e_score"),
        func.avg(ESGReport.s_score).label("avg_s_score"),
        func.avg(ESGReport.g_score).label("avg_g_score"),
        func.avg(ESGReport.total_score).label("avg_total_score"),
    ).where(ESGReport.gics_sector.is_not(None), ESGReport.gics_sector != "Unknown")

    if sector:
        query = query.where(ESGReport.gics_sector == sector)

    query = query.group_by(ESGReport.gics_sector)
    
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
    Returns top companies with the lowest Total ESG Risk score.
    Lowest risk == better score in this methodology.
    """
    query = select(
        ESGReport.ticker, 
        ESGReport.security_name, 
        ESGReport.e_score, 
        ESGReport.s_score, 
        ESGReport.g_score, 
        ESGReport.total_score
    ).where(ESGReport.total_score.is_not(None))

    if sector:
        query = query.where(ESGReport.gics_sector == sector)

    # Calculate by taking the most recent year's score ideally, 
    # but for this MVP aggregation, we will just order by lowest total_score directly.
    query = query.order_by(ESGReport.total_score.asc()).limit(limit)
    
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
