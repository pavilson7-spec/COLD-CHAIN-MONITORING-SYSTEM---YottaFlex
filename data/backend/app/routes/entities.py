from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.user import User
from app.models.product import Product
from app.models.shipment import Shipment
from app.models.container import Container
from app.models.sensor import Sensor
from app.models.sensor_reading import SensorReading
from app.models.route_stop import RouteStop
from app.models.threshold_policy import ThresholdPolicy
from app.models.excursion import Excursion
from app.models.custody_event import CustodyEvent
from app.models.corrective_action import CorrectiveAction
from app.models.alert import Alert
from app.models.excursion_status_event import ExcursionStatusEvent
from app.models.container_assignment import ContainerShipmentAssignment
from app.models.sensor_calibration_event import SensorCalibrationEvent
from app.models.corrective_action_status_event import CorrectiveActionStatusEvent
from app.schemas.all_schemas import *
from app.services.excursion_engine import ExcursionRuleEngine

router = APIRouter(tags=["Core Entities"])

# --- PRODUCTS ---
@router.get("/products", response_model=List[ProductResponse])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Product).offset(skip).limit(limit).all()

@router.post("/products", response_model=ProductResponse)
def create_product(
    product_in: ProductCreate, 
    db: Session = Depends(get_db), 
    user: User = Depends(require_roles(["Quality Engineer", "Production Planner", "OT/IT Administrator"]))
):
    if db.query(Product).filter(Product.product_id == product_in.product_id).first():
        raise HTTPException(status_code=400, detail="Product ID already exists")
    product = Product(**product_in.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

# --- SHIPMENTS ---
@router.get("/shipments", response_model=List[ShipmentResponse])
def get_shipments(skip: int = 0, limit: int = 100, status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Shipment)
    if status:
        query = query.filter(Shipment.shipment_status == status)
    return query.order_by(Shipment.departure_time.desc()).offset(skip).limit(limit).all()

@router.get("/shipments/{shipment_id}", response_model=ShipmentResponse)
def get_shipment(shipment_id: str, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment

@router.put("/shipments/{shipment_id}/status", response_model=ShipmentResponse)
def transition_shipment(
    shipment_id: str,
    transition: ShipmentStatusTransition,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["Plant Operator", "Production Planner", "OT/IT Administrator"])),
):
    shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    allowed = {
        "Created": {"In_Transit", "Cancelled"},
        "In_Transit": {"Delayed", "Delivered", "Cancelled"},
        "Delayed": {"In_Transit", "Delivered", "Cancelled"},
        "Delivered": set(),
        "Cancelled": set(),
    }
    if transition.status not in allowed.get(shipment.shipment_status, set()):
        raise HTTPException(status_code=409, detail=f"Invalid shipment transition: {shipment.shipment_status} to {transition.status}")
    timestamp = transition.actual_delivery_time or datetime.now(timezone.utc)
    if transition.status == "Delivered" and timestamp < shipment.departure_time:
        raise HTTPException(status_code=400, detail="Delivery cannot occur before departure")
    prior = shipment.shipment_status
    shipment.shipment_status = transition.status
    if transition.status == "Delivered":
        shipment.actual_delivery_time = timestamp
        assignments = db.query(ContainerShipmentAssignment).filter(
            ContainerShipmentAssignment.shipment_id == shipment_id
        ).all()
        for assignment in assignments:
            assignment.released_at = timestamp
            assignment.assignment_status = "Released"
            container = db.query(Container).filter(Container.container_id == assignment.container_id).first()
            if container and container.assigned_shipment_id == shipment_id:
                container.assigned_shipment_id = None
                container.status = "Available"
    elif transition.status == "In_Transit":
        for assignment in db.query(ContainerShipmentAssignment).filter(ContainerShipmentAssignment.shipment_id == shipment_id).all():
            container = db.query(Container).filter(Container.container_id == assignment.container_id).first()
            if container:
                container.status = "In_Transit"
    db.add(CustodyEvent(
        event_id=f"CST-{shipment_id}-{int(timestamp.timestamp())}",
        shipment_id=shipment_id,
        event_timestamp=timestamp,
        event_type="STATUS_CHANGE",
        from_party=prior,
        to_party=transition.status,
        location=shipment.destination if transition.status == "Delivered" else shipment.origin,
        condition_status="Normal",
        notes=transition.note or f"Status changed by {user.username}",
    ))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A shipment event with this timestamp already exists")
    db.refresh(shipment)
    return shipment

