from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, JSON, Index
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base

class SensorDevice(Base):
    __tablename__ = "sensor_devices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String(36), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(String(100), unique=True, nullable=False, index=True) # e.g. "IOT-TH-102"
    sensor_type = Column(String(50), nullable=False, index=True) # temperature, humidity, vibration, power, pressure
    status = Column(String(50), nullable=False, default="ONLINE") # ONLINE, OFFLINE, DELAYED, STALE, NO_SENSOR
    last_seen = Column(DateTime, default=datetime.utcnow)
    # configuration holds thresholds: safe_min/max, warning_min/max, critical_min/max, sampling_rate_sec
    configuration = Column(JSON, nullable=False, default=dict)

    asset = relationship("Asset", back_populates="sensor_devices")
    readings = relationship("SensorReading", back_populates="sensor", cascade="all, delete-orphan")
    anomalies = relationship("SensorAnomaly", back_populates="sensor", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="sensor")

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sensor_id = Column(String(36), ForeignKey("sensor_devices.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False) # e.g. "°C", "%", "Hz", "kW"

    sensor = relationship("SensorDevice", back_populates="readings")

    __table_args__ = (
        Index("ix_sensor_timestamp", "sensor_id", "timestamp"),
    )

class SensorAnomaly(Base):
    __tablename__ = "sensor_anomalies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sensor_id = Column(String(36), ForeignKey("sensor_devices.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    severity = Column(String(50), nullable=False) # WARNING, CRITICAL
    value = Column(Float, nullable=False)
    threshold_breached = Column(String(100), nullable=False) # e.g. "critical_max: 35.0"
    duration_minutes = Column(Float, default=0.0)
    resolved = Column(String(20), default="FALSE")

    sensor = relationship("SensorDevice", back_populates="anomalies")
