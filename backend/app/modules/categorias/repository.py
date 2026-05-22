"""Repositorio de Categoria."""

from typing import List, Optional

from sqlmodel import select

from app.core.repository import BaseRepository
from app.modules.categorias.model import Categoria


class CategoriaRepository(BaseRepository[Categoria]):
    def __init__(self, session) -> None:
        super().__init__(session, Categoria)

    def get_all_active(self) -> List[Categoria]:
        """Retorna todas las categorías activas (sin deleted_at) como lista plana."""
        statement = select(Categoria).where(Categoria.deleted_at == None)  # noqa: E711
        return list(self.session.exec(statement).all())

    def get_with_subcategorias(self, categoria_id: int) -> Optional[Categoria]:
        """Retorna una categoría por ID (no eliminada). Las subcategorías se cargan via relationship."""
        statement = (
            select(Categoria)
            .where(Categoria.id == categoria_id)
            .where(Categoria.deleted_at == None)  # noqa: E711
        )
        return self.session.exec(statement).first()

    def has_active_products(self, categoria_id: int) -> bool:
        """Verifica si existen productos activos asociados a esta categoría."""
        try:
            from app.modules.productos.model import Producto
            statement = (
                select(Producto)
                .where(Producto.categoria_id == categoria_id)
                .where(Producto.deleted_at == None)  # noqa: E711
            )
            result = self.session.exec(statement).first()
            return result is not None
        except Exception:
            return False

    def has_active_children(self, categoria_id: int) -> bool:
        """Verifica si existen subcategorías activas con este parent_id."""
        statement = (
            select(Categoria)
            .where(Categoria.parent_id == categoria_id)
            .where(Categoria.deleted_at == None)  # noqa: E711
        )
        result = self.session.exec(statement).first()
        return result is not None
