"""AdminService — lógica de negocio stateless para el módulo de administración."""

import math
from typing import List, Optional

from fastapi import HTTPException, status

from app.modules.admin.schemas import (
    ActivarUsuarioRequest,
    MetricasResumenResponse,
    PedidosPorEstadoItem,
    PedidosPorEstadoResponse,
    ProductoTopItem,
    ProductosTopResponse,
    UsuarioAdminRead,
    UsuarioAdminUpdate,
    UsuariosListResponse,
    VentaItem,
    VentasPorPeriodoResponse,
)


def _to_usuario_read(usuario) -> UsuarioAdminRead:
    """Convierte un Usuario ORM a UsuarioAdminRead con roles como lista de códigos."""
    roles = [ur.rol_codigo for ur in usuario.roles]
    return UsuarioAdminRead(
        id=usuario.id,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        activo=usuario.activo,
        roles=roles,
        created_at=usuario.created_at,
    )


class AdminService:
    """Servicio stateless para administración. Nunca llama session.commit()."""

    # ------------------------------------------------------------------
    # Gestión de usuarios
    # ------------------------------------------------------------------

    def list_usuarios(
        self,
        uow,
        q: Optional[str] = None,
        activo: Optional[bool] = None,
        page: int = 1,
        size: int = 20,
    ) -> UsuariosListResponse:
        """Lista usuarios paginados con filtros opcionales."""
        usuarios, total = uow.admin.list_usuarios(q=q, activo=activo, page=page, size=size)
        pages = math.ceil(total / size) if size > 0 else 0
        return UsuariosListResponse(
            items=[_to_usuario_read(u) for u in usuarios],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    def update_usuario(
        self, uow, usuario_id: int, data: UsuarioAdminUpdate
    ) -> UsuarioAdminRead:
        """Actualiza nombre, apellido, email. 404 si no existe, 409 si email duplicado."""
        usuario = uow.admin.get_usuario_by_id(usuario_id)
        if usuario is None or usuario.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Usuario no encontrado.", "code": "USUARIO_NOT_FOUND"},
            )

        if data.email is not None and data.email != usuario.email:
            if uow.admin.email_exists(data.email, usuario_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"detail": "Email ya en uso.", "code": "EMAIL_DUPLICATE"},
                )

        updated = uow.admin.update_usuario(
            usuario_id, data.nombre, data.apellido, data.email
        )
        return _to_usuario_read(updated)

    def asignar_roles(
        self,
        uow,
        usuario_id: int,
        roles: List[str],
        current_user_id: int,
    ) -> UsuarioAdminRead:
        """Asigna roles a un usuario. Valida RN-RB03 (último ADMIN) y RN-RB04 (propios roles)."""
        # RN-RB04: No puede cambiar sus propios roles
        if usuario_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "detail": "No puede cambiar sus propios roles.",
                    "code": "CANNOT_CHANGE_OWN_ROLES",
                },
            )

        usuario = uow.admin.get_usuario_by_id(usuario_id)
        if usuario is None or usuario.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Usuario no encontrado.", "code": "USUARIO_NOT_FOUND"},
            )

        # RN-RB03: Si se quita el rol ADMIN, debe quedar al menos 1 ADMIN activo
        current_roles = [ur.rol_codigo for ur in usuario.roles]
        if "ADMIN" in current_roles and "ADMIN" not in roles:
            remaining = uow.admin.count_admins_activos(exclude_usuario_id=usuario_id)
            if remaining == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "detail": "No se puede quitar el rol ADMIN del último administrador activo.",
                        "code": "LAST_ADMIN",
                    },
                )

        uow.admin.set_roles(usuario_id, roles, asignado_por_id=current_user_id)
        updated = uow.admin.get_usuario_by_id(usuario_id)
        return _to_usuario_read(updated)

    def activar_usuario(
        self, uow, usuario_id: int, activo: bool
    ) -> UsuarioAdminRead:
        """Activa/desactiva un usuario. Valida que no sea el último ADMIN activo."""
        usuario = uow.admin.get_usuario_by_id(usuario_id)
        if usuario is None or usuario.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Usuario no encontrado.", "code": "USUARIO_NOT_FOUND"},
            )

        if not activo:
            current_roles = [ur.rol_codigo for ur in usuario.roles]
            if "ADMIN" in current_roles and usuario.activo:
                remaining = uow.admin.count_admins_activos(exclude_usuario_id=usuario_id)
                if remaining == 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "detail": "No se puede desactivar al último administrador activo.",
                            "code": "LAST_ADMIN",
                        },
                    )

        updated = uow.admin.set_activo(usuario_id, activo)
        return _to_usuario_read(updated)

    # ------------------------------------------------------------------
    # Métricas
    # ------------------------------------------------------------------

    def get_resumen(self, uow) -> MetricasResumenResponse:
        """Retorna el resumen de métricas del dashboard."""
        data = uow.admin.get_resumen()
        return MetricasResumenResponse(**data)

    def get_ventas_por_periodo(self, uow, periodo: str) -> VentasPorPeriodoResponse:
        """Retorna ventas agrupadas por período."""
        series = uow.admin.get_ventas_por_periodo(periodo)
        return VentasPorPeriodoResponse(
            periodo=periodo,
            series=[VentaItem(**s) for s in series],
        )

    def get_productos_top(self, uow, limit: int = 10) -> ProductosTopResponse:
        """Retorna los productos más vendidos."""
        items = uow.admin.get_productos_top(limit)
        return ProductosTopResponse(items=[ProductoTopItem(**item) for item in items])

    def get_pedidos_por_estado(self, uow) -> PedidosPorEstadoResponse:
        """Retorna el conteo de pedidos por estado."""
        items = uow.admin.get_pedidos_por_estado()
        return PedidosPorEstadoResponse(
            items=[PedidosPorEstadoItem(**item) for item in items]
        )


admin_service = AdminService()
