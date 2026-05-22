"""Schemas Pydantic para el perfil del usuario autenticado."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UsuarioMeRead(BaseModel):
    """Schema de lectura del perfil propio (sin password_hash)."""

    id: int
    nombre: str
    apellido: str
    email: str
    activo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UsuarioMeUpdate(BaseModel):
    """Schema para actualizar datos propios (solo nombre y apellido)."""

    nombre: Optional[str] = None
    apellido: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    """Schema para cambiar la contraseña del usuario autenticado."""

    password_actual: str
    password_nuevo: str = Field(min_length=8)
    password_nuevo_confirmar: str
