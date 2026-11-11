"""Preserve source and labels for shipment timing anomalies.

Revision ID: a702e40a215c
Revises: e6b172ac94fd
"""
from alembic import op
import sqlalchemy as sa

revision = "a702e40a215c"
down_revision = "e6b172ac94fd"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("shipments", sa.Column("issue_type", sa.String(length=80), nullable=True))
    op.add_column("shipments", sa.Column("ground_truth_label", sa.String(length=100), nullable=True))
    op.add_column("shipments", sa.Column("source_actual_delivery_time", sa.DateTime(), nullable=True))
    op.execute("UPDATE shipments SET issue_type = 'CHRONOLOGICAL_INVERSION', ground_truth_label = 'LIFECYCLE_TEMPORAL_CORRUPTION', source_actual_delivery_time = actual_delivery_time WHERE actual_delivery_time < departure_time")


def downgrade():
    op.drop_column("shipments", "source_actual_delivery_time")
    op.drop_column("shipments", "ground_truth_label")
    op.drop_column("shipments", "issue_type")
