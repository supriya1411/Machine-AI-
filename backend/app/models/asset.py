from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Integer, Float, JSON
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String(100), unique=True, nullable=False, index=True) # e.g. "EQ-102"
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True) # HVAC, Chiller, Transformer, Generator, AHU, etc.
    model = Column(String(150), nullable=True)
    serial_number = Column(String(150), nullable=True, index=True)
    manufacturer = Column(String(150), nullable=True)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False, index=True)
    floor = Column(String(50), nullable=True)
    installation_date = Column(Date, nullable=True)
    warranty_expiry = Column(Date, nullable=True)
    criticality = Column(String(50), nullable=False, default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), nullable=False, default="OPERATIONAL") # OPERATIONAL, DEGRADED, DOWN, MAINTENANCE

    # Dynamically calculated/cached operational metrics
    health_score = Column(Integer, default=100) # 0-100
    risk_score = Column(Integer, default=0) # 0-100
    risk_level = Column(String(50), default="LOW") # LOW, MEDIUM, HIGH, CRITICAL
    last_risk_assessment = Column(DateTime, default=datetime.utcnow)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    site = relationship("Site", back_populates="assets")
    service_calls = relationship("ServiceCall", back_populates="asset", cascade="all, delete-orphan")
    sensor_devices = relationship("SensorDevice", back_populates="asset", cascade="all, delete-orphan")
    maintenances = relationship("Maintenance", back_populates="asset", cascade="all, delete-orphan")
    work_orders = relationship("WorkOrder", back_populates="asset", cascade="all, delete-orphan")
    contract_associations = relationship("ContractAsset", back_populates="asset", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="asset", cascade="all, delete-orphan")
