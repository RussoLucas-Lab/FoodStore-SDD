"""Modelos SQLModel para Producto, ProductoCategoria y ProductoIngrediente."""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Numeric, CheckConstraint, Column


class Producto(SQLModel, table=True):
    """Producto del catálogo con precio, stock y soft delete.

    Constraints de BD:
    - precio_base >= 0
    - stock_cantidad >= 0
    """

    __tablename__ = "producto"
    __table_args__ = (
        CheckConstraint("precio_base >= 0", name="ck_producto_precio_positivo"),
        CheckConstraint("stock_cantidad >= 0", name="ck_producto_stock_positivo"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=200, nullable=False)
    descripcion: Optional[str] = Field(default=None)
    precio_base: Decimal = Field(
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    stock_cantidad: int = Field(default=0, nullable=False)
    disponible: bool = Field(default=True, nullable=False)
    imagen_url: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)

    # Relationships
    categorias: List["ProductoCategoria"] = Relationship(back_populates="producto")
    ingredientes: List["ProductoIngrediente"] = Relationship(back_populates="producto")


class ProductoCategoria(SQLModel, table=True):
    """Tabla pivot N:M entre Producto y Categoria."""

    __tablename__ = "producto_categoria"

    producto_id: int = Field(foreign_key="producto.id", primary_key=True)
    categoria_id: int = Field(foreign_key="categoria.id", primary_key=True)

    # Relationships
    producto: Optional[Producto] = Relationship(back_populates="categorias")
    categoria: Optional["Categoria"] = Relationship()  # type: ignore[name-defined]


class ProductoIngrediente(SQLModel, table=True):
    """Tabla pivot N:M entre Producto e Ingrediente con flag de removible."""

    __tablename__ = "producto_ingrediente"

    producto_id: int = Field(foreign_key="producto.id", primary_key=True)
    ingrediente_id: int = Field(foreign_key="ingrediente.id", primary_key=True)
    es_removible: bool = Field(default=False, nullable=False)

    # Relationships
    producto: Optional[Producto] = Relationship(back_populates="ingredientes")
    ingrediente: Optional["Ingrediente"] = Relationship(back_populates="productos")  # type: ignore[name-defined]
