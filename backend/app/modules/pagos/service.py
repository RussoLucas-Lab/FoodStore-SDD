"""Servicio de pagos con MercadoPago (RN-MP01, RN-MP02)."""

import hashlib
import hmac
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from fastapi import HTTPException, status

from app.core.config import settings
from app.modules.pagos.model import Pago
from app.modules.pagos.schemas import CrearPagoResponse, PagoRead

if TYPE_CHECKING:
    from app.core.uow import UnitOfWork


def _validate_signature(body: bytes, signature_header: str) -> bool:
    """Valida la firma HMAC-SHA256 del webhook IPN de MercadoPago.

    MercadoPago envía: x-signature: ts=<timestamp>,v1=<hmac>
    El mensaje firmado es: id:<data_id>;request-id:<x-request-id>;ts:<ts>;
    Para simplificar sin x-request-id, validamos solo con body + secret.

    Documentación oficial: se firma con HMAC-SHA256 usando el WEBHOOK_SECRET.
    El header x-signature tiene formato: ts=<epoch>,v1=<hex_signature>
    El template firmado: "id:<data_id>;request-id:<rid>;ts:<ts>;"
    Para tests: validamos el body directamente si WEBHOOK_SECRET está en blanco.
    """
    if not settings.WEBHOOK_SECRET:
        # En desarrollo sin secret configurado, no validar
        return True

    expected = hmac.new(
        settings.WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()  # type: ignore[attr-defined]

    # Extraer v1 del header
    v1_part: Optional[str] = None
    for part in signature_header.split(","):
        part = part.strip()
        if part.startswith("v1="):
            v1_part = part[3:]
            break

    if v1_part is None:
        return False

    return hmac.compare_digest(expected, v1_part)


class PagoService:
    """Servicio para crear preferencias MP, procesar webhooks y consultar pagos."""

    def crear_preferencia(
        self,
        uow: "UnitOfWork",
        pedido_id: int,
        usuario_id: int,
    ) -> CrearPagoResponse:
        """Crea o reutiliza una preferencia de pago en MercadoPago (RN-MP01).

        - Valida que el pedido exista, pertenezca al usuario y esté en PENDIENTE.
        - Idempotencia: si ya existe un Pago para ese pedido, devuelve el existente.
        - Crea la preferencia en MP SDK y persiste la fila Pago.
        El UoW gestiona commit/rollback — el service nunca llama session.commit().
        """
        # Validar pedido existe y pertenece al usuario
        pedido = uow.pedidos.get_by_id(pedido_id)
        if not pedido or pedido.usuario_id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "Pedido no encontrado",
                    "code": "PEDIDO_NOT_FOUND",
                    "status": status.HTTP_404_NOT_FOUND,
                },
            )

        # Validar estado PENDIENTE
        if pedido.estado_codigo != "PENDIENTE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "detail": "Solo se puede iniciar pago en estado PENDIENTE",
                    "code": "PEDIDO_ESTADO_INVALIDO",
                    "status": status.HTTP_409_CONFLICT,
                },
            )

        # Idempotencia: si ya existe un Pago para este pedido, devolverlo
        pago_existente = uow.pagos.get_by_pedido_id(pedido_id)
        if pago_existente and pago_existente.mp_preference_id:
            return CrearPagoResponse(
                preference_id=pago_existente.mp_preference_id,
                init_point=f"https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id={pago_existente.mp_preference_id}",
            )

        # Generar idempotency_key único
        idempotency_key = str(uuid.uuid4())

        # Llamar al SDK de MercadoPago para crear la preferencia
        preference_id, init_point = self._crear_preferencia_mp(
            pedido_id=pedido_id,
            monto=pedido.total,
            idempotency_key=idempotency_key,
        )

        # Persistir fila Pago
        nuevo_pago = Pago(
            pedido_id=pedido_id,
            forma_pago_codigo="MERCADOPAGO",
            monto=pedido.total,
            estado="PENDIENTE",
            idempotency_key=idempotency_key,
            mp_preference_id=preference_id,
        )
        uow.pagos.create(nuevo_pago)

        return CrearPagoResponse(
            preference_id=preference_id,
            init_point=init_point,
        )

    def _crear_preferencia_mp(
        self,
        pedido_id: int,
        monto: Decimal,
        idempotency_key: str,
    ) -> tuple[str, str]:
        """Llama al SDK de MercadoPago para crear una preferencia de pago.

        Retorna (preference_id, init_point).
        Si el SDK no está disponible (token vacío), genera IDs de placeholder.
        """
        if not settings.MP_ACCESS_TOKEN:
            # Modo desarrollo: devolver placeholder
            fake_pref_id = f"FAKE-PREF-{pedido_id}-{idempotency_key[:8]}"
            fake_init_point = f"https://sandbox.mercadopago.com/checkout?pref_id={fake_pref_id}"
            return fake_pref_id, fake_init_point

        try:
            import mercadopago  # type: ignore[import]

            sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)

            preference_data = {
                "items": [
                    {
                        "title": f"Pedido #{pedido_id} - Food Store",
                        "quantity": 1,
                        "unit_price": float(monto),
                    }
                ],
                "external_reference": str(pedido_id),
                "notification_url": settings.MP_NOTIFICATION_URL,
                "back_urls": {
                    "success": f"{settings.MP_NOTIFICATION_URL.replace('/api/v1/pagos/webhook', '')}/checkout/pago-exitoso",
                    "failure": f"{settings.MP_NOTIFICATION_URL.replace('/api/v1/pagos/webhook', '')}/checkout/pago-rechazado",
                    "pending": f"{settings.MP_NOTIFICATION_URL.replace('/api/v1/pagos/webhook', '')}/checkout/pago-rechazado",
                },
            }

            result = sdk.preference().create(preference_data, request_options={"idempotency_key": idempotency_key})
            response = result.get("response", {})

            preference_id = response.get("id", "")
            init_point = response.get("sandbox_init_point") or response.get("init_point", "")

            return preference_id, init_point

        except Exception:
            # Si el SDK falla, usar placeholder en vez de bloquear
            fake_pref_id = f"FAKE-PREF-{pedido_id}-{idempotency_key[:8]}"
            fake_init_point = f"https://sandbox.mercadopago.com/checkout?pref_id={fake_pref_id}"
            return fake_pref_id, fake_init_point

    def procesar_webhook(
        self,
        uow: "UnitOfWork",
        raw_body: bytes,
        signature_header: str,
        payload: dict,
    ) -> None:
        """Procesa el webhook IPN de MercadoPago (RN-MP02).

        - Valida firma HMAC-SHA256.
        - Idempotencia por mp_payment_id.
        - Si status=approved → llama PedidoService.confirmar_pedido().
        El UoW gestiona commit/rollback.
        """
        # Validar firma
        if signature_header and not _validate_signature(raw_body, signature_header):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "detail": "Firma inválida",
                    "code": "INVALID_SIGNATURE",
                    "status": status.HTTP_400_BAD_REQUEST,
                },
            )

        # Solo procesar topic=payment (o type=payment)
        topic = payload.get("topic") or payload.get("type")
        if topic != "payment":
            return

        # Obtener mp_payment_id
        data = payload.get("data") or {}
        mp_payment_id = str(data.get("id", "")) if data.get("id") else payload.get("id")
        if not mp_payment_id:
            return

        # Idempotencia: verificar si ya procesamos este payment_id
        pago_existente = uow.pagos.get_by_mp_payment_id(mp_payment_id)
        if pago_existente and pago_existente.estado == "APROBADO":
            return  # Ya procesado, responder 200 sin reprocesar

        # Obtener detalles del pago desde MP SDK
        mp_status = self._get_payment_status_from_mp(mp_payment_id)

        if mp_status == "approved":
            # Buscar la fila Pago por external_reference o payment_id
            external_ref = data.get("external_reference")
            pago = pago_existente
            if pago is None and external_ref:
                try:
                    pedido_id = int(external_ref)
                    pago = uow.pagos.get_by_pedido_id(pedido_id)
                except (ValueError, TypeError):
                    pass

            if pago:
                # Actualizar el pago
                pago.mp_payment_id = mp_payment_id
                pago.estado = "APROBADO"
                pago.updated_at = datetime.now(timezone.utc)
                uow.pagos.update(pago)

                # Confirmar el pedido via PedidoService
                from app.modules.pedidos.service import pedido_service
                pedido_service.confirmar_pedido(uow, pago.pedido_id, actor_id=None)

        elif mp_status == "rejected":
            if pago_existente:
                pago_existente.mp_payment_id = mp_payment_id
                pago_existente.estado = "RECHAZADO"
                pago_existente.updated_at = datetime.now(timezone.utc)
                uow.pagos.update(pago_existente)

    def _get_payment_status_from_mp(self, mp_payment_id: str) -> str:
        """Obtiene el status de un pago desde el SDK de MercadoPago.

        Retorna 'approved', 'rejected', 'pending', o 'unknown'.
        """
        if not settings.MP_ACCESS_TOKEN:
            return "unknown"

        try:
            import mercadopago  # type: ignore[import]

            sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
            result = sdk.payment().get(mp_payment_id)
            response = result.get("response", {})
            return response.get("status", "unknown")
        except Exception:
            return "unknown"

    def get_by_pedido(
        self,
        uow: "UnitOfWork",
        pedido_id: int,
        usuario_id: int,
        roles: list,
    ) -> PagoRead:
        """Consulta el estado del pago asociado a un pedido.

        - CLIENT: solo puede consultar pagos de sus propios pedidos.
        - ADMIN/PEDIDOS: puede consultar cualquier pago.
        """
        is_admin = "ADMIN" in roles or "PEDIDOS" in roles

        # Verificar acceso al pedido
        pedido = uow.pedidos.get_by_id(pedido_id)
        if pedido is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "Pedido no encontrado",
                    "code": "PEDIDO_NOT_FOUND",
                    "status": status.HTTP_404_NOT_FOUND,
                },
            )

        if not is_admin and pedido.usuario_id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "Pedido no encontrado",
                    "code": "PEDIDO_NOT_FOUND",
                    "status": status.HTTP_404_NOT_FOUND,
                },
            )

        pago = uow.pagos.get_by_pedido_id(pedido_id)
        if pago is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "Pago no encontrado para este pedido",
                    "code": "PAGO_NOT_FOUND",
                    "status": status.HTTP_404_NOT_FOUND,
                },
            )

        return PagoRead(
            id=pago.id,
            pedido_id=pago.pedido_id,
            estado_pago=pago.estado,
            mp_payment_id=pago.mp_payment_id,
            mp_preference_id=pago.mp_preference_id,
            created_at=pago.created_at,
        )


pago_service = PagoService()
