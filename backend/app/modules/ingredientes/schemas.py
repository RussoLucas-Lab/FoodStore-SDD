"""Schemas Pydantic/SQLModel para Ingrediente."""

from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel


class IngredienteCreate(BaseModel):
    """Schema para crear un ingrediente."""

    nombre: str
    es_alergeno: bool = False


class IngredienteUpdate(BaseModel):
    """Schema para actualizar un ingrediente (todos los campos opcionales)."""

    nombre: Optional[str] = None
    es_alergeno: Optional[bool] = None


class IngredienteRead(BaseModel):
    """Schema de lectura de ingrediente."""

    id: int
    nombre: str
    es_alergeno: bool
    deleted_at: Optional[datetime]

    model_config = {"from_attributes": True}


class PaginatedIngredientes(BaseModel):
    """Respuesta paginada de ingredientes."""

    items: List[IngredienteRead]
    total: int
    page: int
    size: int
    pages: int
