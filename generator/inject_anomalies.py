import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from generator.ground_truth import GroundTruthTracker

def inject_mandatory_negative_scenarios(
    shipments: List[Dict[str, Any]],
    readings: List[Dict[str, Any]],
    sensors: List[Dict[str, Any]],
    gt_tracker: GroundTruthTracker,
    route_stops: List[Dict[str, Any]] = None,
):
    """
    Inject the required labelled negative scenarios:
    1. Reading outside physical range (e.g. -150C or +120C).
    2. Missing interval incorrectly interpreted as safe (create 60-minute gaps without readings).
    3. Shipment delivered before departure (chronological impossibility).
    4. Wrong product threshold applied (corrupt threshold association).
    5. Excursion duration undercounted (split or truncated calculation bounds).
    """
    print("[Anomaly Injector] Injecting labelled negative scenarios and guarded-input cases...")

    # 1. Reading outside physical range
    # Select reading at index 100
    if len(readings) > 100:
        target_rdg = readings[100]
        original_temperature = target_rdg["temperature"]
        target_rdg["temperature"] = 125.4 # Physically impossible temperature
        target_rdg["is_anomaly"] = True
        target_rdg["issue_type"] = "PHYSICAL_OUT_OF_BOUNDS"
        target_rdg["ground_truth_label"] = "CRITICAL_HARDWARE_ANOMALY"
        target_rdg["source_reading_id"] = target_rdg["reading_id"]
        gt_tracker.record_scenario(
            case_id="SCENARIO-01-PHYSICAL-RANGE",
            shipment_id=target_rdg["shipment_id"],
            sensor_id=target_rdg["sensor_id"],
            scenario_name="Reading outside physical range",
            issue_type="PHYSICAL_OUT_OF_BOUNDS",
            ground_truth_label="CRITICAL_HARDWARE_ANOMALY",
            injected_value=125.4,
            expected_behavior="Engine must flag reading as exceeding physical bounds [-80, 70] C and create alert",
            original_source=f"temperature={original_temperature}",
        )

    # 2. Missing interval incorrectly interpreted as safe
    # Remove readings over a 1-hour span for shipment 5
    if len(shipments) > 5:
        target_shp = shipments[5]["shipment_id"]
        shp_readings = [r for r in readings if r["shipment_id"] == target_shp and r["sensor_id"].endswith("-TEMP")]
        if len(shp_readings) > 20:
            # Drop 10 consecutive readings creating a 50-minute blackout
            positions = {id(reading): index for index, reading in enumerate(readings)}
            drop_indices = [positions[id(r)] for r in shp_readings[10:20]]
            # Mark the time gap
            gap_start = shp_readings[9]["timestamp"]
            gap_end = shp_readings[20]["timestamp"]
            for idx in sorted(drop_indices, reverse=True):
                readings.pop(idx)
            gt_tracker.record_scenario(
                case_id="SCENARIO-02-MISSING-INTERVAL",
                shipment_id=target_shp,
                sensor_id=shp_readings[9]["sensor_id"],
                scenario_name="Missing interval safe assumption prevention",
                issue_type="TELEMETRY_DROPOUT_GAP",
                ground_truth_label="MISSING_DATA_EXCURSION",
                injected_value=f"Gap from {gap_start} to {gap_end}",
                expected_behavior="Engine must NOT treat missing period as safe; must flag critical telemetry gap"
            )

    # 3. Shipment delivered before departure
    if len(shipments) > 2:
        target_shp = shipments[2]
        # Invert actual delivery time to 5 hours prior to departure
        target_shp["source_actual_delivery_time"] = target_shp["actual_delivery_time"]
        target_shp["actual_delivery_time"] = target_shp["departure_time"] - timedelta(hours=5)
        target_shp["issue_type"] = "CHRONOLOGICAL_INVERSION"
        target_shp["ground_truth_label"] = "LIFECYCLE_TEMPORAL_CORRUPTION"
        final_stop = next((stop for stop in (route_stops or []) if stop["shipment_id"] == target_shp["shipment_id"] and stop["stop_sequence"] == 3), None)
        if final_stop:
            final_stop["actual_arrival"] = target_shp["actual_delivery_time"]
            final_stop["issue_type"] = "CHRONOLOGICAL_INVERSION"
            final_stop["ground_truth_label"] = "LIFECYCLE_TEMPORAL_CORRUPTION"
        gt_tracker.record_scenario(
            case_id="SCENARIO-03-DELIVERED-BEFORE-DEPARTURE",
            shipment_id=target_shp["shipment_id"],
            sensor_id="N/A",
            scenario_name="Shipment delivered before departure",
            issue_type="CHRONOLOGICAL_INVERSION",
            ground_truth_label="LIFECYCLE_TEMPORAL_CORRUPTION",
            injected_value=str(target_shp["actual_delivery_time"]),
            expected_behavior="Validator must flag error: actual delivery timestamp cannot precede departure",
            original_source=target_shp["source_actual_delivery_time"],
        )

    # 4. Wrong product threshold applied
    # Calibrate sensor to 'Failed' or assign wrong threshold
    if len(sensors) > 3:
        target_sns = sensors[3]
        target_sns["source_calibration_status"] = target_sns["calibration_status"]
        target_sns["calibration_status"] = "Failed"
        target_sns["sensor_health"] = "Faulty"
        target_sns["issue_type"] = "CALIBRATION_FAILURE"
        target_sns["ground_truth_label"] = "UNVERIFIED_SENSOR_DATA"
        target_rdg = next((r for r in readings if r["sensor_id"] == target_sns["sensor_id"]), None)
        gt_tracker.record_scenario(
            case_id="SCENARIO-04-CALIBRATION-POLICY-FAILURE",
            shipment_id=target_rdg["shipment_id"] if target_rdg else "N/A",
            sensor_id=target_sns["sensor_id"],
            scenario_name="Calibration failure / invalid policy enforcement",
            issue_type="UNCALIBRATED_TELEMETRY",
            ground_truth_label="UNVERIFIED_DATA",
            injected_value="Calibration Status: Failed",
            expected_behavior="Engine must validate sensor calibration and flag uncalibrated excursions",
            original_source="Calibration Status: Valid",
        )

    # 5. Excursion duration undercounted
    # Inject continuous sustained high temperature for 10 consecutive readings (50 mins)
    if len(shipments) > 1:
        target_shp = shipments[1]["shipment_id"]
        shp_readings = [r for r in readings if r["shipment_id"] == target_shp and r["sensor_id"].endswith("-TEMP")]
        if len(shp_readings) > 15:
            original_values = [r["temperature"] for r in shp_readings[5:15]]
            for r in shp_readings[5:15]:
                r["temperature"] = 28.5 # High excursion for chilled goods (typically 2-8 C)
                r["is_anomaly"] = True
                r["issue_type"] = "CONTINUOUS_HIGH_TEMP"
                r["ground_truth_label"] = "HIGH_TEMPERATURE_EXCURSION"
                r["source_reading_id"] = r["reading_id"]
            gt_tracker.record_scenario(
                case_id="SCENARIO-05-EXCURSION-DURATION-CONTINUITY",
                shipment_id=target_shp,
                sensor_id=shp_readings[5]["sensor_id"],
                scenario_name="Continuous excursion duration tracking",
                issue_type="CONTINUOUS_HIGH_TEMP",
                ground_truth_label="HIGH_TEMPERATURE_EXCURSION",
                injected_value="28.5 C across 50 mins",
                expected_behavior="Engine must record continuous duration of at least 45-50 minutes, exceeding product-specific limit",
                original_source=f"temperatures={original_values}",
            )

    # The remaining cases describe rejected inputs and guarded decisions. They are
    # kept in ground truth instead of inserting invalid foreign keys or duplicates.
    if shipments:
        shipment = shipments[min(3, len(shipments) - 1)]
        gt_tracker.record_scenario(
            case_id="SCENARIO-06-WRONG-PRODUCT-THRESHOLD",
            shipment_id=shipment["shipment_id"], sensor_id="N/A",
            scenario_name="Wrong product threshold application",
            issue_type="POLICY_PRODUCT_MISMATCH", ground_truth_label="MISMATCH_MUST_BE_REJECTED",
            injected_value="Attempt to evaluate using another product's policy",
            expected_behavior="Use only the effective threshold policy linked to this shipment's product",
        )

    if readings:
        sample = readings[0]
        gt_tracker.record_scenario(
            case_id="SCENARIO-07-DUPLICATE-READING",
            shipment_id=sample["shipment_id"], sensor_id=sample["sensor_id"],
            scenario_name="Duplicate sensor reading",
            issue_type="DUPLICATE_SENSOR_TIMESTAMP", ground_truth_label="DUPLICATE_MUST_BE_REJECTED",
            injected_value=f"{sample['sensor_id']} at {sample['timestamp']}",
            expected_behavior="Reject duplicate readings for the same sensor timestamp",
            original_source=sample["reading_id"],
        )

    delayed_stop = next((stop for stop in (route_stops or []) if stop.get("status") == "Delayed"), None)
    if delayed_stop:
        gt_tracker.record_scenario(
            case_id="SCENARIO-08-ROUTE-STOP-DELAY",
            shipment_id=delayed_stop["shipment_id"], sensor_id="N/A",
            scenario_name="Shipment delayed at route stop",
            issue_type="ROUTE_STOP_DELAY", ground_truth_label="DELAY_REQUIRES_NOTIFICATION",
            injected_value=f"{delayed_stop['location_name']} arrival {delayed_stop['actual_arrival']}",
            expected_behavior="Flag route stop delays against planned arrival and retain actual arrival time",
        )

    if shipments:
        shipment = shipments[0]
        gt_tracker.record_scenario(
            case_id="SCENARIO-09-INVALID-ASSIGNMENT",
            shipment_id=shipment["shipment_id"], sensor_id="N/A",
            scenario_name="Invalid container or sensor assignment",
            issue_type="INVALID_CONTAINER_SENSOR_ASSIGNMENT", ground_truth_label="ASSIGNMENT_MUST_BE_REJECTED",
            injected_value="Unknown container reference",
            expected_behavior="Reject sensor readings unless sensor, container, and shipment assignments are valid",
        )
        gt_tracker.record_scenario(
            case_id="SCENARIO-10-INVALID-LIFECYCLE-TRANSITION",
            shipment_id=shipment["shipment_id"], sensor_id="N/A",
            scenario_name="Invalid lifecycle state transition",
            issue_type="INVALID_STATE_TRANSITION", ground_truth_label="TRANSITION_MUST_BE_REJECTED",
            injected_value="Created -> Delivered without departure",
            expected_behavior="Enforce legal shipment and excursion lifecycle transitions",
        )
        gt_tracker.record_scenario(
            case_id="SCENARIO-11-MISSING-FOREIGN-KEY",
            shipment_id=shipment["shipment_id"], sensor_id="N/A",
            scenario_name="Missing foreign-key reference",
            issue_type="MISSING_FOREIGN_KEY", ground_truth_label="REFERENCE_MUST_BE_REJECTED",
            injected_value="Reading references unknown sensor",
            expected_behavior="Reject records with missing parent rows and return a client error",
        )

    print("[Anomaly Injector] Scenario ground truth recorded.")
