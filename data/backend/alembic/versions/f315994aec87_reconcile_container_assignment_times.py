"""Reconcile legacy assignment windows against their sensor samples.

Revision ID: f315994aec87
Revises: d9b814bc210d
"""
from alembic import op

revision = "f315994aec87"
down_revision = "d9b814bc210d"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        UPDATE container_shipment_assignments AS assignment
        SET assigned_at = LEAST(assignment.assigned_at, samples.first_sample),
            released_at = GREATEST(COALESCE(assignment.released_at, shipments.expected_delivery_time), samples.last_sample)
        FROM (
            SELECT sensors.assigned_container_id AS container_id, readings.shipment_id,
                   MIN(readings.timestamp) AS first_sample, MAX(readings.timestamp) AS last_sample
            FROM sensor_readings AS readings
            JOIN sensors ON sensors.sensor_id = readings.sensor_id
            WHERE sensors.assigned_container_id IS NOT NULL AND readings.shipment_id IS NOT NULL
            GROUP BY sensors.assigned_container_id, readings.shipment_id
        ) AS samples
        JOIN shipments ON shipments.shipment_id = samples.shipment_id
        WHERE assignment.container_id = samples.container_id AND assignment.shipment_id = samples.shipment_id
    """)


def downgrade():
    pass
