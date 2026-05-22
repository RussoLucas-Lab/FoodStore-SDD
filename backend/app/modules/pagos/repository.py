"""Repositorio de Pago."""

from typing import Optional

from sqlmodel import select

from app.core.repository import BaseRepository
from app.modules.pagos.model import Pago


class PagoRepository(BaseRepository[Pago]):
    """Operaciones de BD para la entidad Pago."""

    def __init__(self, session) -> None:
        super().__init__(session, Pago)

    def get_by_pedido_id(self, pedido_id: int) -> Optional[Pago]:
        """Retorna el pago asociado a un pedido, o None si no existe."""
        stmt = select(Pago).where(Pago.pedido_id == pedido_id)
        return self.session.exec(stmt).first()

    def get_by_mp_payment_id(self, mp_payment_id: str) -> Optional[Pago]:
        """Retorna el pago por su ID de pago en MercadoPago."""
        stmt = select(Pago).where(Pago.mp_payment_id == mp_payment_id)
        return self.session.exec(stmt).first()
