import os
import time
import random
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from models import Base, Company, ESGMetric

def generate_and_benchmark(db_url, num_companies, months=60):
    engine = create_engine(db_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    total_rows = num_companies * months
    print(f"\n=======================================================")
    print(f"--- Benchmarking with {total_rows:,} rows ---")
    print(f"=======================================================")
    
    # 1. Generate companies
    companies = []
    for i in range(num_companies):
        companies.append(Company(
            ticker=f"TICK{i}",
            security_name=f"Company {i}",
            industry=f"Sector {i % 11}"
        ))
    session.add_all(companies)
    session.commit()

    company_ids = [c.id for c in session.query(Company).all()]
    
    # 2. Generate metrics
    metrics = []
    start_time = time.time()
    for cid in company_ids:
        for m in range(months):
            y = 2020 + (m // 12)
            mo = (m % 12) + 1
            metrics.append({
                'company_id': cid,
                'year_month': f"{y}-{mo:02d}",
                'e_score': random.uniform(10, 40),
                's_score': random.uniform(10, 40),
                'g_score': random.uniform(10, 40),
                'carbon_emissions': random.uniform(100, 1000)
            })
            if len(metrics) >= 5000:
                session.bulk_insert_mappings(ESGMetric, metrics)
                metrics = []
    
    if metrics:
        session.bulk_insert_mappings(ESGMetric, metrics)
    session.commit()
    insert_time = time.time() - start_time
    print(f"[*] Data Generation & Insert Time: {insert_time:.2f} seconds")

    total_score_calc = (ESGMetric.e_score + ESGMetric.s_score + ESGMetric.g_score) / 3.0

    # 3. Benchmark Query 1: Sector Aggregation (All data Group By)
    start_time = time.time()
    query1 = select(
        Company.industry.label("sector"),
        func.avg(ESGMetric.e_score).label("avg_e_score"),
        func.avg(total_score_calc).label("avg_total_score"),
    ).join(ESGMetric, Company.id == ESGMetric.company_id)\
     .group_by(Company.industry)
    
    results1 = session.execute(query1).all()
    query1_time = time.time() - start_time
    print(f"[*] Sector Aggregation Query (GROUP BY): {query1_time * 1000:.2f} ms")

    # 4. Benchmark Query 2: Top Companies Filtering
    start_time = time.time()
    query2 = select(
        Company.ticker, 
        Company.security_name, 
        func.avg(total_score_calc).label("total_score")
    ).join(ESGMetric, Company.id == ESGMetric.company_id)\
     .group_by(Company.ticker, Company.security_name)\
     .order_by(func.avg(total_score_calc).asc()).limit(10)
    
    results2 = session.execute(query2).all()
    query2_time = time.time() - start_time
    print(f"[*] Top 10 Companies Query (ORDER BY + LIMIT): {query2_time * 1000:.2f} ms")

    session.close()
    engine.dispose()
    return query1_time, query2_time

if __name__ == "__main__":
    db_url = "sqlite:///./benchmark.db"
    
    def clean_db():
        if os.path.exists("./benchmark.db"):
            os.remove("./benchmark.db")
            
    # Test 1: 50k rows
    clean_db()
    generate_and_benchmark(db_url, 834, 60) # ~50,040 rows
    
    # Test 2: 1M rows
    clean_db()
    generate_and_benchmark(db_url, 16667, 60) # ~1,000,020 rows
    
    # Test 3: 10M rows
    clean_db()
    generate_and_benchmark(db_url, 166667, 60) # ~10,000,020 rows
    
    clean_db()
    print("\nBenchmarking complete.")
