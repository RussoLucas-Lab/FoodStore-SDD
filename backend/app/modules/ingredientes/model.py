"""Modelo SQLModel para Ingrediente."""

from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship


class Ingrediente(SQLModel, table=True):
    """Ingrediente con flag de alérgeno y soft delete."""

    __tablename__ = "ingrediente"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100, nullable=False, unique=True)
    es_alergeno: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)

    # Relationships
    productos: List["ProductoIngrediente"] = Relationship(back_populates="ingrediente")  # type: ignore[name-defined]
