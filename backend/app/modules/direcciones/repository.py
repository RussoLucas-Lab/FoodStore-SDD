"""Repositorio de Direccion — queries específicas del módulo."""

from typing import List, Optional

from sqlmodel import select

from app.core.repository import BaseRepository
from app.modules.direcciones.model import Direccion


class DireccionRepository(BaseRepository[Direccion]):
    """Repositorio con operaciones específicas para Direccion."""

    def __init__(self, session) -> None:
        super().__init__(session, Direccion)

    def list_by_usuario(self, usuario_id: int) -> List[Direccion]:
        """Retorna las direcciones activas del usuario, con la principal primero."""
        stmt = (
            select(Direccion)
            .where(Direccion.usuario_id == usuario_id)
            .where(Direccion.deleted_at == None)  # noqa: E711
            .order_by(Direccion.es_principal.desc(), Direccion.id.asc())  # type: ignore[union-attr]
        )
        return list(self.session.exec(stmt).all())

    def count_activas_by_usuario(self, usuario_id: int) -> int:
        """Cuenta direcciones activas (sin soft delete) del usuario."""
        stmt = (
            select(Direccion)
            .where(Direccion.usuario_id == usuario_id)
            .where(Direccion.deleted_at == None)  # noqa: E711
        )
        return len(list(self.session.exec(stmt).all()))

    def get_principal_by_usuario(self, usuario_id: int) -> Optional[Direccion]:
        """Retorna la dirección principal activa del usuario, o None."""
        stmt = (
            select(Direccion)
            .where(Direccion.usuario_id == usuario_id)
            .where(Direccion.es_principal == True)  # noqa: E712
            .where(Direccion.deleted_at == None)  # noqa: E711
        )
        return self.session.exec(stmt).first()

    def get_by_id_and_usuario(self, direccion_id: int, usuario_id: int) -> Optional[Direccion]:
        """Retorna la dirección si pertenece al usuario y no está eliminada, o None."""
        stmt = (
            select(Direccion)
            .where(Direccion.id == direccion_id)
            .where(Direccion.usuario_id == usuario_id)
            .where(Direccion.deleted_at == None)  # noqa: E711
        )
        return self.session.exec(stmt).first()
