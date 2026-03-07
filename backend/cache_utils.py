import logging
from sqlalchemy import text
from sqlalchemy.engine.base import Connection

logger = logging.getLogger(__name__)

SECTOR_QUERY = """
SELECT c.industry AS sector,
       AVG(m.e_score) AS avg_e_score,
       AVG(m.s_score) AS avg_s_score,
       AVG(m.g_score) AS avg_g_score,
       AVG((m.e_score + m.s_score + m.g_score) / 3.0) AS avg_total_score
FROM companies c
JOIN esg_metrics m ON c.id = m.company_id
WHERE c.industry IS NOT NULL AND c.industry != 'Unknown'
GROUP BY c.industry
"""

TOP_COMPANIES_QUERY = """
SELECT c.ticker, c.security_name, c.industry AS sector,
       AVG(m.e_score) AS e_score,
       AVG(m.s_score) AS s_score,
       AVG(m.g_score) AS g_score,
       AVG((m.e_score + m.s_score + m.g_score) / 3.0) AS total_score
FROM companies c
JOIN esg_metrics m ON c.id = m.company_id
GROUP BY c.ticker, c.security_name, c.industry
"""

def create_or_refresh_cache(conn: Connection, dialect: str, is_refresh: bool = False):
    """
    Creates or refreshes Materialized Views/Cache tables.
    Works for both PostgreSQL (Materialized Views) and SQLite (Standard Tables as Cache).
    
    In SQLite, since MV is not supported, we always DROP and recreate.
    In Postgres, if `is_refresh` is True, we use REFRESH. Otherwise, DROP and CREATE.
    """
    if dialect == "sqlite":
        # SQLite: Drop and Recreate
        conn.execute(text("DROP TABLE IF EXISTS mv_esg_summary_sector"))
        conn.execute(text("DROP TABLE IF EXISTS mv_top_companies"))
        
        conn.execute(text(f"CREATE TABLE mv_esg_summary_sector AS {SECTOR_QUERY}"))
        conn.execute(text(f"CREATE TABLE mv_top_companies AS {TOP_COMPANIES_QUERY}"))
        
        conn.execute(text("CREATE INDEX idx_mv_sector ON mv_esg_summary_sector(sector)"))
        conn.execute(text("CREATE INDEX idx_mv_top_comp_total ON mv_top_companies(total_score)"))
        conn.execute(text("CREATE INDEX idx_mv_top_comp_sector ON mv_top_companies(sector)"))
        logger.info("SQLite cache tables re-created successfully.")
        
    else:
        # PostgreSQL
        if is_refresh:
            # We attempt standard REFRESH. 
            # Note: CONCURRENTLY is removed here because execution in FastAPI often occurs 
            # within a session transaction block (autocommit=False) which blocks CONCURRENTLY.
            # Plain REFRESH takes an exclusive lock but reliably works in all contexts.
            try:
                conn.execute(text("REFRESH MATERIALIZED VIEW mv_esg_summary_sector"))
                conn.execute(text("REFRESH MATERIALIZED VIEW mv_top_companies"))
                logger.info("PostgreSQL Materialized Views refreshed successfully.")
            except Exception as e:
                logger.error(f"Failed to refresh Materialized Views: {e}")
                raise
        else:
            conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS mv_esg_summary_sector"))
            conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS mv_top_companies"))
            
            conn.execute(text(f"CREATE MATERIALIZED VIEW mv_esg_summary_sector AS {SECTOR_QUERY}"))
            conn.execute(text(f"CREATE MATERIALIZED VIEW mv_top_companies AS {TOP_COMPANIES_QUERY}"))
            
            # MUST include UNIQUE for Postgres to support CONCURRENTLY later if configured properly
            conn.execute(text("CREATE UNIQUE INDEX idx_mv_sector ON mv_esg_summary_sector(sector)"))
            conn.execute(text("CREATE UNIQUE INDEX idx_mv_top_comp_ticker ON mv_top_companies(ticker, security_name, sector)"))
            
            # General Query Optimization indexes
            conn.execute(text("CREATE INDEX idx_mv_top_comp_total ON mv_top_companies(total_score)"))
            conn.execute(text("CREATE INDEX idx_mv_top_comp_sector ON mv_top_companies(sector)"))
            logger.info("PostgreSQL Materialized Views created successfully.")
