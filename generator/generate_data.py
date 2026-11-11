import os
import sys
import json
import random
import argparse
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np

# Ensure backend modules can be imported
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.core.database import SessionLocal, engine, Base
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
from app.models.container_assignment import ContainerShipmentAssignment

from generator.ground_truth import GroundTruthTracker
from generator.inject_anomalies import inject_mandatory_negative_scenarios

DATA_GENERATED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "generated")

# Product Catalog
PRODUCTS_DATA = [
    {
        "product_id": "PRD-VAX-001",
        "product_name": "mRNA Vaccine Vax-Ultra",
        "product_category": "Vaccines & Biologics",
        "temperature_min": -75.0,
        "temperature_max": -60.0,
        "humidity_min": 20.0,
        "humidity_max": 60.0,
        "permissible_excursion_duration": 15
    },
    {
        "product_id": "PRD-INS-002",
        "product_name": "Recombinant Human Insulin",
        "product_category": "Endocrinology",
        "temperature_min": 2.0,
        "temperature_max": 8.0,
        "humidity_min": 30.0,
        "humidity_max": 70.0,
        "permissible_excursion_duration": 30
    },
    {
        "product_id": "PRD-BLD-003",
        "product_name": "Packed Red Blood Cells (PRBC)",
        "product_category": "Blood Products",
        "temperature_min": 1.0,
        "temperature_max": 6.0,
        "humidity_min": 40.0,
        "humidity_max": 80.0,
        "permissible_excursion_duration": 20
    },
    {
        "product_id": "PRD-ONC-004",
        "product_name": "Monoclonal Antibody OncoShield",
        "product_category": "Oncology",
        "temperature_min": 2.0,
        "temperature_max": 8.0,
        "humidity_min": 35.0,
        "humidity_max": 65.0,
        "permissible_excursion_duration": 45
    },
    {
        "product_id": "PRD-ORG-005",
        "product_name": "Biological Tissue Graft",
        "product_category": "Transplantation",
        "temperature_min": -40.0,
        "temperature_max": -20.0,
        "humidity_min": 10.0,
        "humidity_max": 50.0,
        "permissible_excursion_duration": 15
    }
]

CITIES = [
    "Boston, MA", "Philadelphia, PA", "Basel, Switzerland", "Dublin, Ireland",
    "Frankfurt, Germany", "Singapore", "Chicago, IL", "San Francisco, CA",
    "Tokyo, Japan", "Brussels, Belgium", "Raleigh, NC", "Amsterdam, Netherlands"
]

CONTAINER_TYPES = [
    "Active Cryogenic VIP",
    "Insulated Dry-Ice Shipper",
    "Refrigerated Reefer Container",
    "Phase Change Material Box"
]

