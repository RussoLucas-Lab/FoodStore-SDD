"""Repositorio de Ingrediente."""

from typing import List, Optional

from sqlmodel import select

from app.core.repository import BaseRepository
from app.modules.ingredientes.model import Ingrediente


class IngredienteRepository(BaseRepository[Ingrediente]):
    def __init__(self, session) -> None:
        super().__init__(session, Ingrediente)

    def get_by_nombre(self, nombre: str) -> Optional[Ingrediente]:
        """Retorna el ingrediente con el nombre dado (no eliminado), o None si no existe."""
        statement = (
            select(Ingrediente)
            .where(Ingrediente.nombre == nombre)
            .where(Ingrediente.deleted_at == None)  # noqa: E711
        )
        return self.session.exec(statement).first()

    def list_paginated(
        self,
        page: int = 1,
        size: int = 20,
        es_alergeno: Optional[bool] = None,
    ) -> tuple[List[Ingrediente], int]:
        """Retorna una tupla (items, total) con filtro opcional por es_alergeno."""
        from sqlalchemy import func, select as sa_select

        base_stmt = select(Ingrediente).where(Ingrediente.deleted_at == None)  # noqa: E711
        count_stmt = sa_select(func.count()).select_from(Ingrediente).where(
            Ingrediente.deleted_at == None  # noqa: E711
        )

        if es_alergeno is not None:
            base_stmt = base_stmt.where(Ingrediente.es_alergeno == es_alergeno)
            count_stmt = count_stmt.where(Ingrediente.es_alergeno == es_alergeno)

        result = self.session.execute(count_stmt)  # type: ignore[arg-type]
        total: int = result.scalar_one()
        skip = (page - 1) * size
        items = list(self.session.exec(base_stmt.offset(skip).limit(size)).all())
        return items, total
