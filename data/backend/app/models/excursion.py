from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin

class Excursion(Base, TimestampMixin):
    __tablename__ = "excursions"

    excursion_id = Column(String(50), primary_key=True, index=True) # e.g. EXC-2026-000001
    shipment_id = Column(String(50), ForeignKey("shipments.shipment_id"), nullable=False, index=True)
    container_id = Column(String(50), ForeignKey("containers.container_id"), nullable=True, index=True)
    sensor_id = Column(String(100), ForeignKey("sensors.sensor_id"), nullable=False, index=True)
    policy_id = Column(String(50), ForeignKey("threshold_policies.policy_id"), nullable=True, index=True)
    excursion_type = Column(String(50), nullable=False) # TEMPERATURE_HIGH, TEMPERATURE_LOW, HUMIDITY_HIGH, HUMIDITY_LOW, MISSING_INTERVAL
    severity = Column(String(50), nullable=False) # WARNING, CRITICAL
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Float, nullable=False, default=0.0)
    peak_value = Column(Float, nullable=True)
    threshold_limit = Column(Float, nullable=True)
    status = Column(String(50), nullable=False, default="OPEN") # OPEN, ACKNOWLEDGED, RESOLVED, CLOSED
    root_cause = Column(String(255), nullable=True)
    review_status = Column(String(30), nullable=False, default="Pending")
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    shipment = relationship("Shipment", back_populates="excursions")
    sensor = relationship("Sensor", back_populates="excursions")
    policy = relationship("ThresholdPolicy", back_populates="excursions")
    alerts = relationship("Alert", back_populates="excursion", cascade="all, delete-orphan")
    corrective_actions = relationship("CorrectiveAction", back_populates="excursion", cascade="all, delete-orphan")
    container = relationship("Container")
    status_history = relationship("ExcursionStatusEvent", back_populates="excursion", cascade="all, delete-orphan", order_by="ExcursionStatusEvent.changed_at")
