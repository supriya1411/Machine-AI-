from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Float, Integer
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base

class ContractAsset(Base):
    __tablename__ = "contract_assets"

    contract_id = Column(String(36), ForeignKey("contracts.id", ondelete="CASCADE"), primary_key=True)
    asset_id = Column(String(36), ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True)

    contract = relationship("Contract", back_populates="contract_assets")
    asset = relationship("Asset", back_populates="contract_associations")

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String(100), unique=True, nullable=False, index=True) # e.g. "AMC-2025-089"
    name = Column(String(255), nullable=False)
    customer = Column(String(200), nullable=False)
    vendor = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False) # AMC, CMC
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False, index=True)
    value = Column(Float, nullable=False, default=0.0)
    pm_frequency_days = Column(Integer, nullable=False, default=90) # e.g. every 90 days
    status = Column(String(50), nullable=False, default="ACTIVE") # ACTIVE, EXPIRING_SOON, EXPIRED, TERMINATED

    # Dynamic metrics
    compliance_score = Column(Float, default=100.0) # 0-100
    renewal_risk = Column(String(50), default="LOW") # LOW, MEDIUM, HIGH, CRITICAL

    contract_assets = relationship("ContractAsset", back_populates="contract", cascade="all, delete-orphan")
    maintenances = relationship("Maintenance", back_populates="contract")
    alerts = relationship("Alert", back_populates="contract")
