from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin

class CustodyEvent(Base, TimestampMixin):
    __tablename__ = "custody_events"

    event_id = Column(String(50), primary_key=True, index=True)
    shipment_id = Column(String(50), ForeignKey("shipments.shipment_id"), nullable=False, index=True)
    event_timestamp = Column(DateTime, nullable=False, index=True)
    event_type = Column(String(50), nullable=False) # DEPARTURE, HANDOVER, INSPECTION, ARRIVAL, TAMPER_ALERT
    from_party = Column(String(100), nullable=False)
    to_party = Column(String(100), nullable=False)
    location = Column(String(150), nullable=False)
    condition_status = Column(String(50), nullable=False, default="Normal") # Normal, Compromised, Inspected
    notes = Column(String(255), nullable=True)

    shipment = relationship("Shipment", back_populates="custody_events")
