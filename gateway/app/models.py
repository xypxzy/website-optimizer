from sqlalchemy import Column, String, Integer, JSON
from app.database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    correlation_id = Column(String, unique=True, index=True, nullable=False)
    frequency_distribution = Column(JSON)
    entities = Column(JSON)
    status = Column(String, default="processing")