@router.post("/shipments", response_model=ShipmentResponse)
def create_shipment(
    shipment_in: ShipmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["Production Planner", "Plant Operator", "OT/IT Administrator"]))
):
    if db.query(Shipment).filter(Shipment.shipment_id == shipment_in.shipment_id).first():
        raise HTTPException(status_code=400, detail="Shipment ID already exists")
    if not db.query(Product).filter(Product.product_id == shipment_in.product_id).first():
        raise HTTPException(status_code=404, detail="Product not found")
    # Validate chronological constraint: Delivery before departure
    if shipment_in.actual_delivery_time and shipment_in.actual_delivery_time < shipment_in.departure_time:
        raise HTTPException(status_code=400, detail="Invalid chronological order: Delivery cannot occur before departure")
    shipment = Shipment(**shipment_in.dict())
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    return shipment

# --- CONTAINERS ---
@router.get("/containers", response_model=List[ContainerResponse])
def get_containers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Container).offset(skip).limit(limit).all()

@router.post("/containers", response_model=ContainerResponse)
def create_container(
    container_in: ContainerCreate, 
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["Production Planner", "Plant Operator", "OT/IT Administrator"]))
):
    if db.query(Container).filter(Container.container_id == container_in.container_id).first():
        raise HTTPException(status_code=400, detail="Container ID already exists")
    if container_in.assigned_shipment_id and not db.query(Shipment).filter(Shipment.shipment_id == container_in.assigned_shipment_id).first():
        raise HTTPException(status_code=404, detail="Assigned shipment not found")
    cnt = Container(**container_in.dict())
    db.add(cnt)
    db.commit()
    db.refresh(cnt)
    return cnt

@router.post("/containers/{container_id}/assign/{shipment_id}")
def assign_container_to_shipment(
    container_id: str,
    shipment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["Production Planner", "OT/IT Administrator"])),
):
    container = db.query(Container).filter(Container.container_id == container_id).first()
    shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
    if not container or not shipment:
        raise HTTPException(status_code=404, detail="Container or shipment not found")
    if container.status not in {"Available", "Assigned"}:
        raise HTTPException(status_code=409, detail=f"Container is not available: {container.status}")
    sensors = db.query(Sensor).filter(Sensor.assigned_container_id == container_id).all()
    if not sensors or any(s.calibration_status != "Valid" or s.sensor_health != "Healthy" for s in sensors):
        raise HTTPException(status_code=409, detail="Container must have healthy, calibrated sensors before assignment")
    collision = db.query(ContainerShipmentAssignment).filter(
        ContainerShipmentAssignment.container_id == container_id,
        ContainerShipmentAssignment.assigned_at <= shipment.departure_time,
        (ContainerShipmentAssignment.released_at.is_(None) | (ContainerShipmentAssignment.released_at > shipment.departure_time)),
    ).first()
    if collision:
        raise HTTPException(status_code=409, detail="Container is already assigned during this shipment")
    assignment = ContainerShipmentAssignment(
        container_id=container_id,
        shipment_id=shipment_id,
        assigned_at=shipment.departure_time,
        released_at=shipment.actual_delivery_time,
        assignment_status="Released" if shipment.shipment_status == "Delivered" else "Assigned",
    )
    container.assigned_shipment_id = shipment_id
    container.status = "In_Transit" if shipment.shipment_status == "In_Transit" else "Assigned"
    db.add(assignment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Container already has an assignment for this shipment")
    return {"container_id": container_id, "shipment_id": shipment_id, "assigned_at": assignment.assigned_at, "status": assignment.assignment_status}

# --- SENSORS ---
@router.get("/sensors", response_model=List[SensorResponse])
def get_sensors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Sensor).offset(skip).limit(limit).all()

@router.post("/sensors", response_model=SensorResponse)
def create_sensor(
    sensor_in: SensorCreate, 
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["Quality Engineer", "OT/IT Administrator"]))
):
    if db.query(Sensor).filter(Sensor.sensor_id == sensor_in.sensor_id).first():
        raise HTTPException(status_code=400, detail="Sensor ID already exists")
    if sensor_in.assigned_container_id and not db.query(Container).filter(Container.container_id == sensor_in.assigned_container_id).first():
        raise HTTPException(status_code=404, detail="Assigned container not found")
    sensor = Sensor(**sensor_in.dict())
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    return sensor

