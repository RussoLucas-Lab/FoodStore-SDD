"""Schemas Pydantic para el módulo de pagos."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CrearPagoRequest(BaseModel):
    """Cuerpo para crear una preferencia de pago en MercadoPago."""

    pedido_id: int


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class CrearPagoResponse(BaseModel):
    """Respuesta de creación de preferencia MercadoPago."""

    preference_id: str
    init_point: str


class PagoRead(BaseModel):
    """Representa el estado actual de un pago."""

    id: int
    pedido_id: int
    estado_pago: str
    mp_payment_id: Optional[str] = None
    mp_preference_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookPayload(BaseModel):
    """Payload del webhook IPN de MercadoPago."""

    topic: Optional[str] = None
    type: Optional[str] = None
    data: Optional[dict] = None
    action: Optional[str] = None
    id: Optional[str] = None
