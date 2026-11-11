from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.shipment import Shipment
from app.models.container import Container
from app.models.sensor import Sensor
from app.models.excursion import Excursion
from app.models.alert import Alert
from app.models.corrective_action import CorrectiveAction
from app.schemas.all_schemas import DashboardMetrics
from app.validators.data_validator import DataValidator

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/metrics", response_model=DashboardMetrics)
def get_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_shipments = db.query(Shipment).count()
    active_shipments = db.query(Shipment).filter(Shipment.shipment_status.in_(["Created", "In_Transit"])).count()
    delivered_shipments = db.query(Shipment).filter(Shipment.shipment_status == "Delivered").count()
    total_containers = db.query(Container).count()
    healthy_sensors = db.query(Sensor).filter(Sensor.sensor_health == "Healthy").count()
    failed_sensors = db.query(Sensor).filter(Sensor.sensor_health.in_(["Faulty", "Offline", "Warning"])).count()
    active_excursions = db.query(Excursion).filter(Excursion.status == "OPEN").count()
    critical_alerts = db.query(Alert).filter(Alert.severity == "CRITICAL", Alert.resolution_status == "OPEN").count()
    open_corrective_actions = db.query(CorrectiveAction).filter(CorrectiveAction.status == "OPEN").count()

    validator = DataValidator(db)
    validation_summary = validator.validate_all()
    success_rate = validation_summary.get("success_rate", 100.0)

    return DashboardMetrics(
        total_shipments=total_shipments,
        active_shipments=active_shipments,
        delivered_shipments=delivered_shipments,
        total_containers=total_containers,
        healthy_sensors=healthy_sensors,
        failed_sensors=failed_sensors,
        active_excursions=active_excursions,
        critical_alerts=critical_alerts,
        open_corrective_actions=open_corrective_actions,
        data_validation_success_rate=success_rate
    )
