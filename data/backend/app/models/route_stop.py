from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin

class RouteStop(Base, TimestampMixin):
    __tablename__ = "route_stops"

    stop_id = Column(String(50), primary_key=True, index=True)
    shipment_id = Column(String(50), ForeignKey("shipments.shipment_id"), nullable=False, index=True)
    stop_sequence = Column(Integer, nullable=False)
    location_name = Column(String(150), nullable=False)
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)
    planned_arrival = Column(DateTime, nullable=False)
    actual_arrival = Column(DateTime, nullable=True)
    departure_time = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="Pending") # Pending, Arrived, Departed, Skipped
    issue_type = Column(String(80), nullable=True)
    ground_truth_label = Column(String(100), nullable=True)

    shipment = relationship("Shipment", back_populates="route_stops")

    __table_args__ = (
        Index("ix_route_stops_shipment_seq", "shipment_id", "stop_sequence", unique=True),
    )
