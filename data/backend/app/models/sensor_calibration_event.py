from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class SensorCalibrationEvent(Base):
    __tablename__ = "sensor_calibration_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(String(100), ForeignKey("sensors.sensor_id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(String(50), nullable=False)
    to_status = Column(String(50), nullable=False)
    calibration_date = Column(DateTime, nullable=False)
    changed_by = Column(String(100), nullable=False)
    note = Column(String(500), nullable=True)
    changed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    sensor = relationship("Sensor", back_populates="calibration_history")
