import csv
import io
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.product import Product
from app.models.shipment import Shipment
from app.models.container import Container
from app.models.sensor import Sensor
from app.models.sensor_reading import SensorReading
from app.models.route_stop import RouteStop
from app.models.threshold_policy import ThresholdPolicy
from app.models.excursion import Excursion
from app.models.excursion_status_event import ExcursionStatusEvent
from app.models.custody_event import CustodyEvent
from app.models.corrective_action import CorrectiveAction
from app.models.alert import Alert

router = APIRouter(prefix="/exports", tags=["Data Export"])
EXPORTS = {
    "products": Product,
    "shipments": Shipment,
    "containers": Container,
    "sensors": Sensor,
    "readings": SensorReading,
    "route-stops": RouteStop,
    "threshold-policies": ThresholdPolicy,
    "excursions": Excursion,
    "excursion-status-events": ExcursionStatusEvent,
    "custody-events": CustodyEvent,
    "corrective-actions": CorrectiveAction,
    "alerts": Alert,
}


def _records(entity_name: str, db: Session):
    model = EXPORTS.get(entity_name)
    if model is None:
        raise HTTPException(status_code=404, detail=f"Unknown export entity: {entity_name}")
    columns = [column.key for column in inspect(model).columns]
    rows = db.query(model).order_by(*[getattr(model, c) for c in columns if c.endswith("_id")][:1]).all()
    return columns, [{column: getattr(row, column) for column in columns} for row in rows]


@router.get("/csv/{entity_name}")
def export_entity_csv(entity_name: str, db: Session = Depends(get_db)):
    columns, rows = _records(entity_name, db)
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: value.isoformat() if hasattr(value, "isoformat") else value for key, value in row.items()})
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={entity_name}_export.csv"},
    )


@router.get("/json/{entity_name}")
def export_entity_json(entity_name: str, db: Session = Depends(get_db)):
    _, rows = _records(entity_name, db)
    return Response(
        content=json.dumps(rows, indent=2, default=lambda value: value.isoformat() if hasattr(value, "isoformat") else str(value)),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={entity_name}_export.json"},
    )
