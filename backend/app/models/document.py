from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False) # SIGNED_SERVICE_REPORT, PM_REPORT, CONTRACT_DOC, INSPECTION_REPORT, WARRANTY_DOC
    entity_type = Column(String(50), nullable=False, index=True) # ASSET, CONTRACT, MAINTENANCE, SERVICE_CALL
    entity_id = Column(String(36), nullable=False, index=True)
    file_path = Column(String(500), nullable=False) # Internal stored path, never exposed raw
    uploaded_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    uploader = relationship("User")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True) # e.g. ASSET_CREATED, THRESHOLD_UPDATED, ALERT_ACKNOWLEDGED
    entity_type = Column(String(100), nullable=False) # ASSET, SENSOR, ALERT, WORK_ORDER, USER
    entity_id = Column(String(100), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")
