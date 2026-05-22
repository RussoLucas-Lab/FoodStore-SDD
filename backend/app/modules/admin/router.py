"""Router de Admin — endpoints REST bajo /api/v1/admin."""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query

from app.core.security import require_role
from app.core.uow import UnitOfWork
from app.modules.admin.schemas import (
    ActivarUsuarioRequest,
    AsignarRolesRequest,
    MetricasResumenResponse,
    PedidosPorEstadoResponse,
    ProductosTopResponse,
    UsuarioAdminRead,
    UsuarioAdminUpdate,
    UsuariosListResponse,
    VentasPorPeriodoResponse,
)
from app.modules.admin.service import admin_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Gestión de usuarios
# ---------------------------------------------------------------------------

@router.get(
    "/usuarios",
    response_model=UsuariosListResponse,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def listar_usuarios(
    q: Optional[str] = None,
    activo: Optional[bool] = None,
    page: int = 1,
    size: int = 20,
):
    """Lista usuarios con filtros opcionales. Solo ADMIN."""
    with UnitOfWork() as uow:
        return admin_service.list_usuarios(uow, q=q, activo=activo, page=page, size=size)


@router.put(
    "/usuarios/{usuario_id}",
    response_model=UsuarioAdminRead,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def actualizar_usuario(usuario_id: int, body: UsuarioAdminUpdate):
    """Actualiza nombre, apellido, email de un usuario. Solo ADMIN."""
    with UnitOfWork() as uow:
        return admin_service.update_usuario(uow, usuario_id, body)


@router.patch(
    "/usuarios/{usuario_id}/roles",
    response_model=UsuarioAdminRead,
)
def asignar_roles(
    usuario_id: int,
    body: AsignarRolesRequest,
    current_user=Depends(require_role(["ADMIN"])),
):
    """Asigna roles a un usuario. Solo ADMIN."""
    with UnitOfWork() as uow:
        return admin_service.asignar_roles(uow, usuario_id, body.roles, current_user.id)


@router.patch(
    "/usuarios/{usuario_id}/activar",
    response_model=UsuarioAdminRead,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def activar_usuario(usuario_id: int, body: ActivarUsuarioRequest):
    """Activa o desactiva un usuario. Solo ADMIN."""
    with UnitOfWork() as uow:
        return admin_service.activar_usuario(uow, usuario_id, body.activo)


# ---------------------------------------------------------------------------
# Métricas
# ---------------------------------------------------------------------------

@router.get(
    "/metricas/resumen",
    response_model=MetricasResumenResponse,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def metricas_resumen():
    """Retorna el resumen de métricas del dashboard. Solo ADMIN."""
    with UnitOfWork() as uow:
        return admin_service.get_resumen(uow)


@router.get(
    "/metricas/ventas",
    response_model=VentasPorPeriodoResponse,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def metricas_ventas(
    periodo: Literal["dia", "semana", "mes"] = "mes",
):
    """Retorna ventas agrupadas por período. Solo ADMIN."""
    with UnitOfWork() as uow:
        return admin_service.get_ventas_por_periodo(uow, periodo)


@router.get(
    "/metricas/productos-top",
    response_model=ProductosTopResponse,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def metricas_productos_top(
    limit: int = Query(default=10, ge=1, le=50),
):
    """Retorna los productos más vendidos. Solo ADMIN."""
    with UnitOfWork() as uow:
        return admin_service.get_productos_top(uow, limit)


@router.get(
    "/metricas/pedidos-por-estado",
    response_model=PedidosPorEstadoResponse,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def metricas_pedidos_por_estado():
    """Retorna el conteo de pedidos por estado. Solo ADMIN."""
    with UnitOfWork() as uow:
        return admin_service.get_pedidos_por_estado(uow)
