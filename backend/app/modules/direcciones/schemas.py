"""Schemas Pydantic para el módulo de direcciones."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class DireccionCreate(BaseModel):
    """Payload para crear una dirección de entrega."""

    calle: str
    numero: str
    piso: Optional[str] = None
    depto: Optional[str] = None
    ciudad: str
    provincia: str
    codigo_postal: str
    referencia: Optional[str] = None
    es_principal: bool = False


class DireccionUpdate(BaseModel):
    """Payload para actualizar una dirección. No modifica es_principal (usa PATCH /principal)."""

    calle: Optional[str] = None
    numero: Optional[str] = None
    piso: Optional[str] = None
    depto: Optional[str] = None
    ciudad: Optional[str] = None
    provincia: Optional[str] = None
    codigo_postal: Optional[str] = None
    referencia: Optional[str] = None


class DireccionRead(BaseModel):
    """Respuesta de una dirección de entrega."""

    id: int
    usuario_id: int
    calle: str
    numero: str
    piso: Optional[str] = None
    depto: Optional[str] = None
    ciudad: str
    provincia: str
    codigo_postal: str
    referencia: Optional[str] = None
    es_principal: bool
    created_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DireccionSetPrincipalResponse(BaseModel):
    """Respuesta del PATCH /principal."""

    message: str
    direccion: DireccionRead
