"""Track reusable container shipment assignments over time.

Revision ID: c1840b780f6a
Revises: a702e40a215c
"""
from alembic import op
import sqlalchemy as sa

revision = "c1840b780f6a"
down_revision = "a702e40a215c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "container_shipment_assignments",
        sa.Column("container_id", sa.String(length=50), nullable=False),
        sa.Column("shipment_id", sa.String(length=50), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.Column("released_at", sa.DateTime(), nullable=True),
        sa.Column("assignment_status", sa.String(length=30), nullable=False),
        sa.ForeignKeyConstraint(["container_id"], ["containers.container_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shipment_id"], ["shipments.shipment_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("container_id", "shipment_id", name="pk_container_shipment_assignments"),
    )
    op.create_index("ix_container_assignments_shipment_id", "container_shipment_assignments", ["shipment_id"])
    op.execute("""
        INSERT INTO container_shipment_assignments (container_id, shipment_id, assigned_at, released_at, assignment_status)
        SELECT container_id, assigned_shipment_id, departure_time, actual_delivery_time,
               CASE WHEN actual_delivery_time IS NULL THEN 'Assigned' ELSE 'Released' END
        FROM containers JOIN shipments ON shipments.shipment_id = containers.assigned_shipment_id
    """)


def downgrade():
    op.drop_index("ix_container_assignments_shipment_id", table_name="container_shipment_assignments")
    op.drop_table("container_shipment_assignments")
