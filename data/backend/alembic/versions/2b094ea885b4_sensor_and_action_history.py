"""Track calibration and corrective action lifecycle changes.

Revision ID: 2b094ea885b4
Revises: f315994aec87
"""
from alembic import op
import sqlalchemy as sa

revision = "2b094ea885b4"
down_revision = "f315994aec87"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sensor_calibration_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sensor_id", sa.String(length=100), nullable=False),
        sa.Column("from_status", sa.String(length=50), nullable=False),
        sa.Column("to_status", sa.String(length=50), nullable=False),
        sa.Column("calibration_date", sa.DateTime(), nullable=False),
        sa.Column("changed_by", sa.String(length=100), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sensor_id"], ["sensors.sensor_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sensor_calibration_events_sensor_id", "sensor_calibration_events", ["sensor_id"])
    op.create_table(
        "corrective_action_status_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("action_id", sa.String(length=50), nullable=False),
        sa.Column("from_status", sa.String(length=50), nullable=True),
        sa.Column("to_status", sa.String(length=50), nullable=False),
        sa.Column("changed_by", sa.String(length=100), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["action_id"], ["corrective_actions.action_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_corrective_action_status_events_action_id", "corrective_action_status_events", ["action_id"])
    op.execute("INSERT INTO corrective_action_status_events (action_id, from_status, to_status, changed_by, note, changed_at) SELECT action_id, NULL, status, 'Migration', 'Status captured during audit history initialization', created_at FROM corrective_actions")


def downgrade():
    op.drop_index("ix_corrective_action_status_events_action_id", table_name="corrective_action_status_events")
    op.drop_table("corrective_action_status_events")
    op.drop_index("ix_sensor_calibration_events_sensor_id", table_name="sensor_calibration_events")
    op.drop_table("sensor_calibration_events")