def generate_cold_chain_data(
    num_shipments: int = 1000,
    num_containers: int = 300,
    seed: int = 20261022,
    readings_per_shipment: int = None,
    persist_db: bool = True
):
    if num_shipments <= 0 or num_containers <= 0:
        raise ValueError("num_shipments and num_containers must both be positive")
    if readings_per_shipment is not None and readings_per_shipment <= 0:
        raise ValueError("readings_per_shipment must be positive when specified")
    print(f"\n=======================================================")
    print(f"Cold Chain Synthetic Data Generator")
    print(f"Seed: {seed} | Shipments: {num_shipments} | Containers: {num_containers}")
    print(f"=======================================================\n")

    random.seed(seed)
    np.random.seed(seed)
    os.makedirs(DATA_GENERATED_DIR, exist_ok=True)
    gt_tracker = GroundTruthTracker()

    # 1. Generate Products
    products = []
    threshold_policies = []
    for p in PRODUCTS_DATA:
        products.append(Product(
            product_id=p["product_id"],
            product_name=p["product_name"],
            product_category=p["product_category"],
            temperature_min=p["temperature_min"],
            temperature_max=p["temperature_max"],
            humidity_min=p["humidity_min"],
            humidity_max=p["humidity_max"],
            permissible_excursion_duration=p["permissible_excursion_duration"],
            product_status="Active"
        ))
        threshold_policies.append(ThresholdPolicy(
            policy_id=f"POL-{p['product_id']}",
            product_id=p["product_id"],
            policy_name=f"Standard Threshold for {p['product_name']}",
            temp_critical_low=p["temperature_min"] - 2.0,
            temp_warning_low=p["temperature_min"],
            temp_warning_high=p["temperature_max"],
            temp_critical_high=p["temperature_max"] + 2.0,
            humidity_min=p["humidity_min"],
            humidity_max=p["humidity_max"],
            max_excursion_duration_minutes=p["permissible_excursion_duration"],
            is_active=True,
            effective_start=datetime(2020, 1, 1),
            effective_end=None,
            policy_status="Active"
        ))

    # 2. Generate Containers
    containers = []
    for i in range(1, num_containers + 1):
        c_id = f"CNT-{i:06d}"
        containers.append({
            "container_id": c_id,
            "assigned_shipment_id": None,
            "container_type": random.choice(CONTAINER_TYPES),
            "capacity": round(random.uniform(50.0, 500.0), 1),
            "status": "Available"
        })

    # 3. Generate Sensors
    sensors = []
    for i, c in enumerate(containers):
        s_temp_id = f"SNS-{c['container_id']}-TEMP"
        sensors.append({
            "sensor_id": s_temp_id,
            "sensor_type": "TEMPERATURE",
            "assigned_container_id": c["container_id"],
            "calibration_status": "Valid",
            "calibration_date": datetime(2026, 1, 15) + timedelta(days=random.randint(0, 180)),
            "sensor_health": "Healthy",
            "issue_type": None,
            "ground_truth_label": None,
            "source_calibration_status": None
        })
        s_hum_id = f"SNS-{c['container_id']}-HUM"
        sensors.append({
            "sensor_id": s_hum_id,
            "sensor_type": "HUMIDITY",
            "assigned_container_id": c["container_id"],
            "calibration_status": "Valid",
            "calibration_date": datetime(2026, 1, 15) + timedelta(days=random.randint(0, 180)),
            "sensor_health": "Healthy",
            "issue_type": None,
            "ground_truth_label": None,
            "source_calibration_status": None
        })

    # 4. Generate Shipments & Route Stops & Custody Events
    shipments = []
    route_stops = []
    custody_events = []
    base_date = datetime(2026, 6, 1, 8, 0, 0)

    for i in range(1, num_shipments + 1):
        shp_id = f"SHP-2026-{i:06d}"
        prd = random.choice(PRODUCTS_DATA)
        origin = random.choice(CITIES)
        dest = random.choice([c for c in CITIES if c != origin])
        container_index = (i - 1) % max(num_containers, 1)
        container_cycle = (i - 1) // max(num_containers, 1)
        # Reuse a physical container only after the longest configured transit window.
        dep_time = base_date + timedelta(days=container_cycle * 6, hours=container_index * 0.02, minutes=random.randint(0, 59))
        duration_days = random.randint(2, 5)
        delivery_time = dep_time + timedelta(days=duration_days, hours=random.randint(1, 10))

        # 80% Delivered, 15% In_Transit, 5% Created
        rand_stat = random.random()
        if rand_stat < 0.80:
            status = "Delivered"
            actual_delivery = delivery_time + timedelta(minutes=random.randint(0, 120))
        elif rand_stat < 0.95:
            status = "In_Transit"
            actual_delivery = None
        else:
            status = "Created"
            actual_delivery = None

        shipments.append({
            "shipment_id": shp_id,
            "container_id": f"CNT-{container_index + 1:06d}",
            "product_id": prd["product_id"],
            "origin": origin,
            "destination": dest,
            "departure_time": dep_time,
            "expected_delivery_time": delivery_time,
            "actual_delivery_time": actual_delivery,
            "shipment_status": status,
            "target_temp_min": prd["temperature_min"],
            "target_temp_max": prd["temperature_max"],
            "target_hum_min": prd["humidity_min"],
            "target_hum_max": prd["humidity_max"]
        })

        # Route stops (Origin, Midpoint, Destination)
        mid_delay = timedelta(minutes=random.randint(45, 180)) if status in ["Delivered", "In_Transit"] and random.random() < 0.08 else timedelta(0)
        route_stops.append({
            "stop_id": f"STP-{shp_id}-01",
            "shipment_id": shp_id,
            "stop_sequence": 1,
            "location_name": f"{origin} Logistics Hub",
            "latitude": "42.3601",
            "longitude": "-71.0589",
            "planned_arrival": dep_time,
            "actual_arrival": dep_time,
            "departure_time": dep_time + timedelta(hours=1),
            "status": "Departed"
        })
        mid_time = dep_time + timedelta(days=duration_days / 2)
        route_stops.append({
            "stop_id": f"STP-{shp_id}-02",
            "shipment_id": shp_id,
            "stop_sequence": 2,
            "location_name": f"Mid-Transit Cold Hub",
            "latitude": "40.7128",
            "longitude": "-74.0060",
            "planned_arrival": mid_time,
            "actual_arrival": mid_time + mid_delay if status in ["Delivered", "In_Transit"] else None,
            "departure_time": mid_time + mid_delay + timedelta(hours=2) if status in ["Delivered", "In_Transit"] else None,
            "status": "Delayed" if mid_delay else ("Departed" if status == "Delivered" else "Arrived"),
            "issue_type": "ROUTE_STOP_DELAY" if mid_delay else None,
            "ground_truth_label": "DELAY_REQUIRES_NOTIFICATION" if mid_delay else None
        })
        route_stops.append({
            "stop_id": f"STP-{shp_id}-03",
            "shipment_id": shp_id,
            "stop_sequence": 3,
            "location_name": f"{dest} Receiving Dock",
            "latitude": "50.1109",
            "longitude": "8.6821",
            "planned_arrival": delivery_time,
            "actual_arrival": actual_delivery,
            "departure_time": None,
            "status": "Arrived" if status == "Delivered" else "Pending",
            "issue_type": "ROUTE_STOP_DELAY" if actual_delivery and actual_delivery > delivery_time + timedelta(minutes=30) else None,
            "ground_truth_label": "DELAY_REQUIRES_NOTIFICATION" if actual_delivery and actual_delivery > delivery_time + timedelta(minutes=30) else None
        })

        # Custody events
        custody_events.append({
            "event_id": f"CST-{shp_id}-01",
            "shipment_id": shp_id,
            "event_timestamp": dep_time,
            "event_type": "DEPARTURE",
            "from_party": "Pharma Manufacturing Plant",
            "to_party": "Cold Line Express Logistics",
            "location": origin,
            "condition_status": "Normal",
            "notes": "Container sealed and calibrated."
        })
        if status == "Delivered":
            custody_events.append({
                "event_id": f"CST-{shp_id}-02",
                "shipment_id": shp_id,
                "event_timestamp": actual_delivery,
                "event_type": "ARRIVAL",
                "from_party": "Cold Line Express Logistics",
                "to_party": "Hospital Receiving Pharmacy",
                "location": dest,
                "condition_status": "Normal",
                "notes": "Delivered into verified refrigerated storage."
            })

    # Assign containers to active/delivered shipments
    for idx, s in enumerate(shipments):
        c_idx = idx % len(containers)
        containers[c_idx]["assigned_shipment_id"] = s["shipment_id"]
        if s["shipment_status"] == "In_Transit":
            containers[c_idx]["status"] = "In_Transit"
        elif s["shipment_status"] == "Delivered":
            containers[c_idx]["status"] = "Available"

    container_assignments = [
        ContainerShipmentAssignment(
            container_id=s["container_id"],
            shipment_id=s["shipment_id"],
            assigned_at=s["departure_time"],
            released_at=s["actual_delivery_time"] or s["expected_delivery_time"],
            assignment_status="Released" if s["shipment_status"] == "Delivered" else "Assigned",
        ) for s in shipments
    ]

    # 5. Generate Sensor Readings at 5-minute intervals
    print("[Synthetic Generator] Generating sensor readings...")
    readings = []
    # For every shipment, generate readings
    for idx, s in enumerate(shipments):
        assigned_cnt = containers[idx % len(containers)]
        s_temp = f"SNS-{assigned_cnt['container_id']}-TEMP"
        s_hum = f"SNS-{assigned_cnt['container_id']}-HUM"

        t_min = s["target_temp_min"]
        t_max = s["target_temp_max"]
        h_min = s["target_hum_min"]
        h_max = s["target_hum_max"]

        t_mean = (t_min + t_max) / 2.0
        h_mean = (h_min + h_max) / 2.0

        current_ts = s["departure_time"]
        trip_end = s["actual_delivery_time"] or s["expected_delivery_time"]
        sample_count = readings_per_shipment if readings_per_shipment is not None else max(1, int((trip_end - current_ts).total_seconds() // 300) + 1)
        for step in range(sample_count):
            reading_time = current_ts + timedelta(minutes=step * 5)
            # Simulated normal distribution within acceptable thresholds
            temp_val = round(np.random.normal(t_mean, (t_max - t_min) * 0.1), 2)
            hum_val = round(np.random.normal(h_mean, 3.0), 1)
            batt = round(max(20.0, 100.0 - (step * 0.1)), 1)
            
            ts_str = reading_time.strftime("%Y%m%d%H%M%S")
            readings.append({
                "reading_id": f"RDG-{s_temp}-{ts_str}",
                "sensor_id": s_temp,
                "shipment_id": s["shipment_id"],
                "timestamp": reading_time,
                "temperature": float(temp_val),
                "humidity": float(hum_val),
                "battery_level": float(batt),
                "is_anomaly": False
            })
            readings.append({
                "reading_id": f"RDG-{s_hum}-{ts_str}",
                "sensor_id": s_hum,
                "shipment_id": s["shipment_id"],
                "timestamp": reading_time,
                "temperature": None,
                "humidity": float(hum_val),
                "battery_level": float(batt),
                "is_anomaly": False
            })

    print(f"[Synthetic Generator] Generated baseline: {len(shipments)} shipments, {len(readings)} readings.")

    # 6. Inject Mandatory Negative Scenarios
    inject_mandatory_negative_scenarios(shipments, readings, sensors, gt_tracker, route_stops)
    gt_tracker.save_ground_truth()

    # 7. Persist to Database if requested
    if persist_db:
        print("[Database Seeder] Persisting generated dataset to PostgreSQL...")
        db = SessionLocal()
        try:
            # Upsert Products
            for p in products:
                if not db.query(Product).filter(Product.product_id == p.product_id).first():
                    db.add(p)
            for pol in threshold_policies:
                if not db.query(ThresholdPolicy).filter(ThresholdPolicy.policy_id == pol.policy_id).first():
                    db.add(pol)
            db.commit()

            # Insert Shipments FIRST before containers reference them
            for s in shipments:
                if not db.query(Shipment).filter(Shipment.shipment_id == s["shipment_id"]).first():
                    db.add(Shipment(
                        shipment_id=s["shipment_id"],
                        product_id=s["product_id"],
                        origin=s["origin"],
                        destination=s["destination"],
                        departure_time=s["departure_time"],
                        expected_delivery_time=s["expected_delivery_time"],
                        actual_delivery_time=s["actual_delivery_time"],
                        shipment_status=s["shipment_status"],
                        issue_type=s.get("issue_type"),
                        ground_truth_label=s.get("ground_truth_label"),
                        source_actual_delivery_time=s.get("source_actual_delivery_time")
                    ))
            db.commit()

            # Insert Containers
            for c in containers:
                if not db.query(Container).filter(Container.container_id == c["container_id"]).first():
                    db.add(Container(
                        container_id=c["container_id"],
                        assigned_shipment_id=c["assigned_shipment_id"],
                        container_type=c["container_type"],
                        capacity=c["capacity"],
                        status=c["status"]
                    ))
            db.commit()

            for assignment in container_assignments:
                exists = db.query(ContainerShipmentAssignment).filter_by(
                    container_id=assignment.container_id,
                    shipment_id=assignment.shipment_id,
                ).first()
                if not exists:
                    db.add(assignment)
            db.commit()

            # Insert Sensors
            for s in sensors:
                if not db.query(Sensor).filter(Sensor.sensor_id == s["sensor_id"]).first():
                    db.add(Sensor(
                        sensor_id=s["sensor_id"],
                        sensor_type=s["sensor_type"],
                        assigned_container_id=s["assigned_container_id"],
                        calibration_status=s["calibration_status"],
                        calibration_date=s["calibration_date"],
                        sensor_health=s["sensor_health"],
                        issue_type=s.get("issue_type"),
                        ground_truth_label=s.get("ground_truth_label"),
                        source_calibration_status=s.get("source_calibration_status")
                    ))
            db.commit()

            # Insert Route Stops
            for stp in route_stops:
                if not db.query(RouteStop).filter(RouteStop.stop_id == stp["stop_id"]).first():
                    db.add(RouteStop(**stp))
            db.commit()

            # Insert Custody Events
            for cst in custody_events:
                if not db.query(CustodyEvent).filter(CustodyEvent.event_id == cst["event_id"]).first():
                    db.add(CustodyEvent(**cst))
            db.commit()

            # Insert Readings in Batches
            print(f"[Database Seeder] Inserting {len(readings)} sensor readings...")
            batch_size = 5000
            for b in range(0, len(readings), batch_size):
                chunk = readings[b:b+batch_size]
                chunk_ids = [r["reading_id"] for r in chunk]
                existing_ids = {
                    row[0] for row in db.query(SensorReading.reading_id).filter(SensorReading.reading_id.in_(chunk_ids)).all()
                }
                reading_objs = [
                    SensorReading(
                        reading_id=r["reading_id"],
                        sensor_id=r["sensor_id"],
                        shipment_id=r["shipment_id"],
                        timestamp=r["timestamp"],
                        temperature=r["temperature"],
                        humidity=r["humidity"],
                        battery_level=r["battery_level"],
                        is_anomaly=r["is_anomaly"],
                        issue_type=r.get("issue_type"),
                        ground_truth_label=r.get("ground_truth_label"),
                        source_reading_id=r.get("source_reading_id")
                    ) for r in chunk if r["reading_id"] not in existing_ids
                ]
                if reading_objs:
                    db.bulk_save_objects(reading_objs)
                    db.commit()
            print("[Database Seeder] Database seeded successfully!")

            # Evaluate excursions on first 20 shipments to seed excursions, alerts and actions
            from app.services.excursion_engine import ExcursionRuleEngine
            engine_inst = ExcursionRuleEngine(db)
            print("[Excursion Engine] Running initial excursion evaluations on baseline shipments...")
            for s in shipments[:20]:
                engine_inst.evaluate_shipment_readings(s["shipment_id"])
            print("[Excursion Engine] Excursions, alerts and corrective actions generated.")

        finally:
            db.close()

    # Save summary stats to data/generated
    summary = {
        "shipments_count": len(shipments),
        "containers_count": len(containers),
        "sensors_count": len(sensors),
        "readings_count": len(readings),
        "seed": seed,
        "readings_per_shipment": readings_per_shipment,
        "sampling_interval_minutes": 5,
    }
    with open(os.path.join(DATA_GENERATED_DIR, "generation_manifest.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[Generation Complete] Summary manifest saved to {os.path.join(DATA_GENERATED_DIR, 'generation_manifest.json')}")
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthetic Cold Chain Data Generator")
    parser.add_argument("--shipments", type=int, default=1000, help="Number of shipments (default: 1000)")
    parser.add_argument("--containers", type=int, default=300, help="Number of containers (default: 300)")
    parser.add_argument("--seed", type=int, default=20261022, help="Random seed (default: 20261022)")
    parser.add_argument("--readings-per-shipment", type=int, default=None, help="Override full trip sampling with a fixed sample count (default: every 5 minutes through delivery)")
    parser.add_argument("--no-db", action="store_true", help="Do not persist to PostgreSQL database")
    args = parser.parse_args()

    generate_cold_chain_data(
        num_shipments=args.shipments,
        num_containers=args.containers,
        seed=args.seed,
        readings_per_shipment=args.readings_per_shipment,
        persist_db=not args.no_db
    )
