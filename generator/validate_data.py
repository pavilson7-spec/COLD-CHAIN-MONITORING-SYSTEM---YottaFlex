import sys
import os
from datetime import datetime, timezone

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.core.database import SessionLocal
from app.validators.data_validator import DataValidator
from generator.ground_truth import GroundTruthTracker

def run_validation():
    print("[Data Validation] Executing automated validation on generated database entities...")
    db = SessionLocal()
    try:
        validator = DataValidator(db)
        results = validator.validate_all()
        print("\n================== VALIDATION REPORT ==================")
        print(f"Timestamp: {results['timestamp']}")
        print(f"Overall Success Rate: {results['success_rate']}%")
        print(f"Passed: {results['passed_tests']} / {results['total_tests']}")
        print("-------------------------------------------------------")
        for d in results["details"]:
            print(f"- Scenario: {d['scenario']}")
            print(f"  Issue Type: {d.get('issue_type')}")
            print(f"  Status: {d['status']}")
            print(f"  Expected: {d['expected_behavior']}")
            if 'violations_found' in d:
                print(f"  Violations Flagged: {d['violations_found']}")
            print("-------------------------------------------------------")
        print("=======================================================\n")
        return results
    finally:
        db.close()

if __name__ == "__main__":
    run_validation()
