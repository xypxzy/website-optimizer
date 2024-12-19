from sqlalchemy import Column, Integer, Text, JSON, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    frequency_distribution = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
