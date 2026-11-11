import os
import json
import csv
from typing import List, Dict, Any

GROUND_TRUTH_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "generated")

class GroundTruthTracker:
    """
    Dedicated tracker for mandatory negative scenario test cases and ground truth verification.
    NEVER leaked into production feature inputs or runtime detection logic.
    Maintained independently in data/generated/ground_truth.csv and ground_truth.json.
    """
    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def record_scenario(
        self,
        case_id: str,
        shipment_id: str,
        sensor_id: str,
        scenario_name: str,
        issue_type: str,
        ground_truth_label: str,
        injected_value: Any,
        expected_behavior: str,
        original_source: Any = None,
    ):
        record = {
            "case_id": case_id,
            "shipment_id": shipment_id,
            "sensor_id": sensor_id,
            "scenario_name": scenario_name,
            "issue_type": issue_type,
            "ground_truth_label": ground_truth_label, # ANOMALOUS, EXCURSION, CORRUPT, INVALID_TIMING
            "injected_value": str(injected_value),
            "original_source": str(original_source) if original_source is not None else "",
            "expected_behavior": expected_behavior,
            "validation_result": "UNVERIFIED"
        }
        self.records.append(record)

    def save_ground_truth(self):
        os.makedirs(GROUND_TRUTH_DIR, exist_ok=True)
        csv_path = os.path.join(GROUND_TRUTH_DIR, "ground_truth.csv")
        json_path = os.path.join(GROUND_TRUTH_DIR, "ground_truth.json")

        # Save CSV
        if self.records:
            fieldnames = list(self.records[0].keys())
            with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in self.records:
                    writer.writerow(r)

        # Save JSON
        with open(json_path, mode="w", encoding="utf-8") as f:
            json.dump(self.records, f, indent=2)

        print(f"[GroundTruthTracker] Saved {len(self.records)} ground truth records to {csv_path} and {json_path}")
