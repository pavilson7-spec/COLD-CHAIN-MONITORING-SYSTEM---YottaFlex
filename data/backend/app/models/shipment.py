from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin

class Shipment(Base, TimestampMixin):
    __tablename__ = "shipments"

    shipment_id = Column(String(50), primary_key=True, index=True) # e.g. SHP-2026-000001
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False, index=True)
    origin = Column(String(150), nullable=False)
    destination = Column(String(150), nullable=False)
    departure_time = Column(DateTime, nullable=False)
    expected_delivery_time = Column(DateTime, nullable=False)
    actual_delivery_time = Column(DateTime, nullable=True)
    issue_type = Column(String(80), nullable=True)
    ground_truth_label = Column(String(100), nullable=True)
    source_actual_delivery_time = Column(DateTime, nullable=True)
    shipment_status = Column(String(50), nullable=False, default="Created")
    # States: Created, In_Transit, Delivered, Delayed, Cancelled

    product = relationship("Product", back_populates="shipments")
    containers = relationship("Container", back_populates="shipment")
    route_stops = relationship("RouteStop", back_populates="shipment", cascade="all, delete-orphan", order_by="RouteStop.stop_sequence")
    excursions = relationship("Excursion", back_populates="shipment")
    custody_events = relationship("CustodyEvent", back_populates="shipment", cascade="all, delete-orphan", order_by="CustodyEvent.event_timestamp")
    alerts = relationship("Alert", back_populates="shipment")
