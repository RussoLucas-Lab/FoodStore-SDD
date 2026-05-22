"""Modelo SQLModel para Direccion de entrega del cliente."""

from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class Direccion(SQLModel, table=True):
    """Dirección de entrega asociada a un usuario autenticado.

    Soporta soft delete via deleted_at.
    Invariante: a lo sumo una dirección activa con es_principal=True por usuario
    (garantizado en DireccionService, no a nivel de constraint SQL).
    """

    __tablename__ = "direccion"

    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(nullable=False, index=True)
    calle: str = Field(max_length=200, nullable=False)
    numero: str = Field(max_length=20, nullable=False)
    piso: Optional[str] = Field(default=None, max_length=10)
    depto: Optional[str] = Field(default=None, max_length=10)
    ciudad: str = Field(max_length=100, nullable=False)
    provincia: str = Field(max_length=100, nullable=False)
    codigo_postal: str = Field(max_length=10, nullable=False)
    referencia: Optional[str] = Field(default=None, max_length=500)
    es_principal: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)
