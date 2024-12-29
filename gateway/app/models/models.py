from sqlalchemy import Column, Integer, String, JSON
from app.database.database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    correlation_id = Column(String, unique=True, index=True, nullable=False)
    frequency_distribution = Column(JSON)
    entities = Column(JSON)
    sentiment = Column(JSON)
    seo_data = Column(JSON)
    performance_data = Column(JSON)
    accessibility_data = Column(JSON)
    security_data = Column(JSON)
    structure_data = Column(JSON)
    recommendations = Column(JSON)
    status = Column(String, default="processing")
