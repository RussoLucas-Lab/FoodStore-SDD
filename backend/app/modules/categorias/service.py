"""Servicio de lógica de negocio para Categoria."""

from typing import List, Optional

from fastapi import HTTPException, status

from app.modules.categorias.model import Categoria
from app.modules.categorias.schemas import (
    CategoriaCreate,
    CategoriaRead,
    CategoriaTreeRead,
    CategoriaUpdate,
)


def _build_tree(
    categorias: List[Categoria],
    parent_id: Optional[int] = None,
) -> List[CategoriaTreeRead]:
    """Construye el árbol recursivo a partir de la lista plana de categorías."""
    nodes = []
    for cat in categorias:
        if cat.parent_id == parent_id:
            node = CategoriaTreeRead(
                id=cat.id,  # type: ignore[arg-type]
                nombre=cat.nombre,
                parent_id=cat.parent_id,
                descripcion=cat.descripcion,
                orden=cat.orden,
                activa=cat.activa,
                subcategorias=_build_tree(categorias, parent_id=cat.id),
            )
            nodes.append(node)
    return sorted(nodes, key=lambda n: n.orden)


class CategoriaService:
    """Lógica de negocio stateless para Categoria. Nunca llama session.commit()."""

    def get_tree(self, uow) -> List[CategoriaTreeRead]:
        """Retorna el árbol completo de categorías activas."""
        todas = uow.categorias.get_all_active()
        return _build_tree(todas, parent_id=None)

    def get_by_id(self, uow, categoria_id: int) -> CategoriaRead:
        """Retorna una categoría por ID. 404 si no existe o está eliminada."""
        cat = uow.categorias.get_with_subcategorias(categoria_id)
        if cat is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": f"Categoría con id {categoria_id} no encontrada.",
                    "code": "CATEGORIA_NOT_FOUND",
                },
            )
        return CategoriaRead.model_validate(cat)

    def create(self, uow, body: CategoriaCreate) -> CategoriaRead:
        """Crea una nueva categoría. Valida que el parent exista si se indica."""
        if body.parent_id is not None:
            parent = uow.categorias.get_with_subcategorias(body.parent_id)
            if parent is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "detail": "La categoría padre indicada no existe o está eliminada.",
                        "code": "PARENT_CATEGORIA_NOT_FOUND",
                    },
                )

        nueva = Categoria(
            nombre=body.nombre,
            parent_id=body.parent_id,
            descripcion=body.descripcion,
            orden=body.orden,
        )
        created = uow.categorias.create(nueva)
        return CategoriaRead.model_validate(created)

    def update(self, uow, categoria_id: int, body: CategoriaUpdate) -> CategoriaRead:
        """Actualiza una categoría existente. 404 si no existe."""
        cat = uow.categorias.get_with_subcategorias(categoria_id)
        if cat is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": f"Categoría con id {categoria_id} no encontrada.",
                    "code": "CATEGORIA_NOT_FOUND",
                },
            )

        if body.parent_id is not None and body.parent_id != cat.parent_id:
            parent = uow.categorias.get_with_subcategorias(body.parent_id)
            if parent is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "detail": "La categoría padre indicada no existe o está eliminada.",
                        "code": "PARENT_CATEGORIA_NOT_FOUND",
                    },
                )
            # Evitar ciclo: el nuevo padre no puede ser un descendiente de la cat actual
            if body.parent_id == categoria_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "detail": "Una categoría no puede ser su propio padre.",
                        "code": "CATEGORIA_SELF_REFERENCE",
                    },
                )

        if body.nombre is not None:
            cat.nombre = body.nombre
        if body.parent_id is not None:
            cat.parent_id = body.parent_id
        if body.descripcion is not None:
            cat.descripcion = body.descripcion
        if body.orden is not None:
            cat.orden = body.orden
        if body.activa is not None:
            cat.activa = body.activa

        updated = uow.categorias.update(cat)
        return CategoriaRead.model_validate(updated)

    def delete(self, uow, categoria_id: int) -> None:
        """Elimina (soft delete) una categoría. Valida RN-CA03 y subcategorías activas."""
        cat = uow.categorias.get_with_subcategorias(categoria_id)
        if cat is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": f"Categoría con id {categoria_id} no encontrada.",
                    "code": "CATEGORIA_NOT_FOUND",
                },
            )

        # RN-CA03: No se puede eliminar una categoría que tiene productos activos
        if uow.categorias.has_active_products(categoria_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "detail": "No se puede eliminar una categoría con productos activos asociados.",
                    "code": "RN_CA03",
                },
            )

        # No se puede eliminar si tiene subcategorías activas
        if uow.categorias.has_active_children(categoria_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "detail": "No se puede eliminar una categoría con subcategorías activas.",
                    "code": "CATEGORIA_HAS_CHILDREN",
                },
            )

        uow.categorias.soft_delete(cat)


categoria_service = CategoriaService()
