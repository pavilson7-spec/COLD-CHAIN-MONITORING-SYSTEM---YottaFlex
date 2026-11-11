from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    reading_id = Column(String(150), primary_key=True, index=True) # e.g. RDG-{sensor-id}-{timestamp}
    sensor_id = Column(String(100), ForeignKey("sensors.sensor_id"), nullable=False, index=True)
    shipment_id = Column(String(50), ForeignKey("shipments.shipment_id"), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    temperature = Column(Float, nullable=True) # in Celsius
    humidity = Column(Float, nullable=True) # in % RH
    battery_level = Column(Float, nullable=True) # in %
    is_anomaly = Column(Boolean, default=False, nullable=False)
    issue_type = Column(String(80), nullable=True)
    ground_truth_label = Column(String(100), nullable=True)
    source_reading_id = Column(String(150), nullable=True)

    sensor = relationship("Sensor", back_populates="readings")
    shipment = relationship("Shipment")

    __table_args__ = (
        Index("ix_sensor_readings_shipment_timestamp", "shipment_id", "timestamp"),
        UniqueConstraint("sensor_id", "timestamp", name="uq_sensor_readings_sensor_timestamp"),
    )