@router.put("/sensors/{sensor_id}/calibration", response_model=SensorResponse)
def update_sensor_calibration(
    sensor_id: str,
    update: SensorCalibrationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["Maintenance Engineer", "Quality Engineer", "OT/IT Administrator"])),
):
    sensor = db.query(Sensor).filter(Sensor.sensor_id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    prior = sensor.calibration_status
    if prior != update.calibration_status or sensor.calibration_date != update.calibration_date:
        db.add(SensorCalibrationEvent(
            sensor_id=sensor_id,
            from_status=prior,
            to_status=update.calibration_status,
            calibration_date=update.calibration_date,
            changed_by=user.username,
            note=update.note,
        ))
    sensor.calibration_status = update.calibration_status
    sensor.calibration_date = update.calibration_date
    sensor.sensor_health = "Healthy" if update.calibration_status == "Valid" else "Faulty"
    db.commit()
    db.refresh(sensor)
    return sensor

@router.get("/sensors/{sensor_id}/calibration-history", response_model=List[LifecycleEventResponse])
def get_sensor_calibration_history(sensor_id: str, db: Session = Depends(get_db)):
    if not db.query(Sensor.sensor_id).filter(Sensor.sensor_id == sensor_id).first():
        raise HTTPException(status_code=404, detail="Sensor not found")
    return db.query(SensorCalibrationEvent).filter(SensorCalibrationEvent.sensor_id == sensor_id).order_by(SensorCalibrationEvent.changed_at.asc()).all()

# --- SENSOR READINGS ---
@router.get("/readings", response_model=List[SensorReadingResponse])
def get_sensor_readings(
    shipment_id: Optional[str] = None, 
    sensor_id: Optional[str] = None, 
    skip: int = 0, 
    limit: int = 500, 
    db: Session = Depends(get_db)
):
    query = db.query(SensorReading)
    if shipment_id:
        query = query.filter(SensorReading.shipment_id == shipment_id)
    if sensor_id:
        query = query.filter(SensorReading.sensor_id == sensor_id)
    return query.order_by(SensorReading.timestamp.asc()).offset(skip).limit(limit).all()

@router.post("/readings", response_model=SensorReadingResponse)
def create_sensor_reading(
    reading_in: SensorReadingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["Plant Operator", "OT/IT Administrator"])),
):
    sensor = db.query(Sensor).filter(Sensor.sensor_id == reading_in.sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    if db.query(SensorReading).filter(
        SensorReading.sensor_id == reading_in.sensor_id,
        SensorReading.timestamp == reading_in.timestamp,
    ).first():
        raise HTTPException(status_code=409, detail="A reading already exists for this sensor and timestamp")
    if reading_in.shipment_id:
        shipment = db.query(Shipment).filter(Shipment.shipment_id == reading_in.shipment_id).first()
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")
        if sensor.assigned_container_id:
            assigned = db.query(ContainerShipmentAssignment).filter(
                ContainerShipmentAssignment.container_id == sensor.assigned_container_id,
                ContainerShipmentAssignment.shipment_id == reading_in.shipment_id,
                ContainerShipmentAssignment.assigned_at <= reading_in.timestamp,
                (ContainerShipmentAssignment.released_at.is_(None) | (ContainerShipmentAssignment.released_at >= reading_in.timestamp)),
            ).first()
            if not assigned:
                raise HTTPException(status_code=400, detail="Sensor is not assigned to a container on this shipment")
    payload = reading_in.model_dump()
    out_of_range = (
        reading_in.temperature is not None and not -80 <= reading_in.temperature <= 70
    ) or (reading_in.humidity is not None and not 0 <= reading_in.humidity <= 100)
    if out_of_range:
        payload["is_anomaly"] = True
        payload["issue_type"] = payload["issue_type"] or "PHYSICAL_OUT_OF_BOUNDS"
        payload["ground_truth_label"] = payload["ground_truth_label"] or "CRITICAL_HARDWARE_ANOMALY"
        payload["source_reading_id"] = payload["source_reading_id"] or reading_in.reading_id
    reading = SensorReading(**payload)
    db.add(reading)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Reading conflicts with an existing record or reference")
    db.refresh(reading)
    return reading

# --- ROUTE STOPS ---
@router.get("/route-stops", response_model=List[RouteStopResponse])
def get_route_stops(shipment_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(RouteStop)
    if shipment_id:
        query = query.filter(RouteStop.shipment_id == shipment_id)
    return query.order_by(RouteStop.stop_sequence.asc()).all()

@router.post("/route-stops", response_model=RouteStopResponse)
def create_route_stop(
    stop_in: RouteStopCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["Production Planner", "Plant Operator", "OT/IT Administrator"])),
):
    if not db.query(Shipment).filter(Shipment.shipment_id == stop_in.shipment_id).first():
        raise HTTPException(status_code=404, detail="Shipment not found")
    if db.query(RouteStop).filter(RouteStop.stop_id == stop_in.stop_id).first():
        raise HTTPException(status_code=409, detail="Route stop ID already exists")
    if db.query(RouteStop).filter(
        RouteStop.shipment_id == stop_in.shipment_id,
        RouteStop.stop_sequence == stop_in.stop_sequence,
    ).first():
        raise HTTPException(status_code=409, detail="Route stop sequence already exists for this shipment")
    stop = RouteStop(**stop_in.model_dump())
    db.add(stop)
    db.commit()
    db.refresh(stop)
    return stop

