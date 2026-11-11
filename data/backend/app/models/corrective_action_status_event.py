from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class CorrectiveActionStatusEvent(Base):
    __tablename__ = "corrective_action_status_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(String(50), ForeignKey("corrective_actions.action_id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    changed_by = Column(String(100), nullable=False)
    note = Column(String(500), nullable=True)
    changed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    action = relationship("CorrectiveAction", back_populates="status_history")
