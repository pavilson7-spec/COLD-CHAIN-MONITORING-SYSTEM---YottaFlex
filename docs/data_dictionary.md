# Cold Chain Monitoring System - Data Dictionary

This document defines all entities, primary keys, foreign keys, constraints, and validation rules in the PostgreSQL database (`cold_chain_monitoring_db`).

---

## 1. Product (`products`)
Stores pharmaceutical and biologic items with regulatory temperature and humidity storage specifications.

| Column | Type | Nullable | Constraints / Description |
|---|---|---|---|
| `product_id` | VARCHAR(50) | NO | Primary Key. e.g. `PRD-VAX-001` |
| `product_name` | VARCHAR(150) | NO | Unique product name |
| `product_category` | VARCHAR(100) | NO | e.g. Vaccines & Biologics, Endocrinology |
| `temperature_min` | FLOAT | NO | Minimum allowed storage temp (°C) |
| `temperature_max` | FLOAT | NO | Maximum allowed storage temp (°C) |
| `humidity_min` | FLOAT | NO | Minimum allowed relative humidity (% RH) |
| `humidity_max` | FLOAT | NO | Maximum allowed relative humidity (% RH) |
| `permissible_excursion_duration` | INT | NO | Permissible excursion limit in minutes before violation |
| `product_status` | VARCHAR(50) | NO | Active, Discontinued, Testing |
| `created_at` | TIMESTAMP | NO | Record creation timestamp (UTC) |
| `updated_at` | TIMESTAMP | NO | Record last modified timestamp (UTC) |

---

## 2. Shipment (`shipments`)
Tracks physical movement of cold chain products between manufacturing sites and healthcare destinations.

| Column | Type | Nullable | Constraints / Description |
|---|---|---|---|
| `shipment_id` | VARCHAR(50) | NO | Primary Key. Format: `SHP-2026-000001` |
| `product_id` | VARCHAR(50) | NO | Foreign Key -> `products.product_id` |
| `origin` | VARCHAR(150) | NO | Origin facility/city |
| `destination` | VARCHAR(150) | NO | Receiving facility/city |
| `departure_time` | TIMESTAMP | NO | Actual/planned departure |
| `expected_delivery_time` | TIMESTAMP | NO | Promised delivery SLA |
| `actual_delivery_time` | TIMESTAMP | YES | Physical handover arrival timestamp |
| `shipment_status` | VARCHAR(50) | NO | Created, In_Transit, Delivered, Delayed, Cancelled |
| `issue_type` / `ground_truth_label` | VARCHAR | YES | Separate labels for deliberate timing anomalies |
| `source_actual_delivery_time` | TIMESTAMP | YES | Pre-injection delivery value for labelled chronology anomalies |
| `created_at` | TIMESTAMP | NO | Record creation timestamp (UTC) |
| `updated_at` | TIMESTAMP | NO | Record last modified timestamp (UTC) |

---

## 3. Container (`containers`)
Thermal packaging units, reefer trucks, and active cryogenic shippers holding shipments.

| Column | Type | Nullable | Constraints / Description |
|---|---|---|---|
| `container_id` | VARCHAR(50) | NO | Primary Key. Format: `CNT-000001` |
| `assigned_shipment_id` | VARCHAR(50) | YES | Foreign Key -> `shipments.shipment_id` |
| `container_type` | VARCHAR(100) | NO | Active Cryogenic VIP, Insulated Dry-Ice, Reefer |
| `capacity` | FLOAT | NO | Volume/payload capacity in Liters |
| `status` | VARCHAR(50) | NO | Available, Assigned, In_Transit, Maintenance |
| `created_at` | TIMESTAMP | NO | Record creation timestamp (UTC) |
| `updated_at` | TIMESTAMP | NO | Record last modified timestamp (UTC) |

---

## 4. Sensor (`sensors`)
IoT environmental monitoring hardware assigned to containers.

| Column | Type | Nullable | Constraints / Description |
|---|---|---|---|
| `sensor_id` | VARCHAR(100) | NO | Primary Key. Format: `SNS-CNT-000001-TEMP` |
| `sensor_type` | VARCHAR(50) | NO | TEMPERATURE, HUMIDITY, COMBO |
| `assigned_container_id` | VARCHAR(50) | YES | Foreign Key -> `containers.container_id` |
| `calibration_status` | VARCHAR(50) | NO | Valid, Expired, Failed |
| `calibration_date` | TIMESTAMP | NO | Last official calibration certificate timestamp |
| `sensor_health` | VARCHAR(50) | NO | Healthy, Warning, Faulty, Offline |
| `issue_type` / `ground_truth_label` | VARCHAR | YES | Calibration anomaly classification and ground truth |
| `source_calibration_status` | VARCHAR(50) | YES | Original state before deliberate calibration injection |
| `created_at` | TIMESTAMP | NO | Record creation timestamp (UTC) |
| `updated_at` | TIMESTAMP | NO | Record last modified timestamp (UTC) |

