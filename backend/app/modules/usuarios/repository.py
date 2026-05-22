"""Repositorio de Usuario."""

from typing import Optional
from sqlmodel import select

from app.core.repository import BaseRepository
from app.modules.usuarios.model import Usuario


class UsuarioRepository(BaseRepository[Usuario]):
    """Operaciones de BD para Usuario."""

    def __init__(self, session) -> None:
        super().__init__(session, Usuario)

    def get_by_email(self, email: str) -> Optional[Usuario]:
        """Retorna el usuario por email, o None si no existe (incluyendo soft-deleted)."""
        stmt = select(Usuario).where(Usuario.email == email)
        return self.session.exec(stmt).first()
