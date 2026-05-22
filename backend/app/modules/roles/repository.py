"""Repositorio de Rol."""

from app.core.repository import BaseRepository
from app.modules.roles.model import Rol


class RolRepository(BaseRepository[Rol]):
    def __init__(self, session) -> None:
        super().__init__(session, Rol)
