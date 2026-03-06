from sqlalchemy import Column, Integer, String, Float, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Company(Base):
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, unique=True, index=True)
    security_name = Column(String, index=True)
    industry = Column(String, index=True)

    metrics = relationship("ESGMetric", back_populates="company", cascade="all, delete-orphan")

class ESGMetric(Base):
    __tablename__ = 'esg_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), index=True)
    year_month = Column(String, index=True) # e.g., '2023-01'
    e_score = Column(Float, nullable=False)
    s_score = Column(Float, nullable=False)
    g_score = Column(Float, nullable=False)
    carbon_emissions = Column(Float, nullable=False)

    company = relationship("Company", back_populates="metrics")
    
    # Critical Constraint: Adding composite index architecture 
    # This index is specifically necessary to optimize the 50,000+ row JOIN & GROUP BY aggregations.
    __table_args__ = (
        Index('ix_esg_company_ym', 'company_id', 'year_month', unique=True),
    )

if __name__ == '__main__':
    print("ESG Models schema defined successfully.")
