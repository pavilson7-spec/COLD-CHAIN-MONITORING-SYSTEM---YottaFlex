from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin

class Sensor(Base, TimestampMixin):
    __tablename__ = "sensors"

    sensor_id = Column(String(100), primary_key=True, index=True) # e.g. SNS-CNT-000001-TEMP
    sensor_type = Column(String(50), nullable=False) # TEMPERATURE, HUMIDITY, COMBO
    assigned_container_id = Column(String(50), ForeignKey("containers.container_id"), nullable=True, index=True)
    calibration_status = Column(String(50), nullable=False, default="Valid") # Valid, Expired, Failed
    calibration_date = Column(DateTime, nullable=False)
    sensor_health = Column(String(50), nullable=False, default="Healthy") # Healthy, Warning, Faulty, Offline
    issue_type = Column(String(80), nullable=True)
    ground_truth_label = Column(String(100), nullable=True)
    source_calibration_status = Column(String(50), nullable=True)

    container = relationship("Container", back_populates="sensors")
    readings = relationship("SensorReading", back_populates="sensor", cascade="all, delete-orphan")
    excursions = relationship("Excursion", back_populates="sensor")
    alerts = relationship("Alert", back_populates="sensor")
    calibration_history = relationship("SensorCalibrationEvent", back_populates="sensor", cascade="all, delete-orphan", order_by="SensorCalibrationEvent.changed_at")