# --- THRESHOLD POLICIES ---
@router.get("/threshold-policies", response_model=List[ThresholdPolicyResponse])
def get_threshold_policies(product_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(ThresholdPolicy)
    if product_id:
        query = query.filter(ThresholdPolicy.product_id == product_id)
    return query.all()

@router.post("/threshold-policies", response_model=ThresholdPolicyResponse)
def create_threshold_policy(
    policy_in: ThresholdPolicyCreate, 
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["Quality Engineer", "OT/IT Administrator"]))
):
    if not db.query(Product).filter(Product.product_id == policy_in.product_id).first():
        raise HTTPException(status_code=404, detail="Product not found")
    if db.query(ThresholdPolicy).filter(ThresholdPolicy.policy_id == policy_in.policy_id).first():
        raise HTTPException(status_code=409, detail="Policy ID already exists")
    if policy_in.policy_status == "Active" and policy_in.is_active:
        overlap = db.query(ThresholdPolicy).filter(
            ThresholdPolicy.product_id == policy_in.product_id,
            ThresholdPolicy.is_active.is_(True),
            ThresholdPolicy.policy_status == "Active",
            (ThresholdPolicy.effective_end.is_(None) | (ThresholdPolicy.effective_end > policy_in.effective_start)),
            or_(policy_in.effective_end is None, ThresholdPolicy.effective_start < policy_in.effective_end),
        ).first()
        if overlap:
            raise HTTPException(status_code=409, detail="Active policy dates overlap an existing policy for this product")
    pol = ThresholdPolicy(**policy_in.dict())
    db.add(pol)
    db.commit()
    db.refresh(pol)
    return pol

# --- EXCURSIONS ---
@router.get("/excursions", response_model=List[ExcursionResponse])
def get_excursions(shipment_id: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Excursion)
    if shipment_id:
        query = query.filter(Excursion.shipment_id == shipment_id)
    if status:
        query = query.filter(Excursion.status == status)
    return query.order_by(Excursion.start_time.desc()).all()

@router.get("/excursions/{excursion_id}/history", response_model=List[ExcursionStatusEventResponse])
def get_excursion_history(excursion_id: str, db: Session = Depends(get_db)):
    if not db.query(Excursion.excursion_id).filter(Excursion.excursion_id == excursion_id).first():
        raise HTTPException(status_code=404, detail="Excursion not found")
    return db.query(ExcursionStatusEvent).filter(
        ExcursionStatusEvent.excursion_id == excursion_id
    ).order_by(ExcursionStatusEvent.changed_at.asc()).all()

EXCURSION_TRANSITIONS = {
    "OPEN": {"ACKNOWLEDGED", "UNDER_INVESTIGATION", "CORRECTIVE_ACTION_REQUIRED", "RESOLVED"},
    "ACKNOWLEDGED": {"UNDER_INVESTIGATION", "CORRECTIVE_ACTION_REQUIRED", "RESOLVED"},
    "UNDER_INVESTIGATION": {"CORRECTIVE_ACTION_REQUIRED", "RESOLVED"},
    "CORRECTIVE_ACTION_REQUIRED": {"UNDER_INVESTIGATION", "RESOLVED"},
    "RESOLVED": {"CLOSED", "UNDER_INVESTIGATION"},
    "CLOSED": set(),
}

@router.put("/excursions/{excursion_id}/status", response_model=ExcursionResponse)
def transition_excursion(
    excursion_id: str,
    transition: ExcursionTransition,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["Quality Engineer", "OT/IT Administrator"])),
):
    excursion = db.query(Excursion).filter(Excursion.excursion_id == excursion_id).first()
    if not excursion:
        raise HTTPException(status_code=404, detail="Excursion not found")
    target = transition.status.strip().upper().replace(" ", "_")
    current = excursion.status.upper().replace(" ", "_")
    if target not in EXCURSION_TRANSITIONS.get(current, set()):
        raise HTTPException(status_code=409, detail=f"Invalid excursion transition: {excursion.status} to {target}")
    db.add(ExcursionStatusEvent(
        excursion_id=excursion_id,
        from_status=excursion.status,
        to_status=target,
        changed_by=user.username,
        note=transition.note,
    ))
    excursion.status = target
    db.commit()
    db.refresh(excursion)
    return excursion

