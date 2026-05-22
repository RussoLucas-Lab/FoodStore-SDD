"""add forma_pago_codigo idempotency_key costo_envio to pedido

Revision ID: 003
Revises: 002
Create Date: 2026-05-21

"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("pedido", sa.Column("forma_pago_codigo", sa.String(length=50), nullable=True))
    op.add_column("pedido", sa.Column("idempotency_key", sa.String(length=100), nullable=True))
    op.add_column(
        "pedido",
        sa.Column(
            "costo_envio",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        ),
    )
    # Partial unique index: uniqueness only when idempotency_key IS NOT NULL
    op.execute(
        "CREATE UNIQUE INDEX ix_pedido_usuario_idempotency_key "
        "ON pedido (usuario_id, idempotency_key) "
        "WHERE idempotency_key IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_pedido_usuario_idempotency_key")
    op.drop_column("pedido", "costo_envio")
    op.drop_column("pedido", "idempotency_key")
    op.drop_column("pedido", "forma_pago_codigo")
