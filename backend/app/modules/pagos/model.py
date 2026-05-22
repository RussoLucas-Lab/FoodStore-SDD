"""Modelos SQLModel para FormaPago y Pago."""

from typing import Optional
from decimal import Decimal
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import Numeric, Column


class FormaPago(SQLModel, table=True):
    """Forma de pago con PK semántica (código string) y flag habilitado."""

    __tablename__ = "forma_pago"

    codigo: str = Field(max_length=50, primary_key=True)
    descripcion: Optional[str] = Field(default=None, max_length=200)
    habilitado: bool = Field(default=True, nullable=False)


class Pago(SQLModel, table=True):
    """Registro de pago vinculado a un pedido.

    mp_payment_id, idempotency_key y external_reference son únicos
    para garantizar idempotencia con MercadoPago.
    """

    __tablename__ = "pago"

    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedido.id", nullable=False, index=True)
    forma_pago_codigo: str = Field(
        foreign_key="forma_pago.codigo",
        max_length=50,
        nullable=False,
    )
    monto: Decimal = Field(
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    estado: str = Field(max_length=50, nullable=False, default="pending")

    # Campos MercadoPago
    mp_payment_id: Optional[str] = Field(
        default=None,
        max_length=100,
        unique=True,
        nullable=True,
    )
    mp_preference_id: Optional[str] = Field(
        default=None,
        max_length=200,
        nullable=True,
    )
    idempotency_key: Optional[str] = Field(
        default=None,
        max_length=100,
        unique=True,
        nullable=True,
    )
    external_reference: Optional[str] = Field(
        default=None,
        max_length=100,
        unique=True,
        nullable=True,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Optional[datetime] = Field(default=None, nullable=True)
