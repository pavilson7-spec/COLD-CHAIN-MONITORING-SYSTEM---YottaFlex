"""Add anomaly provenance to sensor and route records.

Revision ID: d9b814bc210d
Revises: c1840b780f6a
"""
from alembic import op
import sqlalchemy as sa

revision = "d9b814bc210d"
down_revision = "c1840b780f6a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sensors", sa.Column("issue_type", sa.String(length=80), nullable=True))
    op.add_column("sensors", sa.Column("ground_truth_label", sa.String(length=100), nullable=True))
    op.add_column("sensors", sa.Column("source_calibration_status", sa.String(length=50), nullable=True))
    op.add_column("route_stops", sa.Column("issue_type", sa.String(length=80), nullable=True))
    op.add_column("route_stops", sa.Column("ground_truth_label", sa.String(length=100), nullable=True))
    op.execute("UPDATE sensors SET issue_type = 'CALIBRATION_FAILURE', ground_truth_label = 'UNVERIFIED_SENSOR_DATA', source_calibration_status = 'Valid' WHERE calibration_status IN ('Expired', 'Failed')")
    op.execute("UPDATE sensor_readings SET is_anomaly = TRUE, issue_type = COALESCE(issue_type, 'PHYSICAL_OUT_OF_BOUNDS'), ground_truth_label = COALESCE(ground_truth_label, 'CRITICAL_HARDWARE_ANOMALY'), source_reading_id = COALESCE(source_reading_id, reading_id) WHERE temperature < -80 OR temperature > 70 OR humidity < 0 OR humidity > 100")
    op.execute("UPDATE route_stops SET issue_type = 'ROUTE_STOP_DELAY', ground_truth_label = 'DELAY_REQUIRES_NOTIFICATION' WHERE actual_arrival > planned_arrival + INTERVAL '30 minutes'")
    op.execute("""
        INSERT INTO container_shipment_assignments (container_id, shipment_id, assigned_at, released_at, assignment_status)
        SELECT sensors.assigned_container_id, readings.shipment_id, MIN(readings.timestamp),
               COALESCE(shipments.actual_delivery_time, shipments.expected_delivery_time),
               CASE WHEN shipments.actual_delivery_time IS NULL THEN 'Assigned' ELSE 'Released' END
        FROM sensor_readings AS readings
        JOIN sensors ON sensors.sensor_id = readings.sensor_id
        JOIN shipments ON shipments.shipment_id = readings.shipment_id
        WHERE sensors.assigned_container_id IS NOT NULL AND readings.shipment_id IS NOT NULL
        GROUP BY sensors.assigned_container_id, readings.shipment_id, shipments.actual_delivery_time, shipments.expected_delivery_time
        ON CONFLICT (container_id, shipment_id) DO NOTHING
    """)


def downgrade():
    op.drop_column("route_stops", "ground_truth_label")
    op.drop_column("route_stops", "issue_type")
    op.drop_column("sensors", "source_calibration_status")
    op.drop_column("sensors", "ground_truth_label")
    op.drop_column("sensors", "issue_type")
