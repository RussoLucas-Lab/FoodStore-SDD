"""AdminRepository — queries transversales para el módulo de administración."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import func, select as sa_select
from sqlmodel import Session, select

from app.modules.usuarios.model import Usuario
from app.modules.roles.model import UsuarioRol
from app.modules.productos.model import Producto
from app.modules.pedidos.model import DetallePedido, Pedido


class AdminRepository:
    """Repositorio transversal para administración. Sin lógica de negocio."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Gestión de usuarios
    # ------------------------------------------------------------------

    def list_usuarios(
        self,
        q: Optional[str] = None,
        activo: Optional[bool] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Usuario], int]:
        """Retorna lista paginada de usuarios con filtros opcionales."""
        base = select(Usuario).where(Usuario.deleted_at == None)  # noqa: E711
        count_q = (
            sa_select(func.count())
            .select_from(Usuario)
            .where(Usuario.deleted_at == None)  # noqa: E711
        )

        if q:
            from sqlalchemy import or_
            pattern = f"%{q}%"
            filter_expr = or_(
                Usuario.nombre.ilike(pattern),
                Usuario.apellido.ilike(pattern),
                Usuario.email.ilike(pattern),
            )
            base = base.where(filter_expr)
            count_q = count_q.where(filter_expr)

        if activo is not None:
            base = base.where(Usuario.activo == activo)
            count_q = count_q.where(Usuario.activo == activo)

        total: int = self.session.execute(count_q).scalar_one()  # type: ignore[arg-type]

        skip = (page - 1) * size
        usuarios = list(self.session.exec(base.offset(skip).limit(size)).all())

        for u in usuarios:
            _ = list(u.roles)
            for ur in u.roles:
                _ = ur.rol

        return usuarios, total

    def get_usuario_by_id(self, usuario_id: int) -> Optional[Usuario]:
        """Retorna un usuario por ID con roles precargados."""
        usuario = self.session.get(Usuario, usuario_id)
        if usuario is not None:
            _ = list(usuario.roles)
            for ur in usuario.roles:
                _ = ur.rol
        return usuario

    def email_exists(self, email: str, exclude_id: int) -> bool:
        """Verifica si el email ya está en uso por otro usuario."""
        stmt = (
            sa_select(func.count())
            .select_from(Usuario)
            .where(Usuario.email == email)
            .where(Usuario.id != exclude_id)
        )
        count: int = self.session.execute(stmt).scalar_one()  # type: ignore[arg-type]
        return count > 0

    def update_usuario(
        self,
        usuario_id: int,
        nombre: Optional[str],
        apellido: Optional[str],
        email: Optional[str],
    ) -> Usuario:
        """Actualiza nombre, apellido, email del usuario."""
        usuario = self.session.get(Usuario, usuario_id)
        if nombre is not None:
            usuario.nombre = nombre
        if apellido is not None:
            usuario.apellido = apellido
        if email is not None:
            usuario.email = email
        self.session.add(usuario)
        self.session.flush()
        self.session.refresh(usuario)
        _ = list(usuario.roles)
        for ur in usuario.roles:
            _ = ur.rol
        return usuario

    def set_roles(
        self,
        usuario_id: int,
        roles: List[str],
        asignado_por_id: Optional[int] = None,
    ) -> None:
        """Reemplaza las filas en UsuarioRol para el usuario."""
        existing = list(
            self.session.exec(
                select(UsuarioRol).where(UsuarioRol.usuario_id == usuario_id)
            ).all()
        )
        for ur in existing:
            self.session.delete(ur)
        self.session.flush()

        for rol_codigo in roles:
            ur = UsuarioRol(
                usuario_id=usuario_id,
                rol_codigo=rol_codigo,
                asignado_por_id=asignado_por_id,
            )
            self.session.add(ur)
        self.session.flush()

    def set_activo(self, usuario_id: int, activo: bool) -> Usuario:
        """Actualiza el campo activo del usuario."""
        usuario = self.session.get(Usuario, usuario_id)
        usuario.activo = activo
        self.session.add(usuario)
        self.session.flush()
        self.session.refresh(usuario)
        _ = list(usuario.roles)
        for ur in usuario.roles:
            _ = ur.rol
        return usuario

    def count_admins_activos(self, exclude_usuario_id: Optional[int] = None) -> int:
        """Cuenta los administradores activos, excluyendo opcionalmente a uno."""
        stmt = (
            sa_select(func.count())
            .select_from(Usuario)
            .join(UsuarioRol, UsuarioRol.usuario_id == Usuario.id)
            .where(UsuarioRol.rol_codigo == "ADMIN")
            .where(Usuario.activo == True)  # noqa: E712
            .where(Usuario.deleted_at == None)  # noqa: E711
        )
        if exclude_usuario_id is not None:
            stmt = stmt.where(Usuario.id != exclude_usuario_id)
        return self.session.execute(stmt).scalar_one()  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Métricas
    # ------------------------------------------------------------------

    def get_resumen(self) -> dict:
        """Retorna las 4 métricas del resumen del dashboard."""
        now = datetime.now(timezone.utc)

        total_pedidos: int = self.session.execute(
            sa_select(func.count())
            .select_from(Pedido)
            .where(Pedido.deleted_at == None)  # noqa: E711
        ).scalar_one()  # type: ignore[arg-type]

        # SQLite: strftime('%Y-%m', created_at) — PostgreSQL usaría date_trunc('month', ...)
        mes_actual = now.strftime("%Y-%m")
        ventas_raw = self.session.execute(
            sa_select(func.coalesce(func.sum(Pedido.total), 0))
            .select_from(Pedido)
            .where(Pedido.estado_codigo == "ENTREGADO")
            .where(func.strftime("%Y-%m", Pedido.created_at) == mes_actual)
        ).scalar_one()
        ventas_mes = Decimal(str(ventas_raw))

        productos_activos: int = self.session.execute(
            sa_select(func.count())
            .select_from(Producto)
            .where(Producto.deleted_at == None)  # noqa: E711
            .where(Producto.disponible == True)  # noqa: E712
        ).scalar_one()  # type: ignore[arg-type]

        usuarios_activos: int = self.session.execute(
            sa_select(func.count())
            .select_from(Usuario)
            .where(Usuario.activo == True)  # noqa: E712
            .where(Usuario.deleted_at == None)  # noqa: E711
        ).scalar_one()  # type: ignore[arg-type]

        return {
            "total_pedidos": total_pedidos,
            "ventas_mes": ventas_mes,
            "productos_activos": productos_activos,
            "usuarios_activos": usuarios_activos,
        }

    def get_ventas_por_periodo(self, periodo: str) -> List[dict]:
        """Retorna ventas agrupadas por período.

        SQLite: func.strftime. PostgreSQL: func.date_trunc.
        """
        fmt_map = {"dia": "%Y-%m-%d", "semana": "%Y-%W", "mes": "%Y-%m"}
        fmt = fmt_map.get(periodo, "%Y-%m")

        stmt = (
            sa_select(
                func.strftime(fmt, Pedido.created_at).label("fecha"),
                func.sum(Pedido.total).label("total"),
            )
            .select_from(Pedido)
            .where(Pedido.estado_codigo == "ENTREGADO")
            .where(Pedido.deleted_at == None)  # noqa: E711
            .group_by(func.strftime(fmt, Pedido.created_at))
            .order_by(func.strftime(fmt, Pedido.created_at))
        )
        rows = self.session.execute(stmt).all()  # type: ignore[arg-type]
        return [
            {"fecha": row.fecha, "total": Decimal(str(row.total))}
            for row in rows
        ]

    def get_productos_top(self, limit: int = 10) -> List[dict]:
        """Retorna los N productos más vendidos por unidades en pedidos ENTREGADOS."""
        stmt = (
            sa_select(
                DetallePedido.producto_id,
                DetallePedido.nombre_snapshot.label("nombre"),
                func.sum(DetallePedido.cantidad).label("unidades_vendidas"),
                func.sum(
                    DetallePedido.precio_snapshot * DetallePedido.cantidad
                ).label("total_generado"),
            )
            .select_from(DetallePedido)
            .join(Pedido, Pedido.id == DetallePedido.pedido_id)
            .where(Pedido.estado_codigo == "ENTREGADO")
            .where(Pedido.deleted_at == None)  # noqa: E711
            .group_by(DetallePedido.producto_id, DetallePedido.nombre_snapshot)
            .order_by(func.sum(DetallePedido.cantidad).desc())
            .limit(limit)
        )
        rows = self.session.execute(stmt).all()  # type: ignore[arg-type]
        return [
            {
                "producto_id": row.producto_id,
                "nombre": row.nombre,
                "unidades_vendidas": int(row.unidades_vendidas),
                "total_generado": Decimal(str(row.total_generado)),
            }
            for row in rows
        ]

    def get_pedidos_por_estado(self) -> List[dict]:
        """Retorna el conteo de pedidos agrupados por estado."""
        stmt = (
            sa_select(
                Pedido.estado_codigo.label("estado"),
                func.count().label("cantidad"),
            )
            .select_from(Pedido)
            .where(Pedido.deleted_at == None)  # noqa: E711
            .group_by(Pedido.estado_codigo)
        )
        rows = self.session.execute(stmt).all()  # type: ignore[arg-type]
        return [
            {"estado": row.estado, "cantidad": int(row.cantidad)}
            for row in rows
        ]
