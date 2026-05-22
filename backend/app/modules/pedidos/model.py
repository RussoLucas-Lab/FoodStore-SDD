"""Modelos SQLModel para EstadoPedido, Pedido, DetallePedido e HistorialEstadoPedido."""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import Numeric, Column, JSON, String


class EstadoPedido(SQLModel, table=True):
    """Estado de un pedido con PK semántica y flag de terminal."""

    __tablename__ = "estado_pedido"

    codigo: str = Field(max_length=50, primary_key=True)
    descripcion: Optional[str] = Field(default=None, max_length=200)
    orden: int = Field(nullable=False)
    es_terminal: bool = Field(default=False, nullable=False)


class Pedido(SQLModel, table=True):
    """Pedido realizado por un usuario.

    Incluye snapshot de dirección (JSONB) e información de totales.
    El estado se gestiona mediante FSM validada en la capa de servicio.
    """

    __tablename__ = "pedido"

    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", nullable=False, index=True)
    estado_codigo: str = Field(
        foreign_key="estado_pedido.codigo",
        max_length=50,
        nullable=False,
        default="PENDIENTE",
    )

    # Snapshot inmutable de la dirección al momento del pedido
    direccion_snapshot: dict = Field(
        sa_column=Column(JSON, nullable=False),
    )

    total: Decimal = Field(
        sa_column=Column(Numeric(10, 2), nullable=False),
    )

    costo_envio: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0"),
    )

    # FK a FormaPago — guardado como dato del pedido (sin crear registro Pago aquí)
    forma_pago_codigo: Optional[str] = Field(
        default=None,
        sa_column=Column(String(50), nullable=True),
    )

    # Idempotency key para prevenir pedidos duplicados por doble-click
    idempotency_key: Optional[str] = Field(
        default=None,
        sa_column=Column(String(100), nullable=True),
    )

    # Motivo de cancelación (obligatorio si estado == CANCELADO)
    motivo_cancelacion: Optional[str] = Field(default=None, max_length=500, nullable=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Optional[datetime] = Field(default=None, nullable=True)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)


class DetallePedido(SQLModel, table=True):
    """Línea de detalle de un pedido.

    Guarda snapshots de precio y nombre del producto para preservar
    el valor histórico independientemente de cambios futuros al catálogo.
    """

    __tablename__ = "detalle_pedido"

    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedido.id", nullable=False, index=True)
    producto_id: int = Field(foreign_key="producto.id", nullable=False, index=True)

    # Snapshots inmutables al momento del pedido
    precio_snapshot: Decimal = Field(
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    nombre_snapshot: str = Field(max_length=200, nullable=False)

    cantidad: int = Field(nullable=False, ge=1)

    # Array de IDs de ingredientes personalizados (excluidos o añadidos)
    personalizacion: Optional[List[int]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )


class HistorialEstadoPedido(SQLModel, table=True):
    """Registro append-only de cambios de estado de un pedido.

    NUNCA se actualiza ni elimina. Solo INSERT.
    Proporciona trazabilidad completa del ciclo de vida del pedido.
    """

    __tablename__ = "historial_estado_pedido"

    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedido.id", nullable=False, index=True)

    # Estado anterior (nullable para la transición inicial)
    estado_desde: Optional[str] = Field(
        default=None,
        foreign_key="estado_pedido.codigo",
        max_length=50,
        nullable=True,
    )
    estado_hasta: str = Field(
        foreign_key="estado_pedido.codigo",
        max_length=50,
        nullable=False,
    )

    # Usuario o sistema que realizó el cambio
    cambiado_por_id: Optional[int] = Field(
        default=None,
        foreign_key="usuario.id",
        nullable=True,
    )
    motivo: Optional[str] = Field(default=None, max_length=500, nullable=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
