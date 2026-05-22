"""Router de Categoria — endpoints REST bajo /api/v1/categorias."""

from typing import List

from fastapi import APIRouter, Depends, status

from app.core.security import require_role
from app.core.uow import UnitOfWork
from app.modules.categorias.schemas import (
    CategoriaCreate,
    CategoriaRead,
    CategoriaTreeRead,
    CategoriaUpdate,
)
from app.modules.categorias.service import categoria_service

router = APIRouter()


@router.get("/", response_model=List[CategoriaTreeRead])
def listar_categorias():
    """Lista el árbol completo de categorías activas. Público."""
    with UnitOfWork() as uow:
        return categoria_service.get_tree(uow)


@router.get("/{categoria_id}", response_model=CategoriaRead)
def obtener_categoria(categoria_id: int):
    """Obtiene una categoría por ID. Público."""
    with UnitOfWork() as uow:
        return categoria_service.get_by_id(uow, categoria_id)


@router.post(
    "/",
    response_model=CategoriaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def crear_categoria(body: CategoriaCreate):
    """Crea una nueva categoría. Solo ADMIN."""
    with UnitOfWork() as uow:
        return categoria_service.create(uow, body)


@router.put(
    "/{categoria_id}",
    response_model=CategoriaRead,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def actualizar_categoria(categoria_id: int, body: CategoriaUpdate):
    """Actualiza una categoría existente. Solo ADMIN."""
    with UnitOfWork() as uow:
        return categoria_service.update(uow, categoria_id, body)


@router.delete(
    "/{categoria_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def eliminar_categoria(categoria_id: int):
    """Elimina (soft delete) una categoría. Solo ADMIN."""
    with UnitOfWork() as uow:
        categoria_service.delete(uow, categoria_id)
