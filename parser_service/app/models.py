from sqlalchemy import Column, String, Integer, JSON
from app.database import Base


class ParsedData(Base):
    __tablename__ = "parsed_data"

    id = Column(Integer, primary_key=True, index=True)
    correlation_id = Column(String, unique=True, index=True, nullable=False)
    content = Column(JSON, nullable=True)
    status = Column(String, default="parsed", nullable=False)