@router.put("/excursions/{excursion_id}/review", response_model=ExcursionResponse)
def review_excursion(
    excursion_id: str,
    decision: ExcursionReview,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["Quality Engineer", "OT/IT Administrator"])),
):
    excursion = db.query(Excursion).filter(Excursion.excursion_id == excursion_id).first()
    if not excursion:
        raise HTTPException(status_code=404, detail="Excursion not found")
    excursion.review_status = decision.review_status
    excursion.reviewed_by = user.username
    excursion.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(excursion)
    return excursion

@router.post("/excursions/evaluate/{shipment_id}")
def evaluate_shipment_excursions(
    shipment_id: str, 
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["Quality Engineer", "Plant Operator", "OT/IT Administrator"]))
):
    engine = ExcursionRuleEngine(db)
    result = engine.evaluate_shipment_readings(shipment_id)
    return result

# --- CUSTODY EVENTS ---
@router.get("/custody-events", response_model=List[CustodyEventResponse])
def get_custody_events(shipment_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(CustodyEvent)
    if shipment_id:
        query = query.filter(CustodyEvent.shipment_id == shipment_id)
    return query.order_by(CustodyEvent.event_timestamp.asc()).all()

@router.post("/custody-events", response_model=CustodyEventResponse)
def create_custody_event(
    event_in: CustodyEventCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["Plant Operator", "Production Planner", "OT/IT Administrator"])),
):
    if not db.query(Shipment).filter(Shipment.shipment_id == event_in.shipment_id).first():
        raise HTTPException(status_code=404, detail="Shipment not found")
    evt = CustodyEvent(**event_in.dict())
    db.add(evt)
    db.commit()
    db.refresh(evt)
    return evt

# --- CORRECTIVE ACTIONS ---
@router.get("/corrective-actions", response_model=List[CorrectiveActionResponse])
def get_corrective_actions(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(CorrectiveAction)
    if status:
        query = query.filter(CorrectiveAction.status == status)
    return query.order_by(CorrectiveAction.created_at.desc()).all()

@router.get("/corrective-actions/{action_id}/history", response_model=List[LifecycleEventResponse])
def get_corrective_action_history(action_id: str, db: Session = Depends(get_db)):
    if not db.query(CorrectiveAction.action_id).filter(CorrectiveAction.action_id == action_id).first():
        raise HTTPException(status_code=404, detail="Corrective action not found")
    return db.query(CorrectiveActionStatusEvent).filter(CorrectiveActionStatusEvent.action_id == action_id).order_by(CorrectiveActionStatusEvent.changed_at.asc()).all()

@router.put("/corrective-actions/{action_id}", response_model=CorrectiveActionResponse)
def update_corrective_action(
    action_id: str,
    action_update: CorrectiveActionBase,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["Quality Engineer", "OT/IT Administrator"]))
):
    action = db.query(CorrectiveAction).filter(CorrectiveAction.action_id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    transitions = {
        "OPEN": {"ACKNOWLEDGED", "IN_PROGRESS", "RESOLVED", "CLOSED"},
        "ACKNOWLEDGED": {"IN_PROGRESS", "RESOLVED", "CLOSED"},
        "IN_PROGRESS": {"RESOLVED"},
        "RESOLVED": {"CLOSED", "IN_PROGRESS"},
        "CLOSED": set(),
    }
    target = action_update.status.upper()
    if target != action.status.upper() and target not in transitions.get(action.status.upper(), set()):
        raise HTTPException(status_code=409, detail=f"Invalid corrective action transition: {action.status} to {target}")
    prior_status = action.status
    for field, val in action_update.model_dump().items():
        setattr(action, field, val)
    if target != prior_status.upper():
        db.add(CorrectiveActionStatusEvent(
            action_id=action_id,
            from_status=prior_status,
            to_status=target,
            changed_by=user.username,
            note=action_update.resolution_notes,
        ))
    if target in {"RESOLVED", "CLOSED"} and not action.completed_date:
        action.completed_date = datetime.now(timezone.utc)
    db.commit()
    db.refresh(action)
    return action

# --- ALERTS ---
@router.get("/alerts", response_model=List[AlertResponse])
def get_alerts(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Alert)
    if status:
        query = query.filter(Alert.resolution_status == status)
    return query.order_by(Alert.created_at.desc()).all()

@router.put("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["Plant Operator", "Maintenance Engineer", "Quality Engineer", "OT/IT Administrator"])),
):
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledgement_status = "ACKNOWLEDGED"
    db.commit()
    return {"message": "Alert acknowledged", "alert_id": alert_id}
