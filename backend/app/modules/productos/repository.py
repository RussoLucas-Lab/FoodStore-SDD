"""Repositorio de Producto."""

from typing import List, Optional, Tuple

from sqlalchemy import func, select as sa_select
from sqlmodel import select

from app.core.repository import BaseRepository
from app.modules.productos.model import Producto, ProductoCategoria, ProductoIngrediente


class ProductoRepository(BaseRepository[Producto]):
    """Operaciones de BD para Producto."""

    def __init__(self, session) -> None:
        super().__init__(session, Producto)

    def get_with_relations(self, id: int) -> Optional[Producto]:
        """Retorna el producto por ID (no eliminado) cargando relaciones."""
        stmt = (
            select(Producto)
            .where(Producto.id == id)
            .where(Producto.deleted_at == None)  # noqa: E711
        )
        producto = self.session.exec(stmt).first()
        if producto is not None:
            # Eager load relationships
            _ = list(producto.categorias)
            for pc in producto.categorias:
                _ = pc.categoria
            _ = list(producto.ingredientes)
            for pi in producto.ingredientes:
                _ = pi.ingrediente
        return producto

    def list_filtered(
        self,
        page: int = 1,
        size: int = 20,
        categoria_id: Optional[int] = None,
        q: Optional[str] = None,
        excluir_alergenos: Optional[bool] = None,
        disponible: Optional[bool] = None,
        include_deleted: bool = False,
    ) -> Tuple[List[Producto], int]:
        """Retorna una tupla (items, total) con filtros opcionales."""
        if include_deleted:
            base_stmt = select(Producto)
            count_base = sa_select(func.count()).select_from(Producto)
        else:
            base_stmt = select(Producto).where(Producto.deleted_at == None)  # noqa: E711
            count_base = sa_select(func.count()).select_from(Producto).where(
                Producto.deleted_at == None  # noqa: E711
            )

        if disponible is not None:
            base_stmt = base_stmt.where(Producto.disponible == disponible)
            count_base = count_base.where(Producto.disponible == disponible)

        if q:
            pattern = f"%{q}%"
            from sqlalchemy import or_
            base_stmt = base_stmt.where(
                or_(
                    Producto.nombre.ilike(pattern),
                    Producto.descripcion.ilike(pattern),
                )
            )
            count_base = count_base.where(
                or_(
                    Producto.nombre.ilike(pattern),
                    Producto.descripcion.ilike(pattern),
                )
            )

        if categoria_id is not None:
            base_stmt = base_stmt.join(
                ProductoCategoria,
                ProductoCategoria.producto_id == Producto.id,
            ).where(ProductoCategoria.categoria_id == categoria_id)
            count_base = count_base.join(
                ProductoCategoria,
                ProductoCategoria.producto_id == Producto.id,
            ).where(ProductoCategoria.categoria_id == categoria_id)

        if excluir_alergenos:
            from app.modules.ingredientes.model import Ingrediente

            # Exclude products that have at least one alergeno ingrediente
            alergeno_subquery = (
                sa_select(ProductoIngrediente.producto_id)
                .join(
                    Ingrediente,
                    Ingrediente.id == ProductoIngrediente.ingrediente_id,
                )
                .where(Ingrediente.es_alergeno == True)  # noqa: E712
            )
            from sqlalchemy import not_
            base_stmt = base_stmt.where(
                Producto.id.not_in(alergeno_subquery)
            )
            count_base = count_base.where(
                Producto.id.not_in(alergeno_subquery)
            )

        total_result = self.session.execute(count_base)  # type: ignore[arg-type]
        total: int = total_result.scalar_one()

        skip = (page - 1) * size
        items = list(self.session.exec(base_stmt.offset(skip).limit(size)).all())

        # Eager load relations for each product
        for producto in items:
            _ = list(producto.categorias)
            for pc in producto.categorias:
                _ = pc.categoria
            _ = list(producto.ingredientes)
            for pi in producto.ingredientes:
                _ = pi.ingrediente

        return items, total

    def set_relaciones(
        self,
        producto_id: int,
        categoria_ids: List[int],
        ingrediente_ids: List[int],
    ) -> None:
        """Reemplaza las relaciones de categorías e ingredientes del producto."""
        # Delete existing
        existing_cats = self.session.exec(
            select(ProductoCategoria).where(
                ProductoCategoria.producto_id == producto_id
            )
        ).all()
        for pc in existing_cats:
            self.session.delete(pc)

        existing_ings = self.session.exec(
            select(ProductoIngrediente).where(
                ProductoIngrediente.producto_id == producto_id
            )
        ).all()
        for pi in existing_ings:
            self.session.delete(pi)

        self.session.flush()

        # Insert new
        for cat_id in categoria_ids:
            self.session.add(
                ProductoCategoria(producto_id=producto_id, categoria_id=cat_id)
            )

        for ing_id in ingrediente_ids:
            self.session.add(
                ProductoIngrediente(
                    producto_id=producto_id,
                    ingrediente_id=ing_id,
                    es_removible=False,
                )
            )

        self.session.flush()

    def get_ingredientes(self, id: int) -> List[ProductoIngrediente]:
        """Retorna todos los ProductoIngrediente de un producto."""
        stmt = select(ProductoIngrediente).where(
            ProductoIngrediente.producto_id == id
        )
        items = list(self.session.exec(stmt).all())
        for pi in items:
            _ = pi.ingrediente
        return items

    def lock_productos(self, producto_ids: List[int]) -> List[Producto]:
        """Adquiere lock pesimista sobre los productos ordenados por id (evita deadlocks).

        En SQLite el FOR UPDATE es no-op; en PostgreSQL bloquea las filas.
        Filtra deleted_at IS NULL — productos eliminados no aparecen.
        """
        sorted_ids = sorted(set(producto_ids))
        stmt = (
            select(Producto)
            .where(Producto.id.in_(sorted_ids))
            .where(Producto.deleted_at == None)  # noqa: E711
            .order_by(Producto.id.asc())
            .with_for_update()
        )
        return list(self.session.exec(stmt).all())

    def decrement_stock(self, producto_id: int, cantidad: int) -> Producto:
        """Decrementa el stock de un producto. Lanza ValueError si queda negativo.

        Debe ejecutarse dentro de un UoW para garantizar atomicidad.
        """
        producto = self.session.get(Producto, producto_id)
        if producto is None:
            raise ValueError(f"Producto {producto_id} no encontrado")

        nuevo_stock = producto.stock_cantidad - cantidad
        if nuevo_stock < 0:
            raise ValueError(
                f"Stock insuficiente para producto {producto_id}: "
                f"tiene {producto.stock_cantidad}, se necesitan {cantidad}"
            )

        producto.stock_cantidad = nuevo_stock
        self.session.add(producto)
        self.session.flush()
        self.session.refresh(producto)
        return producto

    def increment_stock(self, producto_id: int, cantidad: int) -> Producto:
        """Incrementa el stock de un producto (restauración al cancelar desde CONFIRMADO).

        Debe ejecutarse dentro de un UoW para garantizar atomicidad.
        """
        producto = self.session.get(Producto, producto_id)
        if producto is None:
            raise ValueError(f"Producto {producto_id} no encontrado")

        producto.stock_cantidad += cantidad
        self.session.add(producto)
        self.session.flush()
        self.session.refresh(producto)
        return producto