---

## 5. SensorReading (`sensor_readings`)
High-frequency environmental telemetry sampled at 5-minute intervals.

| Column | Type | Nullable | Constraints / Description |
|---|---|---|---|
| `reading_id` | VARCHAR(150) | NO | Primary Key. Format: `RDG-{sensor-id}-{timestamp}` |
| `sensor_id` | VARCHAR(100) | NO | Foreign Key -> `sensors.sensor_id` |
| `shipment_id` | VARCHAR(50) | YES | Foreign Key -> `shipments.shipment_id` |
| `timestamp` | TIMESTAMP | NO | Telemetry sample timestamp (Indexed) |
| `temperature` | FLOAT | YES | Measured temperature in °C |
| `humidity` | FLOAT | YES | Measured relative humidity in % RH |
| `battery_level` | FLOAT | YES | Battery state of charge (0-100%) |
| `is_anomaly` | BOOLEAN | NO | Synthetic anomaly injection flag |
| `issue_type` | VARCHAR(80) | YES | Structured anomaly type, separate from measured values |
| `ground_truth_label` | VARCHAR(100) | YES | Expected validation classification |
| `source_reading_id` | VARCHAR(150) | YES | Source sample reference for mutated synthetic data |
| `(sensor_id, timestamp)` | UNIQUE | NO | Prevents duplicate samples from one sensor |

---

## 6. RouteStop (`route_stops`)
Waypoints and cold chain transfer points along transit routes.

| Column | Type | Nullable | Constraints / Description |
|---|---|---|---|
| `stop_id` | VARCHAR(50) | NO | Primary Key. e.g. `STP-SHP-2026-000001-01` |
| `shipment_id` | VARCHAR(50) | NO | Foreign Key -> `shipments.shipment_id` |
| `stop_sequence` | INT | NO | 1, 2, 3... (Sequential order) |
| `location_name` | VARCHAR(150) | NO | Name of logistics hub or cross-dock facility |
| `latitude` | VARCHAR(50) | YES | Geographic coordinate |
| `longitude` | VARCHAR(50) | YES | Geographic coordinate |
| `planned_arrival` | TIMESTAMP | NO | Target schedule arrival |
| `actual_arrival` | TIMESTAMP | YES | Physical checkpoint arrival |
| `departure_time` | TIMESTAMP | YES | Physical checkpoint departure |
| `status` | VARCHAR(50) | NO | Pending, Arrived, Departed, Skipped |
| `issue_type` / `ground_truth_label` | VARCHAR | YES | Route delay provenance |

---

## 7. ThresholdPolicy (`threshold_policies`)
Configurable multi-tier excursion alert thresholds per product.

| Column | Type | Nullable | Constraints / Description |
|---|---|---|---|
| `policy_id` | VARCHAR(50) | NO | Primary Key. e.g. `POL-PRD-VAX-001` |
| `product_id` | VARCHAR(50) | NO | Foreign Key -> `products.product_id` |
| `policy_name` | VARCHAR(150) | NO | Descriptive policy name |
| `temp_critical_low` | FLOAT | NO | Critical freezing limit (°C) |
| `temp_warning_low` | FLOAT | NO | Low warning warning threshold (°C) |
| `temp_warning_high` | FLOAT | NO | High warning warning threshold (°C) |
| `temp_critical_high` | FLOAT | NO | Critical overheating limit (°C) |
| `humidity_min` | FLOAT | NO | Minimum allowed RH |
| `humidity_max` | FLOAT | NO | Maximum allowed RH |
| `max_excursion_duration_minutes` | INT | NO | Continuous duration before excursion trigger |
| `is_active` | BOOLEAN | NO | Policy active flag |
| `effective_start` / `effective_end` | TIMESTAMP | NO / YES | Reading-time policy selection window |
| `policy_status` | VARCHAR(30) | NO | Active or Inactive policy lifecycle |

---

## 8. Excursion (`excursions`)
Environmental boundary violations identified by the deterministic rule engine.

