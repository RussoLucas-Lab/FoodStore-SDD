"""Schemas Pydantic para el módulo de pedidos."""

from decimal import Decimal
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator

from app.modules.pagos.schemas import PagoRead  # noqa: F401 — reexported


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ItemPedidoCreate(BaseModel):
    producto_id: int
    cantidad: int
    personalizacion: Optional[List[int]] = None
    precio_esperado: Optional[Decimal] = None

    @field_validator("producto_id")
    @classmethod
    def producto_id_positivo(cls, v: int) -> int:
        if v < 1:
            raise ValueError("producto_id debe ser >= 1")
        return v

    @field_validator("cantidad")
    @classmethod
    def cantidad_positiva(cls, v: int) -> int:
        if v < 1:
            raise ValueError("cantidad debe ser >= 1")
        return v


class PedidoCreate(BaseModel):
    direccion_id: int
    forma_pago_codigo: str
    items: List[ItemPedidoCreate]
    notas: Optional[str] = None

    @field_validator("items")
    @classmethod
    def items_no_vacio(cls, v: List[ItemPedidoCreate]) -> List[ItemPedidoCreate]:
        if len(v) == 0:
            raise ValueError("El carrito está vacío")
        return v


class CancelarPedidoRequest(BaseModel):
    """Cuerpo para cancelar un pedido propio (rol CLIENT)."""

    motivo: str


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class DetallePedidoRead(BaseModel):
    id: int
    producto_id: int
    nombre_snapshot: str
    precio_snapshot: Decimal
    cantidad: int
    personalizacion: Optional[List[int]] = None

    model_config = {"from_attributes": True}


class HistorialEstadoRead(BaseModel):
    """Snapshot de un cambio de estado del pedido (append-only)."""

    id: int
    estado_desde: Optional[str] = None
    estado_hasta: str
    cambiado_por_id: Optional[int] = None
    motivo: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PedidoRead(BaseModel):
    id: int
    estado_codigo: str
    total: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class PedidoDetailRead(PedidoRead):
    """Detalle completo de un pedido con items, historial y pago anidados."""

    direccion_snapshot: dict
    items: List[DetallePedidoRead]
    historial: List[HistorialEstadoRead]
    pago: Optional[PagoRead] = None


class PedidoDetail(PedidoRead):
    subtotal: Decimal
    costo_envio: Decimal
    direccion_snapshot: dict
    items: List[DetallePedidoRead]


# ---------------------------------------------------------------------------
# FSM — cambio de estado
# ---------------------------------------------------------------------------

class CambiarEstadoRequest(BaseModel):
    """Cuerpo para cambiar el estado de un pedido via FSM."""

    nuevo_estado: str
    motivo: Optional[str] = None


class CambiarEstadoResponse(BaseModel):
    """Respuesta tras cambiar el estado del pedido."""

    id: int
    estado_codigo: str
    estado_anterior: str
    total: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# FormaPago schemas
# ---------------------------------------------------------------------------

class FormaPagoRead(BaseModel):
    codigo: str
    descripcion: Optional[str] = None

    model_config = {"from_attributes": True}
