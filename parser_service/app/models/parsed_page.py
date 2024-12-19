from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ParsedPage(Base):
    __tablename__ = "parsed_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, nullable=False)
    html_content = Column(Text)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime, server_default=func.now())