| Column | Type | Nullable | Constraints / Description |
|---|---|---|---|
| `excursion_id` | VARCHAR(50) | NO | Primary Key. Format: `EXC-2026-000001` |
| `shipment_id` | VARCHAR(50) | NO | Foreign Key -> `shipments.shipment_id` |
| `container_id` | VARCHAR(50) | YES | Foreign Key -> `containers.container_id` |
| `sensor_id` | VARCHAR(100) | NO | Foreign Key -> `sensors.sensor_id` |
| `policy_id` | VARCHAR(50) | YES | Foreign Key -> `threshold_policies.policy_id` |
| `excursion_type` | VARCHAR(50) | NO | TEMPERATURE_HIGH, TEMPERATURE_LOW, HUMIDITY_HIGH, MISSING_INTERVAL, CALIBRATION_FAILURE |
| `severity` | VARCHAR(50) | NO | WARNING, CRITICAL |
| `start_time` | TIMESTAMP | NO | Violation start timestamp |
| `end_time` | TIMESTAMP | YES | Violation resolution/end timestamp |
| `duration_minutes` | FLOAT | NO | Continuous violation duration |
| `peak_value` | FLOAT | YES | Maximum/minimum peak excursion temperature or RH |
| `threshold_limit` | FLOAT | YES | Breached threshold limit |
| `status` | VARCHAR(50) | NO | OPEN, ACKNOWLEDGED, RESOLVED, CLOSED |
| `root_cause` | VARCHAR(255) | YES | Root cause analysis findings |
| `review_status` / `reviewed_by` / `reviewed_at` | VARCHAR / VARCHAR / TIMESTAMP | NO / YES / YES | Quality review audit fields |

Excursion status transitions are recorded in `excursion_status_events` with actor, previous status, new status, note, and timestamp.

---

## 9. CustodyEvent (`custody_events`)
Chain-of-custody transfer records maintaining tamper-proof history.

| Column | Type | Nullable | Constraints / Description |
|---|---|---|---|
| `event_id` | VARCHAR(50) | NO | Primary Key. e.g. `CST-SHP-2026-000001-01` |
| `shipment_id` | VARCHAR(50) | NO | Foreign Key -> `shipments.shipment_id` |
| `event_timestamp` | TIMESTAMP | NO | Handover timestamp |
| `event_type` | VARCHAR(50) | NO | DEPARTURE, HANDOVER, INSPECTION, ARRIVAL, TAMPER_ALERT |
| `from_party` | VARCHAR(100) | NO | Releasing entity/officer |
| `to_party` | VARCHAR(100) | NO | Receiving entity/officer |
| `location` | VARCHAR(150) | NO | Physical handover location |
| `condition_status` | VARCHAR(50) | NO | Normal, Compromised, Inspected |
| `notes` | VARCHAR(255) | YES | Sign-off remarks |

---

## 10. CorrectiveAction (`corrective_actions`)
CAPA (Corrective and Preventive Action) remediation workflow.

| Column | Type | Nullable | Constraints / Description |
|---|---|---|---|
| `action_id` | VARCHAR(50) | NO | Primary Key. e.g. `ACT-A1B2C3D4` |
| `excursion_id` | VARCHAR(50) | NO | Foreign Key -> `excursions.excursion_id` |
| `assigned_user` | VARCHAR(100) | NO | Assigned QA engineer or technician |
| `action_description` | VARCHAR(500) | NO | Required mitigation procedure |
| `priority` | VARCHAR(50) | NO | LOW, MEDIUM, HIGH, CRITICAL |
| `status` | VARCHAR(50) | NO | OPEN, ACKNOWLEDGED, IN_PROGRESS, RESOLVED, CLOSED |
| `resolution_notes` | VARCHAR(1000) | YES | Documented remediation actions |
| `completed_date` | TIMESTAMP | YES | Action closure timestamp |

---

## 11. Alerts (`alerts`)
Real-time operational alerts for plant operators and quality dispatchers.

| Column | Type | Nullable | Constraints / Description |
|---|---|---|---|
| `alert_id` | VARCHAR(50) | NO | Primary Key. e.g. `ALT-A1B2C3D4` |
| `shipment_id` | VARCHAR(50) | NO | Foreign Key -> `shipments.shipment_id` |
| `sensor_id` | VARCHAR(100) | NO | Foreign Key -> `sensors.sensor_id` |
| `excursion_id` | VARCHAR(50) | YES | Foreign Key -> `excursions.excursion_id` |
| `severity` | VARCHAR(50) | NO | WARNING, CRITICAL |
| `description` | VARCHAR(500) | NO | Detailed alert trigger text |
| `acknowledgement_status`| VARCHAR(50) | NO | UNACKNOWLEDGED, ACKNOWLEDGED |
| `resolution_status` | VARCHAR(50) | NO | OPEN, RESOLVED, DISMISSED |
