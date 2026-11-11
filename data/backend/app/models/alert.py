from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin

class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    alert_id = Column(String(50), primary_key=True, index=True)
    shipment_id = Column(String(50), ForeignKey("shipments.shipment_id"), nullable=False, index=True)
    sensor_id = Column(String(100), ForeignKey("sensors.sensor_id"), nullable=False, index=True)
    excursion_id = Column(String(50), ForeignKey("excursions.excursion_id"), nullable=True, index=True)
    severity = Column(String(50), nullable=False) # WARNING, CRITICAL
    description = Column(String(500), nullable=False)
    acknowledgement_status = Column(String(50), nullable=False, default="UNACKNOWLEDGED") # UNACKNOWLEDGED, ACKNOWLEDGED
    resolution_status = Column(String(50), nullable=False, default="OPEN") # OPEN, RESOLVED, DISMISSED

    shipment = relationship("Shipment", back_populates="alerts")
    sensor = relationship("Sensor", back_populates="alerts")
    excursion = relationship("Excursion", back_populates="alerts")
