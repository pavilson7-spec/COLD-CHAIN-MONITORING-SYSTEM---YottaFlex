from sqlalchemy import Column, String, Float, Integer, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin

class Product(Base, TimestampMixin):
    __tablename__ = "products"

    product_id = Column(String(50), primary_key=True, index=True)
    product_name = Column(String(150), nullable=False, unique=True, index=True)
    product_category = Column(String(100), nullable=False, index=True)
    temperature_min = Column(Float, nullable=False)
    temperature_max = Column(Float, nullable=False)
    humidity_min = Column(Float, nullable=False)
    humidity_max = Column(Float, nullable=False)
    permissible_excursion_duration = Column(Integer, nullable=False, default=30) # in minutes
    product_status = Column(String(50), nullable=False, default="Active") # Active, Discontinued, Testing

    __table_args__ = (
        CheckConstraint('temperature_min <= temperature_max', name='check_temp_min_max'),
        CheckConstraint('humidity_min <= humidity_max', name='check_humidity_min_max'),
        CheckConstraint('permissible_excursion_duration >= 0', name='check_permissible_duration_non_negative'),
    )

    shipments = relationship("Shipment", back_populates="product", cascade="all, delete-orphan")
    threshold_policies = relationship("ThresholdPolicy", back_populates="product", cascade="all, delete-orphan")
