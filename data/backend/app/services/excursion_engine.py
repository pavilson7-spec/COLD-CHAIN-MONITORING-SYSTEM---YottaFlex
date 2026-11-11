from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.shipment import Shipment
from app.models.sensor import Sensor
from app.models.sensor_reading import SensorReading
from app.models.threshold_policy import ThresholdPolicy
from app.models.excursion import Excursion
from app.models.alert import Alert
from app.models.corrective_action import CorrectiveAction
from app.models.excursion_status_event import ExcursionStatusEvent
from app.models.route_stop import RouteStop
from app.models.container_assignment import ContainerShipmentAssignment
from app.models.corrective_action_status_event import CorrectiveActionStatusEvent

PHYSICAL_TEMP_MIN = -80.0
PHYSICAL_TEMP_MAX = 70.0
PHYSICAL_HUMIDITY_MIN = 0.0
PHYSICAL_HUMIDITY_MAX = 100.0
EXPECTED_INTERVAL_MINUTES = 5.0
MAX_EXPECTED_GAP_MINUTES = 10.0
CALIBRATION_VALID_DAYS = 365


def _naive(value):
    return value.replace(tzinfo=None) if value and value.tzinfo else value


class ExcursionRuleEngine:
    """Evaluate a shipment's telemetry using its product's effective policy."""

    def __init__(self, db: Session):
        self.db = db
        self._policy_cache = {}

    def _policy_for(self, product_id: str, timestamp: datetime):
        timestamp = _naive(timestamp)
        if product_id not in self._policy_cache:
            self._policy_cache[product_id] = self.db.query(ThresholdPolicy).filter(
                ThresholdPolicy.product_id == product_id,
                ThresholdPolicy.is_active.is_(True),
                ThresholdPolicy.policy_status == "Active",
            ).order_by(ThresholdPolicy.effective_start.desc(), ThresholdPolicy.created_at.desc()).all()
        for policy in self._policy_cache[product_id]:
            if _naive(policy.effective_start) <= timestamp and (
                policy.effective_end is None or _naive(policy.effective_end) > timestamp
            ):
                return policy
        return None

    def _next_id(self, year: int) -> str:
        # Serialize the sequence allocation across workers for stable, unique IDs.
        self.db.execute(text("SELECT pg_advisory_xact_lock(17491001)"))
        existing = self.db.query(Excursion.excursion_id).filter(Excursion.excursion_id.like(f"EXC-{year}-%")).all()
        highest = max((int(row[0].rsplit("-", 1)[-1]) for row in existing if row[0].rsplit("-", 1)[-1].isdigit()), default=0)
        return f"EXC-{year}-{highest + 1:06d}"

    def _record(self, *, shipment, sensor, kind, start, end, duration, value=None, threshold=None,
                policy=None, severity="WARNING", cause=""):
        container_id = sensor.assigned_container_id
        existing = self.db.query(Excursion).filter(
            Excursion.shipment_id == shipment.shipment_id,
            Excursion.sensor_id == sensor.sensor_id,
            Excursion.excursion_type == kind,
            Excursion.start_time == start,
        ).first()
        if existing:
            return existing, False

        excursion_id = self._next_id(start.year)
        excursion = Excursion(
            excursion_id=excursion_id,
            shipment_id=shipment.shipment_id,
            container_id=container_id,
            sensor_id=sensor.sensor_id,
            policy_id=policy.policy_id if policy else None,
            excursion_type=kind,
            severity=severity,
            start_time=start,
            end_time=end,
            duration_minutes=max(0.0, duration),
            peak_value=value,
            threshold_limit=threshold,
            status="OPEN",
            root_cause=cause,
        )
        self.db.add(excursion)
        self.db.add(ExcursionStatusEvent(
            excursion_id=excursion_id,
            from_status=None,
            to_status="OPEN",
            changed_by="Excursion Rule Engine",
            note="Automatically created from evaluated telemetry",
        ))
        suffix = excursion_id.rsplit("-", 1)[-1]
        self.db.add(Alert(
            alert_id=f"ALT-{start.year}-{suffix}",
            shipment_id=shipment.shipment_id,
            sensor_id=sensor.sensor_id,
            excursion_id=excursion_id,
            severity=severity,
            description=f"[{kind}] {cause}"[:500],
            acknowledgement_status="UNACKNOWLEDGED",
            resolution_status="OPEN",
        ))
        self.db.add(CorrectiveAction(
            action_id=f"ACT-{start.year}-{suffix}",
            excursion_id=excursion_id,
            assigned_user="Quality Engineer",
            action_description=f"Investigate {kind} on {shipment.shipment_id}: {cause}"[:500],
            priority="CRITICAL" if severity == "CRITICAL" else "HIGH",
            status="OPEN",
        ))
        self.db.add(CorrectiveActionStatusEvent(
            action_id=f"ACT-{start.year}-{suffix}",
            from_status=None,
            to_status="OPEN",
            changed_by="Excursion Rule Engine",
            note="Automatically created for a detected excursion",
        ))
        return excursion, True

    def evaluate_shipment_readings(self, shipment_id: str) -> dict:
        shipment = self.db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
        if not shipment:
            return {"error": f"Shipment {shipment_id} not found", "detected_excursions": 0}

        readings = (
            self.db.query(SensorReading)
            .filter(SensorReading.shipment_id == shipment_id)
            .order_by(SensorReading.sensor_id, SensorReading.timestamp)
            .all()
        )
        if not readings:
            return {"shipment_id": shipment_id, "message": "No sensor readings found for shipment", "detected_excursions": 0}

        grouped = {}
        for reading in readings:
            grouped.setdefault(reading.sensor_id, []).append(reading)

        added = 0
        for sensor_id, stream in grouped.items():
            sensor = self.db.query(Sensor).filter(Sensor.sensor_id == sensor_id).first()
            if not sensor:
                continue

            first_time = _naive(stream[0].timestamp)
            calibration_time = _naive(sensor.calibration_date)
            calibration_bad = sensor.calibration_status.lower() in {"expired", "failed"} or (
                calibration_time and (first_time - calibration_time).days > CALIBRATION_VALID_DAYS
            )
            if calibration_bad:
                _, created = self._record(
                    shipment=shipment, sensor=sensor, kind="CALIBRATION_FAILURE",
                    start=first_time, end=_naive(stream[-1].timestamp),
                    duration=max(0.0, (_naive(stream[-1].timestamp) - first_time).total_seconds() / 60),
                    policy=self._policy_for(shipment.product_id, first_time), severity="CRITICAL",
                    cause=f"Sensor calibration is {sensor.calibration_status} or expired",
                )
                added += int(created)

            active = {"TEMPERATURE": None, "HUMIDITY": None}
            previous = None
            for reading in stream:
                ts = _naive(reading.timestamp)
                policy = self._policy_for(shipment.product_id, ts)
                product = shipment.product
                t_low = policy.temp_warning_low if policy else product.temperature_min
                t_high = policy.temp_warning_high if policy else product.temperature_max
                t_crit_low = policy.temp_critical_low if policy else product.temperature_min - 2
                t_crit_high = policy.temp_critical_high if policy else product.temperature_max + 2
                h_low = policy.humidity_min if policy else product.humidity_min
                h_high = policy.humidity_max if policy else product.humidity_max
                permissible = policy.max_excursion_duration_minutes if policy else product.permissible_excursion_duration

                if previous is not None:
                    gap = (ts - _naive(previous.timestamp)).total_seconds() / 60
                    if gap > MAX_EXPECTED_GAP_MINUTES:
                        sensor.sensor_health = "Faulty" if gap >= 30 else "Warning"
                        _, created = self._record(
                            shipment=shipment, sensor=sensor, kind="MISSING_INTERVAL",
                            start=_naive(previous.timestamp), end=ts, duration=gap,
                            policy=policy, severity="CRITICAL" if gap >= 30 else "WARNING",
                            cause=f"No reading was received for {gap:.1f} minutes; interval is unverified",
                        )
                        added += int(created)

                        for dimension, run in active.items():
                            if run:
                                duration = max(0.0, (_naive(previous.timestamp) - run["start"]).total_seconds() / 60 + EXPECTED_INTERVAL_MINUTES)
                                _, created = self._record(
                                    shipment=shipment, sensor=sensor, kind=run["type"], start=run["start"],
                                    end=_naive(previous.timestamp), duration=duration, value=run["peak"],
                                    threshold=run["threshold"], policy=run["policy"],
                                    severity="CRITICAL" if run["critical"] or duration > run["permissible"] else "WARNING",
                                    cause=f"Continuous {dimension.lower()} excursion lasted {duration:.1f} minutes",
                                )
                                added += int(created)
                                active[dimension] = None

                # Impossible physical values are discrete hardware anomalies, not product excursions.
                physical_fault = (
                    reading.temperature is not None and not PHYSICAL_TEMP_MIN <= reading.temperature <= PHYSICAL_TEMP_MAX
                ) or (
                    reading.humidity is not None and not PHYSICAL_HUMIDITY_MIN <= reading.humidity <= PHYSICAL_HUMIDITY_MAX
                )
                if physical_fault:
                    value = reading.temperature if reading.temperature is not None and not PHYSICAL_TEMP_MIN <= reading.temperature <= PHYSICAL_TEMP_MAX else reading.humidity
                    _, created = self._record(
                        shipment=shipment, sensor=sensor, kind="PHYSICAL_RANGE_VIOLATION",
                        start=ts, end=ts, duration=EXPECTED_INTERVAL_MINUTES, value=value,
                        policy=policy, severity="CRITICAL",
                        cause=f"Sensor value {value} is outside physical measurement limits",
                    )
                    added += int(created)

                checks = (
                    ("TEMPERATURE", reading.temperature, t_low, t_high, t_crit_low, t_crit_high, "TEMPERATURE_LOW", "TEMPERATURE_HIGH"),
                    ("HUMIDITY", reading.humidity, h_low, h_high, h_low, h_high, "HUMIDITY_LOW", "HUMIDITY_HIGH"),
                )
                for dimension, value, low, high, critical_low, critical_high, low_type, high_type in checks:
                    if value is None:
                        continue
                    if dimension == "TEMPERATURE" and not PHYSICAL_TEMP_MIN <= value <= PHYSICAL_TEMP_MAX:
                        violation = False
                    elif dimension == "HUMIDITY" and not PHYSICAL_HUMIDITY_MIN <= value <= PHYSICAL_HUMIDITY_MAX:
                        violation = False
                    else:
                        violation = value < low or value > high
                    run = active[dimension]
                    if violation:
                        kind = low_type if value < low else high_type
                        if run and run["type"] != kind:
                            duration = max(0.0, (_naive(previous.timestamp) - run["start"]).total_seconds() / 60 + EXPECTED_INTERVAL_MINUTES)
                            _, created = self._record(
                                shipment=shipment, sensor=sensor, kind=run["type"], start=run["start"], end=_naive(previous.timestamp),
                                duration=duration, value=run["peak"], threshold=run["threshold"], policy=run["policy"],
                                severity="CRITICAL" if run["critical"] or duration > run["permissible"] else "WARNING",
                                cause=f"Continuous {dimension.lower()} excursion lasted {duration:.1f} minutes",
                            )
                            added += int(created)
                            run = None
                        if run is None:
                            run = {"type": kind, "start": ts, "peak": value, "threshold": low if value < low else high,
                                   "critical": value < critical_low or value > critical_high,
                                   "permissible": permissible, "policy": policy}
                            active[dimension] = run
                        else:
                            run["peak"] = min(run["peak"], value) if value < low else max(run["peak"], value)
                            run["critical"] = run["critical"] or value < critical_low or value > critical_high
                    elif run:
                        duration = max(0.0, (ts - run["start"]).total_seconds() / 60)
                        severity = "CRITICAL" if run["critical"] or duration > run["permissible"] else "WARNING"
                        _, created = self._record(
                            shipment=shipment, sensor=sensor, kind=run["type"], start=run["start"], end=ts,
                            duration=duration, value=run["peak"], threshold=run["threshold"], policy=run["policy"],
                            severity=severity,
                            cause=f"Continuous {dimension.lower()} excursion lasted {duration:.1f} minutes",
                        )
                        added += int(created)
                        active[dimension] = None

                previous = reading

            if previous:
                end = _naive(previous.timestamp)
                for dimension, run in active.items():
                    if run:
                        duration = max(0.0, (end - run["start"]).total_seconds() / 60 + EXPECTED_INTERVAL_MINUTES)
                        _, created = self._record(
                            shipment=shipment, sensor=sensor, kind=run["type"], start=run["start"], end=end,
                            duration=duration, value=run["peak"], threshold=run["threshold"], policy=run["policy"],
                            severity="CRITICAL" if run["critical"] or duration > run["permissible"] else "WARNING",
                            cause=f"Ongoing {dimension.lower()} excursion lasted {duration:.1f} minutes",
                        )
                        added += int(created)

        # Route delays are operational exceptions and retain sensor context.
        delays = self.db.query(RouteStop).filter(
            RouteStop.shipment_id == shipment_id,
            RouteStop.actual_arrival.isnot(None),
            RouteStop.actual_arrival > RouteStop.planned_arrival,
        ).all()
        for stop in delays:
            delay_minutes = (_naive(stop.actual_arrival) - _naive(stop.planned_arrival)).total_seconds() / 60
            if delay_minutes < 30:
                continue
            assignment = self.db.query(ContainerShipmentAssignment).filter(
                ContainerShipmentAssignment.shipment_id == shipment_id,
                ContainerShipmentAssignment.assigned_at <= stop.planned_arrival,
                (ContainerShipmentAssignment.released_at.is_(None) | (ContainerShipmentAssignment.released_at >= stop.actual_arrival)),
            ).first()
            sensor = self.db.query(Sensor).filter(Sensor.assigned_container_id == assignment.container_id).first() if assignment else None
            if not sensor:
                continue
            _, created = self._record(
                shipment=shipment,
                sensor=sensor,
                kind="ROUTE_DELAY",
                start=_naive(stop.planned_arrival),
                end=_naive(stop.actual_arrival),
                duration=delay_minutes,
                policy=self._policy_for(shipment.product_id, _naive(stop.actual_arrival)),
                severity="CRITICAL" if delay_minutes >= 120 else "WARNING",
                cause=f"{stop.location_name} arrived {delay_minutes:.1f} minutes after planned arrival",
            )
            added += int(created)

        self.db.commit()
        return {
            "shipment_id": shipment_id,
            "detected_excursions": self.db.query(Excursion).filter(Excursion.shipment_id == shipment_id).count(),
            "created_excursions": added,
            "created_alerts": added,
            "created_actions": added,
        }
