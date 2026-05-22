"""Repositorios para el módulo de pedidos."""

from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlmodel import select

from app.core.repository import BaseRepository
from app.modules.pedidos.model import (
    DetallePedido,
    HistorialEstadoPedido,
    Pedido,
)
from app.modules.pagos.model import FormaPago


class PedidoRepository(BaseRepository[Pedido]):
    def __init__(self, session) -> None:
        super().__init__(session, Pedido)

    def get_by_usuario_idempotency_key(
        self, usuario_id: int, key: str
    ) -> Optional[Pedido]:
        stmt = (
            select(Pedido)
            .where(Pedido.usuario_id == usuario_id)
            .where(Pedido.idempotency_key == key)
            .where(Pedido.deleted_at == None)  # noqa: E711
        )
        return self.session.exec(stmt).first()

    def get_detalles_by_pedido_id(self, pedido_id: int) -> List[DetallePedido]:
        """Retorna todos los detalles de un pedido."""
        stmt = select(DetallePedido).where(DetallePedido.pedido_id == pedido_id)
        return list(self.session.exec(stmt).all())

    def listar_paginado(
        self,
        usuario_id: int,
        solo_propios: bool,
        estado_codigo: Optional[str],
        page: int,
        size: int,
    ) -> Tuple[List[Pedido], int]:
        """Retorna pedidos paginados con filtro opcional de usuario y estado.

        Args:
            usuario_id: ID del actor (usado solo si solo_propios=True).
            solo_propios: Si True, filtra por usuario_id = actor_id.
            estado_codigo: Filtro por estado (None = todos los estados).
            page: Número de página (1-indexed).
            size: Tamaño de la página.

        Returns:
            Tupla (lista de pedidos, total de registros).
        """
        base_stmt = select(Pedido).where(Pedido.deleted_at == None)  # noqa: E711

        if solo_propios:
            base_stmt = base_stmt.where(Pedido.usuario_id == usuario_id)

        if estado_codigo:
            base_stmt = base_stmt.where(Pedido.estado_codigo == estado_codigo)

        # Contar total
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total: int = self.session.exec(count_stmt).one()  # type: ignore[assignment]

        # Paginar
        offset = (page - 1) * size
        data_stmt = (
            base_stmt
            .order_by(Pedido.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        items = list(self.session.exec(data_stmt).all())
        return items, total

    def get_detalle(self, pedido_id: int) -> Optional[Pedido]:
        """Retorna un pedido activo por ID o None si no existe / está eliminado."""
        stmt = (
            select(Pedido)
            .where(Pedido.id == pedido_id)
            .where(Pedido.deleted_at == None)  # noqa: E711
        )
        return self.session.exec(stmt).first()

    def get_historial(self, pedido_id: int) -> List[HistorialEstadoPedido]:
        """Retorna el historial de estados de un pedido ordenado por created_at ASC."""
        stmt = (
            select(HistorialEstadoPedido)
            .where(HistorialEstadoPedido.pedido_id == pedido_id)
            .order_by(HistorialEstadoPedido.created_at.asc())
        )
        return list(self.session.exec(stmt).all())


class DetallePedidoRepository(BaseRepository[DetallePedido]):
    def __init__(self, session) -> None:
        super().__init__(session, DetallePedido)

    def list_by_pedido(self, pedido_id: int) -> List[DetallePedido]:
        stmt = select(DetallePedido).where(DetallePedido.pedido_id == pedido_id)
        return list(self.session.exec(stmt).all())


class HistorialEstadoPedidoRepository(BaseRepository[HistorialEstadoPedido]):
    def __init__(self, session) -> None:
        super().__init__(session, HistorialEstadoPedido)

    def list_by_pedido(self, pedido_id: int) -> List[HistorialEstadoPedido]:
        stmt = (
            select(HistorialEstadoPedido)
            .where(HistorialEstadoPedido.pedido_id == pedido_id)
            .order_by(HistorialEstadoPedido.created_at.asc())
        )
        return list(self.session.exec(stmt).all())


class FormaPagoRepository(BaseRepository[FormaPago]):
    def __init__(self, session) -> None:
        super().__init__(session, FormaPago)

    def get_by_codigo(self, codigo: str) -> Optional[FormaPago]:
        return self.session.get(FormaPago, codigo)

    def list_habilitadas(self) -> List[FormaPago]:
        stmt = select(FormaPago).where(FormaPago.habilitado == True)  # noqa: E712
        return list(self.session.exec(stmt).all())
