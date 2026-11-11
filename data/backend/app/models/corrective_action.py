from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin

class CorrectiveAction(Base, TimestampMixin):
    __tablename__ = "corrective_actions"

    action_id = Column(String(50), primary_key=True, index=True)
    excursion_id = Column(String(50), ForeignKey("excursions.excursion_id"), nullable=False, index=True)
    assigned_user = Column(String(100), nullable=False)
    action_description = Column(String(500), nullable=False)
    priority = Column(String(50), nullable=False, default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), nullable=False, default="OPEN") # OPEN, ACKNOWLEDGED, IN_PROGRESS, RESOLVED, CLOSED
    resolution_notes = Column(String(1000), nullable=True)
    completed_date = Column(DateTime, nullable=True)

    excursion = relationship("Excursion", back_populates="corrective_actions")
    status_history = relationship("CorrectiveActionStatusEvent", back_populates="action", cascade="all, delete-orphan", order_by="CorrectiveActionStatusEvent.changed_at")
