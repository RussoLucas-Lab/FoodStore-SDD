"""Router de Ingrediente — endpoints REST bajo /api/v1/ingredientes."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.security import require_role
from app.core.uow import UnitOfWork
from app.modules.ingredientes.schemas import (
    IngredienteCreate,
    IngredienteRead,
    IngredienteUpdate,
    PaginatedIngredientes,
)
from app.modules.ingredientes.service import ingrediente_service

router = APIRouter()


@router.get("/", response_model=PaginatedIngredientes)
def listar_ingredientes(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    es_alergeno: Optional[bool] = Query(default=None),
):
    """Lista ingredientes con paginación. Filtro opcional: ?es_alergeno=true. Público."""
    with UnitOfWork() as uow:
        return ingrediente_service.list_all(uow, page, size, es_alergeno)


@router.get("/{ingrediente_id}", response_model=IngredienteRead)
def obtener_ingrediente(ingrediente_id: int):
    """Obtiene un ingrediente por ID. Público."""
    with UnitOfWork() as uow:
        return ingrediente_service.get_by_id(uow, ingrediente_id)


@router.post(
    "/",
    response_model=IngredienteRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def crear_ingrediente(body: IngredienteCreate):
    """Crea un nuevo ingrediente. Solo ADMIN."""
    with UnitOfWork() as uow:
        return ingrediente_service.create(uow, body)


@router.put(
    "/{ingrediente_id}",
    response_model=IngredienteRead,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def actualizar_ingrediente(ingrediente_id: int, body: IngredienteUpdate):
    """Actualiza un ingrediente existente. Solo ADMIN."""
    with UnitOfWork() as uow:
        return ingrediente_service.update(uow, ingrediente_id, body)


@router.delete(
    "/{ingrediente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def eliminar_ingrediente(ingrediente_id: int):
    """Elimina (soft delete) un ingrediente. Solo ADMIN."""
    with UnitOfWork() as uow:
        ingrediente_service.delete(uow, ingrediente_id)
