"""Initial schema — all tables for Food Store.

Revision ID: 001
Revises:
Create Date: 2026-05-20 00:00:00.000000

Tables created (in dependency order):
  rol, usuario, usuario_rol, refresh_token,
  categoria, ingrediente, producto, producto_categoria, producto_ingrediente,
  direccion_entrega,
  estado_pedido, pedido, detalle_pedido, historial_estado_pedido,
  forma_pago, pago
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. rol
    # ------------------------------------------------------------------
    op.create_table(
        "rol",
        sa.Column("codigo", sa.String(length=50), nullable=False),
        sa.Column("descripcion", sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint("codigo"),
    )

    # ------------------------------------------------------------------
    # 2. usuario
    # ------------------------------------------------------------------
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("apellido", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_usuario_email", "usuario", ["email"], unique=True)

    # ------------------------------------------------------------------
    # 3. usuario_rol (pivot N:M)
    # ------------------------------------------------------------------
    op.create_table(
        "usuario_rol",
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("rol_codigo", sa.String(length=50), nullable=False),
        sa.Column("asignado_por_id", sa.Integer(), nullable=True),
        sa.Column(
            "asignado_en",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["asignado_por_id"],
            ["usuario.id"],
            use_alter=True,
            name="fk_usuario_rol_asignado_por",
        ),
        sa.ForeignKeyConstraint(["rol_codigo"], ["rol.codigo"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("usuario_id", "rol_codigo"),
    )

    # ------------------------------------------------------------------
    # 4. refresh_token
    # ------------------------------------------------------------------
    op.create_table(
        "refresh_token",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_refresh_token_usuario_id", "refresh_token", ["usuario_id"])

    # ------------------------------------------------------------------
    # 5. categoria
    # ------------------------------------------------------------------
    op.create_table(
        "categoria",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("descripcion", sa.String(length=500), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre"),
    )

    # ------------------------------------------------------------------
    # 6. ingrediente
    # ------------------------------------------------------------------
    op.create_table(
        "ingrediente",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("descripcion", sa.String(length=500), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre"),
    )

    # ------------------------------------------------------------------
    # 7. producto
    # ------------------------------------------------------------------
    op.create_table(
        "producto",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("precio_base", sa.Numeric(10, 2), nullable=False),
        sa.Column("stock_cantidad", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("disponible", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("imagen_url", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("precio_base >= 0", name="ck_producto_precio_positivo"),
        sa.CheckConstraint("stock_cantidad >= 0", name="ck_producto_stock_positivo"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # 8. producto_categoria (pivot N:M)
    # ------------------------------------------------------------------
    op.create_table(
        "producto_categoria",
        sa.Column("producto_id", sa.Integer(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["categoria_id"], ["categoria.id"]),
        sa.ForeignKeyConstraint(["producto_id"], ["producto.id"]),
        sa.PrimaryKeyConstraint("producto_id", "categoria_id"),
    )

    # ------------------------------------------------------------------
    # 9. producto_ingrediente (pivot N:M)
    # ------------------------------------------------------------------
    op.create_table(
        "producto_ingrediente",
        sa.Column("producto_id", sa.Integer(), nullable=False),
        sa.Column("ingrediente_id", sa.Integer(), nullable=False),
        sa.Column("es_removible", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["ingrediente_id"], ["ingrediente.id"]),
        sa.ForeignKeyConstraint(["producto_id"], ["producto.id"]),
        sa.PrimaryKeyConstraint("producto_id", "ingrediente_id"),
    )

    # ------------------------------------------------------------------
    # 10. direccion_entrega
    # ------------------------------------------------------------------
    op.create_table(
        "direccion_entrega",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("calle", sa.String(length=200), nullable=False),
        sa.Column("numero", sa.String(length=20), nullable=False),
        sa.Column("piso", sa.String(length=10), nullable=True),
        sa.Column("departamento", sa.String(length=10), nullable=True),
        sa.Column("barrio", sa.String(length=100), nullable=True),
        sa.Column("ciudad", sa.String(length=100), nullable=False),
        sa.Column("provincia", sa.String(length=100), nullable=False),
        sa.Column("codigo_postal", sa.String(length=10), nullable=False),
        sa.Column("indicaciones", sa.String(length=500), nullable=True),
        sa.Column("es_principal", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_direccion_entrega_usuario_id", "direccion_entrega", ["usuario_id"])

    # ------------------------------------------------------------------
    # 11. estado_pedido
    # ------------------------------------------------------------------
    op.create_table(
        "estado_pedido",
        sa.Column("codigo", sa.String(length=50), nullable=False),
        sa.Column("descripcion", sa.String(length=200), nullable=True),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.Column("es_terminal", sa.Boolean(), nullable=False, server_default="false"),
        sa.PrimaryKeyConstraint("codigo"),
    )

    # ------------------------------------------------------------------
    # 12. pedido
    # ------------------------------------------------------------------
    op.create_table(
        "pedido",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("estado_codigo", sa.String(length=50), nullable=False),
        sa.Column("direccion_snapshot", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("motivo_cancelacion", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["estado_codigo"], ["estado_pedido.codigo"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pedido_usuario_id", "pedido", ["usuario_id"])

    # ------------------------------------------------------------------
    # 13. detalle_pedido
    # ------------------------------------------------------------------
    op.create_table(
        "detalle_pedido",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pedido_id", sa.Integer(), nullable=False),
        sa.Column("producto_id", sa.Integer(), nullable=False),
        sa.Column("precio_snapshot", sa.Numeric(10, 2), nullable=False),
        sa.Column("nombre_snapshot", sa.String(length=200), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("personalizacion", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["pedido_id"], ["pedido.id"]),
        sa.ForeignKeyConstraint(["producto_id"], ["producto.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_detalle_pedido_pedido_id", "detalle_pedido", ["pedido_id"])
    op.create_index("ix_detalle_pedido_producto_id", "detalle_pedido", ["producto_id"])

    # ------------------------------------------------------------------
    # 14. historial_estado_pedido
    # ------------------------------------------------------------------
    op.create_table(
        "historial_estado_pedido",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pedido_id", sa.Integer(), nullable=False),
        sa.Column("estado_desde", sa.String(length=50), nullable=True),
        sa.Column("estado_hasta", sa.String(length=50), nullable=False),
        sa.Column("cambiado_por_id", sa.Integer(), nullable=True),
        sa.Column("motivo", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["cambiado_por_id"], ["usuario.id"]),
        sa.ForeignKeyConstraint(
            ["estado_desde"],
            ["estado_pedido.codigo"],
            use_alter=True,
            name="fk_historial_desde",
        ),
        sa.ForeignKeyConstraint(["estado_hasta"], ["estado_pedido.codigo"]),
        sa.ForeignKeyConstraint(["pedido_id"], ["pedido.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_historial_pedido_id", "historial_estado_pedido", ["pedido_id"])

    # ------------------------------------------------------------------
    # 15. forma_pago
    # ------------------------------------------------------------------
    op.create_table(
        "forma_pago",
        sa.Column("codigo", sa.String(length=50), nullable=False),
        sa.Column("descripcion", sa.String(length=200), nullable=True),
        sa.Column("habilitado", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("codigo"),
    )

    # ------------------------------------------------------------------
    # 16. pago
    # ------------------------------------------------------------------
    op.create_table(
        "pago",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pedido_id", sa.Integer(), nullable=False),
        sa.Column("forma_pago_codigo", sa.String(length=50), nullable=False),
        sa.Column("monto", sa.Numeric(10, 2), nullable=False),
        sa.Column("estado", sa.String(length=50), nullable=False),
        sa.Column("mp_payment_id", sa.String(length=100), nullable=True),
        sa.Column("idempotency_key", sa.String(length=100), nullable=True),
        sa.Column("external_reference", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["forma_pago_codigo"], ["forma_pago.codigo"]),
        sa.ForeignKeyConstraint(["pedido_id"], ["pedido.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mp_payment_id"),
        sa.UniqueConstraint("idempotency_key"),
        sa.UniqueConstraint("external_reference"),
    )
    op.create_index("ix_pago_pedido_id", "pago", ["pedido_id"])


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table("pago")
    op.drop_table("forma_pago")
    op.drop_table("historial_estado_pedido")
    op.drop_table("detalle_pedido")
    op.drop_table("pedido")
    op.drop_table("estado_pedido")
    op.drop_table("direccion_entrega")
    op.drop_table("producto_ingrediente")
    op.drop_table("producto_categoria")
    op.drop_table("producto")
    op.drop_table("ingrediente")
    op.drop_table("categoria")
    op.drop_table("refresh_token")
    op.drop_table("usuario_rol")
    op.drop_table("usuario")
    op.drop_table("rol")
