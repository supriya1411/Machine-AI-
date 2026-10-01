from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Text, JSON
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base

class FaultCategory(Base):
    __tablename__ = "fault_categories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(50), unique=True, nullable=False, index=True) # e.g. OVERHEATING, VIBRATION_HIGH, POWER_SURGE
    name = Column(String(150), nullable=False)
    severity = Column(String(50), nullable=False, default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    keywords = Column(JSON, nullable=False, default=list) # e.g. ["high temp", "over heating", "excess heat"]

    service_calls = relationship("ServiceCall", back_populates="normalized_fault")

class ServiceCall(Base):
    __tablename__ = "service_calls"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String(36), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    raw_fault = Column(Text, nullable=False) # Never delete original service-call text
    normalized_fault_id = Column(String(36), ForeignKey("fault_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    fault_code = Column(String(50), nullable=True, index=True) # Cached code like OVERHEATING
    severity = Column(String(50), nullable=False, default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)
    engineer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    downtime = Column(Float, default=0.0) # hours
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    asset = relationship("Asset", back_populates="service_calls")
    normalized_fault = relationship("FaultCategory", back_populates="service_calls")
    engineer = relationship("User")
