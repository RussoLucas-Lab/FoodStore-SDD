"""Schemas Pydantic/SQLModel para Categoria."""

from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel


class CategoriaCreate(BaseModel):
    """Schema para crear una categoría."""

    nombre: str
    parent_id: Optional[int] = None
    descripcion: Optional[str] = None
    orden: int = 0


class CategoriaUpdate(BaseModel):
    """Schema para actualizar una categoría (todos los campos opcionales)."""

    nombre: Optional[str] = None
    parent_id: Optional[int] = None
    descripcion: Optional[str] = None
    orden: Optional[int] = None
    activa: Optional[bool] = None


class CategoriaRead(BaseModel):
    """Schema de lectura de categoría."""

    id: int
    nombre: str
    parent_id: Optional[int]
    descripcion: Optional[str]
    orden: int
    activa: bool
    deleted_at: Optional[datetime]

    model_config = {"from_attributes": True}


class CategoriaTreeRead(BaseModel):
    """Schema de lectura en árbol (con subcategorías recursivas)."""

    id: int
    nombre: str
    parent_id: Optional[int]
    descripcion: Optional[str]
    orden: int
    activa: bool
    subcategorias: List["CategoriaTreeRead"] = []

    model_config = {"from_attributes": True}


# Necesario para forward references recursivas
CategoriaTreeRead.model_rebuild()
