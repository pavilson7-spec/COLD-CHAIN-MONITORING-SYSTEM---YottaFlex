"""Add effective policies, anomaly provenance, and excursion history.

Revision ID: e6b172ac94fd
Revises: b39359ed00a0
"""
from alembic import op
import sqlalchemy as sa

revision = "e6b172ac94fd"
down_revision = "b39359ed00a0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("threshold_policies", sa.Column("effective_start", sa.DateTime(), nullable=True))
    op.add_column("threshold_policies", sa.Column("effective_end", sa.DateTime(), nullable=True))
    op.add_column("threshold_policies", sa.Column("policy_status", sa.String(length=30), nullable=True))
    op.execute("UPDATE threshold_policies SET effective_start = created_at, policy_status = CASE WHEN is_active THEN 'Active' ELSE 'Inactive' END")
    op.alter_column("threshold_policies", "effective_start", nullable=False)
    op.alter_column("threshold_policies", "policy_status", nullable=False)

    op.add_column("sensor_readings", sa.Column("issue_type", sa.String(length=80), nullable=True))
    op.add_column("sensor_readings", sa.Column("ground_truth_label", sa.String(length=100), nullable=True))
    op.add_column("sensor_readings", sa.Column("source_reading_id", sa.String(length=150), nullable=True))

    op.add_column("excursions", sa.Column("container_id", sa.String(length=50), nullable=True))
    op.create_foreign_key("fk_excursions_container_id", "excursions", "containers", ["container_id"], ["container_id"])
    op.create_index("ix_excursions_container_id", "excursions", ["container_id"])
    op.add_column("excursions", sa.Column("review_status", sa.String(length=30), nullable=True))
    op.add_column("excursions", sa.Column("reviewed_by", sa.String(length=100), nullable=True))
    op.add_column("excursions", sa.Column("reviewed_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE excursions SET review_status = 'Pending'")
    op.alter_column("excursions", "review_status", nullable=False)

    op.create_table(
        "excursion_status_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("excursion_id", sa.String(length=50), nullable=False),
        sa.Column("from_status", sa.String(length=50), nullable=True),
        sa.Column("to_status", sa.String(length=50), nullable=False),
        sa.Column("changed_by", sa.String(length=100), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["excursion_id"], ["excursions.excursion_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_excursion_status_events_excursion_id", "excursion_status_events", ["excursion_id"])
    op.drop_index("ix_sensor_readings_sensor_timestamp", table_name="sensor_readings")
    op.create_unique_constraint("uq_sensor_readings_sensor_timestamp", "sensor_readings", ["sensor_id", "timestamp"])


def downgrade():
    op.drop_constraint("uq_sensor_readings_sensor_timestamp", "sensor_readings", type_="unique")
    op.create_index("ix_sensor_readings_sensor_timestamp", "sensor_readings", ["sensor_id", "timestamp"])
    op.drop_index("ix_excursion_status_events_excursion_id", table_name="excursion_status_events")
    op.drop_table("excursion_status_events")
    op.drop_column("excursions", "reviewed_at")
    op.drop_column("excursions", "reviewed_by")
    op.drop_column("excursions", "review_status")
    op.drop_index("ix_excursions_container_id", table_name="excursions")
    op.drop_constraint("fk_excursions_container_id", "excursions", type_="foreignkey")
    op.drop_column("excursions", "container_id")
    op.drop_column("sensor_readings", "source_reading_id")
    op.drop_column("sensor_readings", "ground_truth_label")
    op.drop_column("sensor_readings", "issue_type")
    op.drop_column("threshold_policies", "policy_status")
    op.drop_column("threshold_policies", "effective_end")
    op.drop_column("threshold_policies", "effective_start")
