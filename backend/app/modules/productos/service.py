"""Servicio de lógica de negocio para Producto."""

import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status

from app.modules.productos.model import Producto
from app.modules.productos.schemas import (
    DisponibilidadUpdate,
    ProductoCreate,
    ProductoListResponse,
    ProductoRead,
    ProductoUpdate,
    StockUpdate,
)
from app.modules.ingredientes.schemas import IngredienteRead


def _to_read(producto: Producto) -> ProductoRead:
    """Convierte un Producto ORM a ProductoRead, mapeando las relaciones junction."""
    categorias = []
    for pc in producto.categorias:
        if pc.categoria is not None:
            from app.modules.categorias.schemas import CategoriaRead
            categorias.append(CategoriaRead.model_validate(pc.categoria))

    ingredientes = []
    for pi in producto.ingredientes:
        if pi.ingrediente is not None:
            ingredientes.append(IngredienteRead.model_validate(pi.ingrediente))

    return ProductoRead(
        id=producto.id,  # type: ignore[arg-type]
        nombre=producto.nombre,
        descripcion=producto.descripcion,
        precio_base=producto.precio_base,
        stock_cantidad=producto.stock_cantidad,
        disponible=producto.disponible,
        imagen_url=producto.imagen_url,
        created_at=producto.created_at,
        deleted_at=producto.deleted_at,
        categorias=categorias,
        ingredientes=ingredientes,
    )


