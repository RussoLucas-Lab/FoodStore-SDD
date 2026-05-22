"""Modelo SQLModel para Categoria con FK autoreferencial."""

from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.orm import relationship as sa_relationship


class Categoria(SQLModel, table=True):
    """Categoría de producto con soporte para jerarquía (parent_id autoreferencial)."""

    __tablename__ = "categoria"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100, nullable=False)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    parent_id: Optional[int] = Field(
        default=None,
        foreign_key="categoria.id",
        nullable=True,
    )
    orden: int = Field(default=0, nullable=False)
    activa: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)

    # Relationships — self-referential con remote_side explícito
    subcategorias: List["Categoria"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={
            "foreign_keys": "[Categoria.parent_id]",
            "primaryjoin": "Categoria.parent_id == Categoria.id",
        },
    )
    parent: Optional["Categoria"] = Relationship(
        back_populates="subcategorias",
        sa_relationship_kwargs={
            "foreign_keys": "[Categoria.parent_id]",
            "primaryjoin": "Categoria.parent_id == Categoria.id",
            "remote_side": "[Categoria.id]",
        },
    )
