from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String, PrimaryKeyConstraint
from app.core.database import Base


class ContainerShipmentAssignment(Base):
    """Historical many-to-many assignment of reusable containers to shipments."""
    __tablename__ = "container_shipment_assignments"

    container_id = Column(String(50), ForeignKey("containers.container_id", ondelete="CASCADE"), nullable=False)
    shipment_id = Column(String(50), ForeignKey("shipments.shipment_id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime, nullable=False)
    released_at = Column(DateTime, nullable=True)
    assignment_status = Column(String(30), nullable=False, default="Assigned")

    __table_args__ = (PrimaryKeyConstraint("container_id", "shipment_id", name="pk_container_shipment_assignments"),)
