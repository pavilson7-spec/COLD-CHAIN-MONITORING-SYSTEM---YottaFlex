import os
import sys
import hashlib

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))
from generator.generate_data import generate_cold_chain_data

def compute_checksum(filepath):
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def test_reproducibility():
    print("[Reproducibility Verification] Generating datasets with identical seed (20261022)...")
    res1 = generate_cold_chain_data(num_shipments=50, num_containers=15, seed=20261022, persist_db=False)
    gt1_path = os.path.join("data", "generated", "ground_truth.csv")
    manifest_path = os.path.join("data", "generated", "generation_manifest.json")
    cs1 = compute_checksum(gt1_path)
    manifest1 = compute_checksum(manifest_path)

    res2 = generate_cold_chain_data(num_shipments=50, num_containers=15, seed=20261022, persist_db=False)
    cs2 = compute_checksum(gt1_path)
    manifest2 = compute_checksum(manifest_path)

    print(f"Run 1 Checksum: {cs1}")
    print(f"Run 2 Checksum: {cs2}")

    assert cs1 == cs2, "Non-deterministic generation detected!"
    assert manifest1 == manifest2, "Non-deterministic generation manifest detected!"
    assert res1["shipments_count"] == res2["shipments_count"]
    assert res1["readings_count"] == res2["readings_count"]
    print("SUCCESS: Dataset generation is 100% reproducible with bit-for-bit checksum equivalence.")

if __name__ == "__main__":
    test_reproducibility()
