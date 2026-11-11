from sqlalchemy import Column, String, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin

class Container(Base, TimestampMixin):
    __tablename__ = "containers"

    container_id = Column(String(50), primary_key=True, index=True) # e.g. CNT-000001
    assigned_shipment_id = Column(String(50), ForeignKey("shipments.shipment_id"), nullable=True, index=True)
    container_type = Column(String(100), nullable=False) # e.g. Refrigerated Reefer, Insulated Dry Ice, Active Cryo Box
    capacity = Column(Float, nullable=False) # in Liters or Kg
    status = Column(String(50), nullable=False, default="Available")
    # States: Available, Assigned, In_Transit, Maintenance, Retired

    shipment = relationship("Shipment", back_populates="containers")
    sensors = relationship("Sensor", back_populates="container")