class ProductoService:
    """Lógica de negocio stateless para Producto. Nunca llama session.commit()."""

    def list_all(
        self,
        uow,
        page: int = 1,
        size: int = 20,
        categoria_id: Optional[int] = None,
        q: Optional[str] = None,
        excluir_alergenos: Optional[bool] = None,
        disponible: Optional[bool] = None,
        include_deleted: bool = False,
    ) -> ProductoListResponse:
        """Retorna listado paginado de productos con filtros opcionales."""
        items, total = uow.productos.list_filtered(
            page=page,
            size=size,
            categoria_id=categoria_id,
            q=q,
            excluir_alergenos=excluir_alergenos,
            disponible=disponible,
            include_deleted=include_deleted,
        )
        pages = math.ceil(total / size) if size > 0 else 0
        return ProductoListResponse(
            items=[_to_read(p) for p in items],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    def get_by_id(self, uow, id: int) -> ProductoRead:
        """Retorna un producto por ID. 404 si no existe o está eliminado."""
        producto = uow.productos.get_with_relations(id)
        if producto is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": f"Producto con id {id} no encontrado.",
                    "code": "PRODUCTO_NOT_FOUND",
                },
            )
        return _to_read(producto)

    def _validate_categoria_ids(self, uow, categoria_ids: List[int]) -> None:
        """Valida que todos los categoria_ids existan y estén activos."""
        for cat_id in categoria_ids:
            cat = uow.categorias.get_by_id(cat_id)
            if cat is None or cat.deleted_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "detail": f"Categoría con id {cat_id} no encontrada.",
                        "code": "CATEGORIA_NOT_FOUND",
                    },
                )

    def _validate_ingrediente_ids(self, uow, ingrediente_ids: List[int]) -> None:
        """Valida que todos los ingrediente_ids existan y estén activos."""
        for ing_id in ingrediente_ids:
            ing = uow.ingredientes.get_by_id(ing_id)
            if ing is None or ing.deleted_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "detail": f"Ingrediente con id {ing_id} no encontrado.",
                        "code": "INGREDIENTE_NOT_FOUND",
                    },
                )

    def create(self, uow, body: ProductoCreate) -> ProductoRead:
        """Crea un nuevo producto con sus relaciones."""
        self._validate_categoria_ids(uow, body.categoria_ids)
        self._validate_ingrediente_ids(uow, body.ingrediente_ids)

        nuevo = Producto(
            nombre=body.nombre,
            descripcion=body.descripcion,
            precio_base=body.precio_base,
            stock_cantidad=body.stock_cantidad,
            disponible=body.disponible,
            imagen_url=body.imagen_url,
        )
        created = uow.productos.create(nuevo)

        uow.productos.set_relaciones(
            producto_id=created.id,  # type: ignore[arg-type]
            categoria_ids=body.categoria_ids,
            ingrediente_ids=body.ingrediente_ids,
        )

        # Re-fetch with relations
        return self.get_by_id(uow, created.id)  # type: ignore[arg-type]

    def update(self, uow, id: int, body: ProductoUpdate) -> ProductoRead:
        """Actualiza un producto existente."""
        producto = uow.productos.get_with_relations(id)
        if producto is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": f"Producto con id {id} no encontrado.",
                    "code": "PRODUCTO_NOT_FOUND",
                },
            )

        if body.nombre is not None:
            producto.nombre = body.nombre
        if body.descripcion is not None:
            producto.descripcion = body.descripcion
        if body.precio_base is not None:
            producto.precio_base = body.precio_base
        if body.stock_cantidad is not None:
            if body.stock_cantidad < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "detail": "El stock no puede ser negativo.",
                        "code": "STOCK_NEGATIVO",
                    },
                )
            producto.stock_cantidad = body.stock_cantidad
        if body.disponible is not None:
            producto.disponible = body.disponible
        if body.imagen_url is not None:
            producto.imagen_url = body.imagen_url

        uow.productos.update(producto)

        if body.categoria_ids is not None:
            self._validate_categoria_ids(uow, body.categoria_ids)
            uow.productos.set_relaciones(
                producto_id=id,
                categoria_ids=body.categoria_ids,
                ingrediente_ids=[pi.ingrediente_id for pi in producto.ingredientes],
            )

        if body.ingrediente_ids is not None:
            self._validate_ingrediente_ids(uow, body.ingrediente_ids)
            # Reload current categoria_ids
            current_producto = uow.productos.get_with_relations(id)
            current_cat_ids = [pc.categoria_id for pc in (current_producto.categorias if current_producto else [])]
            uow.productos.set_relaciones(
                producto_id=id,
                categoria_ids=current_cat_ids,
                ingrediente_ids=body.ingrediente_ids,
            )

        return self.get_by_id(uow, id)

    def patch_disponibilidad(
        self, uow, id: int, body: DisponibilidadUpdate
    ) -> ProductoRead:
        """Actualiza solo la disponibilidad de un producto."""
        producto = uow.productos.get_with_relations(id)
        if producto is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": f"Producto con id {id} no encontrado.",
                    "code": "PRODUCTO_NOT_FOUND",
                },
            )
        producto.disponible = body.disponible
        uow.productos.update(producto)
        return self.get_by_id(uow, id)

    def patch_stock(self, uow, id: int, body: StockUpdate) -> ProductoRead:
        """Actualiza solo el stock de un producto."""
        producto = uow.productos.get_with_relations(id)
        if producto is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": f"Producto con id {id} no encontrado.",
                    "code": "PRODUCTO_NOT_FOUND",
                },
            )
        if body.cantidad < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "detail": "El stock no puede ser negativo.",
                    "code": "STOCK_NEGATIVO",
                },
            )
        producto.stock_cantidad = body.cantidad
        uow.productos.update(producto)
        return self.get_by_id(uow, id)

    def delete(self, uow, id: int) -> None:
        """Elimina (soft delete) un producto."""
        producto = uow.productos.get_with_relations(id)
        if producto is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": f"Producto con id {id} no encontrado.",
                    "code": "PRODUCTO_NOT_FOUND",
                },
            )
        uow.productos.soft_delete(producto)

    def get_ingredientes(self, uow, id: int) -> List[IngredienteRead]:
        """Retorna los ingredientes de un producto."""
        # First verify product exists
        producto = uow.productos.get_with_relations(id)
        if producto is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": f"Producto con id {id} no encontrado.",
                    "code": "PRODUCTO_NOT_FOUND",
                },
            )
        pivot_items = uow.productos.get_ingredientes(id)
        return [
            IngredienteRead.model_validate(pi.ingrediente)
            for pi in pivot_items
            if pi.ingrediente is not None
        ]


producto_service = ProductoService()
