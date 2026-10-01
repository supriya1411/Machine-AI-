from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base

class Maintenance(Base):
    __tablename__ = "maintenances"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String(36), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    pm_type = Column(String(100), nullable=False, default="QUARTERLY_PM") # MONTHLY_PM, QUARTERLY_PM, ANNUAL_OVERHAUL, STATUTORY_INSPECTION
    scheduled_date = Column(Date, nullable=False, index=True)
    completed_date = Column(Date, nullable=True, index=True)
    status = Column(String(50), nullable=False, default="SCHEDULED") # SCHEDULED, COMPLETED, OVERDUE, MISSED, CANCELLED
    engineer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    contract_id = Column(String(36), ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    evidence_document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)

    asset = relationship("Asset", back_populates="maintenances")
    engineer = relationship("User")
    contract = relationship("Contract", back_populates="maintenances")
    evidence_document = relationship("Document")

class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String(36), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False, default="CORRECTIVE") # PREVENTIVE, CORRECTIVE, EMERGENCY, INSPECTION
    priority = Column(String(50), nullable=False, default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    assigned_engineer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    due_date = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="OPEN") # OPEN, IN_PROGRESS, PENDING_PARTS, COMPLETED, CANCELLED
    description = Column(Text, nullable=False)

    asset = relationship("Asset", back_populates="work_orders")
    assigned_engineer = relationship("User")
