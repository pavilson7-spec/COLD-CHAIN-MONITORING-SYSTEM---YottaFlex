from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin

class ThresholdPolicy(Base, TimestampMixin):
    __tablename__ = "threshold_policies"

    policy_id = Column(String(50), primary_key=True, index=True)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False, index=True)
    policy_name = Column(String(150), nullable=False)
    temp_critical_low = Column(Float, nullable=False)
    temp_warning_low = Column(Float, nullable=False)
    temp_warning_high = Column(Float, nullable=False)
    temp_critical_high = Column(Float, nullable=False)
    humidity_min = Column(Float, nullable=False)
    humidity_max = Column(Float, nullable=False)
    max_excursion_duration_minutes = Column(Integer, nullable=False, default=30)
    is_active = Column(Boolean, default=True, nullable=False)
    effective_start = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    effective_end = Column(DateTime, nullable=True)
    policy_status = Column(String(30), nullable=False, default="Active")

    product = relationship("Product", back_populates="threshold_policies")
    excursions = relationship("Excursion", back_populates="policy")
