from fastapi import FastAPI, Depends, Query, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, select, func, desc, asc, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import ProgrammingError, OperationalError, SQLAlchemyError
from typing import List, Optional
from pydantic import BaseModel
from models import Company, ESGMetric, Base
import logging
import os
from cache_utils import create_or_refresh_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    try:
        # 1. Faster path: Query from Materialized View / Cache Table
        query_sql = "SELECT sector, avg_e_score, avg_s_score, avg_g_score, avg_total_score FROM mv_esg_summary_sector"
        params = {}
        if sector:
            query_sql += " WHERE sector = :sector"
            params["sector"] = sector
            
        results = db.execute(text(query_sql), params).mappings().all()
        
        logger.info(f"Cache Hit: Sector summary served from Materialized View (Rows: {len(results)})")
        return [
            SectorSummaryResponse(
                sector=row["sector"],
                avg_e_score=round(row["avg_e_score"] or 0, 2),
                avg_s_score=round(row["avg_s_score"] or 0, 2),
                avg_g_score=round(row["avg_g_score"] or 0, 2),
                avg_total_score=round(row["avg_total_score"] or 0, 2)
            ) for row in results
        ]
    except (ProgrammingError, OperationalError):
        db.rollback()
        logger.warning("Cache Miss: Computing sector summary manually from 10,000,000+ rows...")
        # 2. Schema not found error (View doesn't exist yet)
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
    try:
        query_sql = "SELECT ticker, security_name, e_score, s_score, g_score, total_score FROM mv_top_companies"
        params = {"limit": limit}
        if sector:
            query_sql += " WHERE sector = :sector"
            params["sector"] = sector
            
        query_sql += " ORDER BY total_score ASC LIMIT :limit"
        
        results = db.execute(text(query_sql), params).mappings().all()
        print(f"[*] Cache Hit: Top companies served from Materialized View (Rows: {len(results)})")
        return [
            TopCompanyResponse(
                ticker=row["ticker"],
                security_name=row["security_name"],
                e_score=round(row["e_score"] or 0, 2),
                s_score=round(row["s_score"] or 0, 2),
                g_score=round(row["g_score"] or 0, 2),
                total_score=round(row["total_score"] or 0, 2)
            ) for row in results
        ]
    except (ProgrammingError, OperationalError):
        db.rollback()
        print("[!] Cache Miss: Finding top companies manually from 10,000,000+ rows...")
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

def get_admin_key(x_admin_key: str = Header(..., description="Administrator API Key")):
    expected_key = os.getenv("ADMIN_API_KEY")
    if not expected_key:
        logger.error("ADMIN_API_KEY is not configured")
        raise HTTPException(status_code=503, detail="Admin authentication is not configured")
    if x_admin_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return True

@app.post("/api/v1/system/refresh-cache")
def refresh_cache(
    db: Session = Depends(get_db),
    authorized: bool = Depends(get_admin_key)
):
    """
    Refreshes the Materialized Views (PostgreSQL) or truncates/rebuilds tables (SQLite).
    This ensures that new incoming real-time data gets cached into the fast DB layer.
    """
    try:
        # Pass raw DB connection to bypass session autocommit limitations 
        con = db.connection()
        dialect = db.bind.dialect.name
        
        create_or_refresh_cache(con, dialect, is_refresh=True)
        db.commit()
        return {"status": "success", "message": "Cache (Materialized Views) refreshed successfully."}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error during refresh: {str(e)}") from e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}") from e

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
