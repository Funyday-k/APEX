import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, JSON, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    image_path = Column(String)
    chart_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExtractionRecord(Base):
    __tablename__ = "extractions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String)
    calibration = Column(JSON)
    result = Column(JSON)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
