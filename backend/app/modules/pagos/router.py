"""Router de Pagos — /api/v1/pagos."""

from fastapi import APIRouter, Depends, Header, Request, status
from typing import Optional

from app.core.security import get_current_user, require_role
from app.core.uow import UnitOfWork
from app.modules.pagos.schemas import CrearPagoRequest, CrearPagoResponse, PagoRead
from app.modules.pagos.service import pago_service

router = APIRouter()


@router.post(
    "/crear",
    response_model=CrearPagoResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_preferencia(
    body: CrearPagoRequest,
    current_user=Depends(require_role(["CLIENT"])),
):
    """Crea o reutiliza una preferencia de pago en MercadoPago para el pedido indicado (RN-MP01)."""
    with UnitOfWork() as uow:
        result = pago_service.crear_preferencia(uow, body.pedido_id, current_user.id)
    # Si la respuesta es para un pago existente (idempotencia), devolver 200
    return result


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
)
async def webhook_ipn(
    request: Request,
    x_signature: Optional[str] = Header(default=None, alias="x-signature"),
):
    """Endpoint público que recibe notificaciones IPN de MercadoPago (RN-MP02).

    Sin autenticación JWT — validado con firma HMAC-SHA256.
    """
    raw_body = await request.body()
    payload = {}
    try:
        import json
        payload = json.loads(raw_body) if raw_body else {}
    except Exception:
        payload = {}

    # También aceptar query params de MercadoPago (topic + id en query string)
    topic = request.query_params.get("topic")
    data_id = request.query_params.get("id")
    if topic and data_id and not payload:
        payload = {"topic": topic, "data": {"id": data_id}}
    elif topic and data_id:
        if "topic" not in payload:
            payload["topic"] = topic
        if "data" not in payload:
            payload["data"] = {"id": data_id}

    with UnitOfWork() as uow:
        pago_service.procesar_webhook(
            uow,
            raw_body=raw_body,
            signature_header=x_signature or "",
            payload=payload,
        )

    return {"status": "ok"}


@router.get(
    "/{pedido_id}",
    response_model=PagoRead,
    status_code=status.HTTP_200_OK,
)
def get_pago_por_pedido(
    pedido_id: int,
    current_user=Depends(require_role(["CLIENT", "ADMIN", "PEDIDOS"])),
):
    """Consulta el estado del pago asociado a un pedido (RN-MP03)."""
    # Obtener roles del usuario
    roles = [ur.rol_codigo for ur in current_user.roles]

    with UnitOfWork() as uow:
        return pago_service.get_by_pedido(uow, pedido_id, current_user.id, roles)
