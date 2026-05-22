"""Modelos SQLModel para Rol y UsuarioRol."""

from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship


class Rol(SQLModel, table=True):
    """Rol con PK semántica (código string)."""

    __tablename__ = "rol"

    codigo: str = Field(max_length=50, primary_key=True)
    descripcion: Optional[str] = Field(default=None, max_length=200)

    # Relationships
    usuarios: List["UsuarioRol"] = Relationship(back_populates="rol")  # type: ignore[name-defined]


class UsuarioRol(SQLModel, table=True):
    """Tabla pivot N:M entre Usuario y Rol."""

    __tablename__ = "usuario_rol"

    usuario_id: int = Field(foreign_key="usuario.id", primary_key=True)
    rol_codigo: str = Field(foreign_key="rol.codigo", primary_key=True)
    asignado_por_id: Optional[int] = Field(
        default=None,
        foreign_key="usuario.id",
        nullable=True,
    )
    asignado_en: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    usuario: Optional["Usuario"] = Relationship(  # type: ignore[name-defined]
        back_populates="roles",
        sa_relationship_kwargs={"foreign_keys": "[UsuarioRol.usuario_id]"},
    )
    rol: Optional[Rol] = Relationship(back_populates="usuarios")
