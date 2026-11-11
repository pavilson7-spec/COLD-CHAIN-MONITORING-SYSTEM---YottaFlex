from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base
from app.models.base import TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(50), nullable=False, default="Plant Operator")
    # Roles: "Plant Operator", "Quality Engineer", "Production Planner", "OT/IT Administrator"
    is_active = Column(Boolean, default=True, nullable=False)
