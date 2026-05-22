"""Schemas Pydantic/SQLModel para Producto."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.categorias.schemas import CategoriaRead
from app.modules.ingredientes.schemas import IngredienteRead


class ProductoIngredienteRead(BaseModel):
    """Schema de lectura de la relación Producto-Ingrediente."""

    ingrediente_id: int
    es_removible: bool
    ingrediente: Optional[IngredienteRead] = None

    model_config = {"from_attributes": True}


class ProductoCategoriaRead(BaseModel):
    """Schema de lectura de la relación Producto-Categoria."""

    categoria_id: int
    categoria: Optional[CategoriaRead] = None

    model_config = {"from_attributes": True}


class ProductoCreate(BaseModel):
    """Schema para crear un producto."""

    nombre: str
    descripcion: Optional[str] = None
    precio_base: Decimal
    stock_cantidad: int = 0
    disponible: bool = True
    imagen_url: Optional[str] = None
    categoria_ids: List[int] = Field(default_factory=list)
    ingrediente_ids: List[int] = Field(default_factory=list)


class ProductoUpdate(BaseModel):
    """Schema para actualizar un producto (todos los campos opcionales)."""

    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio_base: Optional[Decimal] = None
    stock_cantidad: Optional[int] = None
    disponible: Optional[bool] = None
    imagen_url: Optional[str] = None
    categoria_ids: Optional[List[int]] = None
    ingrediente_ids: Optional[List[int]] = None


class ProductoRead(BaseModel):
    """Schema de lectura de producto con categorías e ingredientes embebidos."""

    id: int
    nombre: str
    descripcion: Optional[str]
    precio_base: Decimal
    stock_cantidad: int
    disponible: bool
    imagen_url: Optional[str]
    created_at: datetime
    deleted_at: Optional[datetime]
    categorias: List[CategoriaRead] = Field(default_factory=list)
    ingredientes: List[IngredienteRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ProductoListResponse(BaseModel):
    """Respuesta paginada de productos."""

    items: List[ProductoRead]
    total: int
    page: int
    size: int
    pages: int


class StockUpdate(BaseModel):
    """Schema para actualizar el stock de un producto."""

    cantidad: int = Field(ge=0)


class DisponibilidadUpdate(BaseModel):
    """Schema para actualizar la disponibilidad de un producto."""

    disponible: bool
