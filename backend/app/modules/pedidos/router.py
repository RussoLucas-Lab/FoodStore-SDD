"""Router de Pedidos — endpoints de pedidos y formas de pago."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, Query, status

from app.core.security import get_current_user, require_role
from app.core.uow import UnitOfWork
from app.modules.pedidos.schemas import (
    CambiarEstadoRequest,
    CambiarEstadoResponse,
    CancelarPedidoRequest,
    FormaPagoRead,
    HistorialEstadoRead,
    PedidoCreate,
    PedidoDetailRead,
    PedidoRead,
)
from app.modules.pedidos.service import forma_pago_service, pedido_service

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /pedidos/formas-pago — debe estar ANTES de /{pedido_id} (evitar conflicto)
# ---------------------------------------------------------------------------

@router.get(
    "/formas-pago",
    response_model=List[FormaPagoRead],
)
def listar_formas_pago(
    current_user=Depends(get_current_user),
):
    """Lista las formas de pago habilitadas para el selector de checkout."""
    with UnitOfWork() as uow:
        return forma_pago_service.list_habilitadas(uow)


# ---------------------------------------------------------------------------
# POST /pedidos — crear pedido
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=PedidoRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_pedido(
    body: PedidoCreate,
    current_user=Depends(get_current_user),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    """Crea un pedido atómico desde el carrito del cliente autenticado (RN-PE01)."""
    with UnitOfWork() as uow:
        return pedido_service.crear(uow, current_user.id, body, idempotency_key)


# ---------------------------------------------------------------------------
# GET /pedidos — listado paginado
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
)
def listar_pedidos(
    estado_codigo: Optional[str] = Query(default=None, description="Filtrar por estado FSM"),
    page: int = Query(default=1, ge=1, description="Número de página"),
    size: int = Query(default=20, ge=1, le=100, description="Resultados por página"),
    current_user=Depends(get_current_user),
):
    """Lista pedidos con paginación.

    - CLIENT: solo ve sus propios pedidos.
    - ADMIN / PEDIDOS: ven todos los pedidos.
    """
    roles = [ur.rol_codigo for ur in current_user.roles]
    with UnitOfWork() as uow:
        return pedido_service.listar(
            uow,
            actor_id=current_user.id,
            actor_roles=roles,
            estado_codigo=estado_codigo,
            page=page,
            size=size,
        )


# ---------------------------------------------------------------------------
# GET /pedidos/{pedido_id}/historial — historial de estados
# ---------------------------------------------------------------------------

@router.get(
    "/{pedido_id}/historial",
    response_model=List[HistorialEstadoRead],
    status_code=status.HTTP_200_OK,
)
def get_historial_pedido(
    pedido_id: int,
    current_user=Depends(get_current_user),
):
    """Retorna el historial de estados de un pedido en orden cronológico.

    CLIENT solo puede ver el historial de sus propios pedidos.
    """
    roles = [ur.rol_codigo for ur in current_user.roles]
    with UnitOfWork() as uow:
        return pedido_service.get_historial(
            uow,
            pedido_id=pedido_id,
            actor_id=current_user.id,
            actor_roles=roles,
        )


# ---------------------------------------------------------------------------
# GET /pedidos/{pedido_id} — detalle completo
# ---------------------------------------------------------------------------

@router.get(
    "/{pedido_id}",
    response_model=PedidoDetailRead,
    status_code=status.HTTP_200_OK,
)
def get_pedido(
    pedido_id: int,
    current_user=Depends(get_current_user),
):
    """Retorna el detalle completo de un pedido (items, historial, pago).

    CLIENT solo puede ver sus propios pedidos; ADMIN/PEDIDOS acceden a cualquiera.
    """
    roles = [ur.rol_codigo for ur in current_user.roles]
    with UnitOfWork() as uow:
        return pedido_service.get_detalle(
            uow,
            pedido_id=pedido_id,
            actor_id=current_user.id,
            actor_roles=roles,
        )


# ---------------------------------------------------------------------------
# PATCH /pedidos/{pedido_id}/estado — cambiar estado via FSM
# ---------------------------------------------------------------------------

@router.patch(
    "/{pedido_id}/estado",
    response_model=CambiarEstadoResponse,
    status_code=status.HTTP_200_OK,
)
def cambiar_estado_pedido(
    pedido_id: int,
    body: CambiarEstadoRequest,
    current_user=Depends(get_current_user),
):
    """Cambia el estado de un pedido via FSM (RN-FS01).

    La transición PENDIENTE → CONFIRMADO es exclusivamente automática (webhook).
    El motivo es obligatorio al cancelar.
    """
    roles = [ur.rol_codigo for ur in current_user.roles]
    with UnitOfWork() as uow:
        return pedido_service.cambiar_estado(
            uow,
            pedido_id=pedido_id,
            nuevo_estado=body.nuevo_estado,
            motivo=body.motivo,
            actor_id=current_user.id,
            actor_roles=roles,
        )


# ---------------------------------------------------------------------------
# DELETE /pedidos/{pedido_id} — cancelación propia del cliente
# ---------------------------------------------------------------------------

@router.delete(
    "/{pedido_id}",
    response_model=CambiarEstadoResponse,
    status_code=status.HTTP_200_OK,
)
def cancelar_pedido_propio(
    pedido_id: int,
    body: CancelarPedidoRequest,
    current_user=Depends(require_role(["CLIENT"])),
):
    """Cancela un pedido propio del cliente autenticado.

    Solo disponible para rol CLIENT. El pedido debe estar en estado PENDIENTE.
    El motivo es obligatorio.
    """
    with UnitOfWork() as uow:
        return pedido_service.cancelar_propio(
            uow,
            pedido_id=pedido_id,
            actor_id=current_user.id,
            motivo=body.motivo,
        )
