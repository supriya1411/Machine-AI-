from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String(50), nullable=False, index=True) # IOT_THRESHOLD, ENVIRONMENTAL_ANOMALY, RECURRING_FAILURE, HIGH_RISK, OVERDUE_PM, PM_CADENCE_VIOLATION, EXPIRING_CONTRACT, RENEWAL_RISK
    severity = Column(String(50), nullable=False, index=True) # CRITICAL, HIGH, MEDIUM, LOW
    asset_id = Column(String(36), ForeignKey("assets.id", ondelete="CASCADE"), nullable=True, index=True)
    sensor_id = Column(String(36), ForeignKey("sensor_devices.id", ondelete="SET NULL"), nullable=True)
    contract_id = Column(String(36), ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    current_value = Column(String(100), nullable=True) # e.g. "38.5 °C"
    threshold = Column(String(100), nullable=True) # e.g. "Max 35.0 °C"
    duration = Column(String(100), nullable=True) # e.g. "18 minutes"
    reason = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="ACTIVE", index=True) # ACTIVE, ACKNOWLEDGED, ASSIGNED, RESOLVED

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    asset = relationship("Asset", back_populates="alerts")
    sensor = relationship("SensorDevice", back_populates="alerts")
    contract = relationship("Contract", back_populates="alerts")
    acknowledger = relationship("User")
