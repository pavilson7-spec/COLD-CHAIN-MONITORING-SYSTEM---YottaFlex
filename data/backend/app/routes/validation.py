from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.validators.data_validator import DataValidator

router = APIRouter(prefix="/validation", tags=["Data Validation"])

@router.get("/summary")
def get_validation_summary(db: Session = Depends(get_db)):
    validator = DataValidator(db)
    return validator.validate_all()
