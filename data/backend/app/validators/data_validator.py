from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.shipment import Shipment
from app.models.container import Container
from app.models.container_assignment import ContainerShipmentAssignment
from app.models.sensor import Sensor
from app.models.sensor_reading import SensorReading
from app.models.threshold_policy import ThresholdPolicy
from app.models.excursion import Excursion
from app.models.route_stop import RouteStop
from app.models.corrective_action import CorrectiveAction
from app.models.product import Product


class DataValidator:
    """Run database integrity checks and report observed exceptions honestly."""

    def __init__(self, db: Session):
        self.db = db

    def validate_all(self) -> Dict[str, Any]:
        details = []

        def add(scenario, issue_type, violations, expected, passed=True):
            details.append({
                "scenario": scenario,
                "issue_type": issue_type,
                "violations_found": violations,
                "expected_behavior": expected,
                "status": "PASS" if passed else "FAIL",
            })

        physical = self.db.query(SensorReading).filter(
            (SensorReading.temperature < -80) | (SensorReading.temperature > 70) |
            (SensorReading.humidity < 0) | (SensorReading.humidity > 100)
        ).all()
        physical_unlabelled = sum(not r.is_anomaly or not r.issue_type or not r.ground_truth_label for r in physical)
        add("Physical measurement bounds", "PHYSICAL_OUT_OF_BOUNDS", len(physical),
            "Out-of-range readings are labelled and produce critical hardware excursions.", physical_unlabelled == 0)

        readings = self.db.query(SensorReading.sensor_id, SensorReading.shipment_id, SensorReading.timestamp).filter(
            SensorReading.shipment_id.isnot(None)
        ).order_by(SensorReading.sensor_id, SensorReading.timestamp).all()
        by_sensor = defaultdict(list)
        for row in readings:
            by_sensor[(row.sensor_id, row.shipment_id)].append(row.timestamp)
        gaps = []
        for (sensor_id, shipment_id), timestamps in by_sensor.items():
            for previous, current in zip(timestamps, timestamps[1:]):
                minutes = (current - previous).total_seconds() / 60
                if minutes > 10:
                    gaps.append((sensor_id, shipment_id, previous, current))
        gap_events = self.db.query(Excursion).filter(Excursion.excursion_type == "MISSING_INTERVAL").count()
        add("Missing telemetry intervals", "TELEMETRY_DROPOUT", len(gaps),
            "Every gap over ten minutes is recorded as an unverified interval.", len(gaps) <= gap_events)

        invalid_deliveries = self.db.query(Shipment).filter(
            Shipment.actual_delivery_time.isnot(None), Shipment.actual_delivery_time < Shipment.departure_time
        ).all()
        unlabeled_deliveries = sum(not s.issue_type or not s.ground_truth_label or s.source_actual_delivery_time is None for s in invalid_deliveries)
        add("Shipment delivery chronology", "CHRONOLOGICAL_INVERSION", len(invalid_deliveries),
            "Invalid delivery timestamps are rejected at input or retained with explicit anomaly provenance.", unlabeled_deliveries == 0)

        policy_mismatches = self.db.query(Excursion).join(ThresholdPolicy, Excursion.policy_id == ThresholdPolicy.policy_id).join(
            Shipment, Excursion.shipment_id == Shipment.shipment_id
        ).filter(ThresholdPolicy.product_id != Shipment.product_id).count()
        add("Product-specific policy selection", "POLICY_PRODUCT_MISMATCH", policy_mismatches,
            "An excursion policy belongs to the shipment product.", policy_mismatches == 0)

        undercounted = self.db.query(Excursion).filter(
            Excursion.end_time.isnot(None),
            Excursion.duration_minutes + 0.01 < func.extract("epoch", Excursion.end_time - Excursion.start_time) / 60,
        ).count()
        add("Continuous excursion duration", "CONTINUOUS_DURATION_UNDERCOUNT", undercounted,
            "Recorded duration covers the full elapsed excursion window.", undercounted == 0)

        invalid_sensors = self.db.query(Sensor).filter(Sensor.calibration_status.in_(["Expired", "Failed"])).all()
        sensors_with_telemetry = [s for s in invalid_sensors if self.db.query(SensorReading.reading_id).filter(SensorReading.sensor_id == s.sensor_id).first()]
        missing_calibration_events = sum(
            self.db.query(Excursion).filter(Excursion.sensor_id == s.sensor_id, Excursion.excursion_type == "CALIBRATION_FAILURE").count() == 0
            for s in sensors_with_telemetry
        )
        add("Sensor calibration validity", "UNCALIBRATED_TELEMETRY", len(sensors_with_telemetry),
            "Expired or failed sensors have a linked critical calibration excursion.", missing_calibration_events == 0)

        duplicate_groups = self.db.query(SensorReading.sensor_id, SensorReading.timestamp).group_by(
            SensorReading.sensor_id, SensorReading.timestamp
        ).having(func.count() > 1).count()
        add("Duplicate sensor timestamps", "DUPLICATE_SENSOR_TIMESTAMP", duplicate_groups,
            "A unique sensor and timestamp constraint rejects duplicate readings.", duplicate_groups == 0)

        unalerted_gaps = max(0, len(gaps) - gap_events)
        add("Sensor dropout detection", "SENSOR_DROPOUT", unalerted_gaps,
            "Telemetry dropouts are not treated as safe conditions and create excursions.", unalerted_gaps == 0)

        delayed_stops = self.db.query(RouteStop).filter(
            RouteStop.actual_arrival.isnot(None),
            RouteStop.actual_arrival > RouteStop.planned_arrival + timedelta(minutes=30),
        ).all()
        delayed_unlabelled = sum(not stop.issue_type or not stop.ground_truth_label for stop in delayed_stops)
        add("Route stop delay", "ROUTE_STOP_DELAY", len(delayed_stops),
            "Late route stops retain actual time and anomaly provenance and are eligible for notification.", delayed_unlabelled == 0)

        orphan_readings = self.db.query(SensorReading).outerjoin(Sensor, SensorReading.sensor_id == Sensor.sensor_id).filter(
            Sensor.sensor_id.is_(None)
        ).count()
        invalid_assignments = self.db.query(SensorReading).join(Sensor, SensorReading.sensor_id == Sensor.sensor_id).filter(
            SensorReading.shipment_id.isnot(None), Sensor.assigned_container_id.isnot(None),
            ~self.db.query(ContainerShipmentAssignment).filter(
                ContainerShipmentAssignment.container_id == Sensor.assigned_container_id,
                ContainerShipmentAssignment.shipment_id == SensorReading.shipment_id,
                ContainerShipmentAssignment.assigned_at <= SensorReading.timestamp,
                (ContainerShipmentAssignment.released_at.is_(None) | (ContainerShipmentAssignment.released_at >= SensorReading.timestamp)),
            ).exists(),
        ).count()
        add("Container and sensor assignment", "INVALID_CONTAINER_SENSOR_ASSIGNMENT", invalid_assignments,
            "Every shipment reading belongs to the sensor's container assignment at that time.", invalid_assignments == 0)

        invalid_states = self.db.query(Shipment).filter(~Shipment.shipment_status.in_(["Created", "In_Transit", "Delivered", "Delayed", "Cancelled"])).count()
        invalid_states += self.db.query(Excursion).filter(~Excursion.status.in_(["OPEN", "ACKNOWLEDGED", "UNDER_INVESTIGATION", "CORRECTIVE_ACTION_REQUIRED", "RESOLVED", "CLOSED"])).count()
        invalid_states += self.db.query(CorrectiveAction).filter(~CorrectiveAction.status.in_(["OPEN", "ACKNOWLEDGED", "IN_PROGRESS", "RESOLVED", "CLOSED"])).count()
        add("Lifecycle state values", "INVALID_STATE_TRANSITION", invalid_states,
            "Only supported lifecycle statuses are persisted; transition APIs reject illegal moves.", invalid_states == 0)

        missing_products = self.db.query(Shipment).outerjoin(Product, Shipment.product_id == Product.product_id).filter(Product.product_id.is_(None)).count()
        missing_containers = self.db.query(Container).outerjoin(Shipment, Container.assigned_shipment_id == Shipment.shipment_id).filter(
            Container.assigned_shipment_id.isnot(None), Shipment.shipment_id.is_(None)
        ).count()
        add("Foreign key references", "MISSING_FOREIGN_KEY", missing_products + missing_containers + orphan_readings,
            "Database references point to existing parent records.", missing_products + missing_containers + orphan_readings == 0)

        passed = sum(detail["status"] == "PASS" for detail in details)
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "passed_tests": passed,
            "failed_tests": len(details) - passed,
            "total_tests": len(details),
            "success_rate": round(100 * passed / len(details), 2) if details else 100.0,
            "details": details,
        }
