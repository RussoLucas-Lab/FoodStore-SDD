"""Router de Direccion — endpoints REST bajo /api/v1/direcciones."""

from typing import List

from fastapi import APIRouter, Depends, status

from app.core.security import get_current_user
from app.core.uow import UnitOfWork
from app.modules.direcciones.schemas import (
    DireccionCreate,
    DireccionRead,
    DireccionSetPrincipalResponse,
    DireccionUpdate,
)
from app.modules.direcciones.service import direccion_service

router = APIRouter()


@router.get("/", response_model=List[DireccionRead])
def listar_direcciones(
    current_user=Depends(get_current_user),
):
    """Lista las direcciones activas del usuario autenticado (principal primero)."""
    with UnitOfWork() as uow:
        return direccion_service.listar_propias(uow, current_user.id)


@router.post(
    "/",
    response_model=DireccionRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_direccion(
    body: DireccionCreate,
    current_user=Depends(get_current_user),
):
    """Crea una nueva dirección. Primera dirección = principal automática (RN-DI01)."""
    with UnitOfWork() as uow:
        return direccion_service.crear(uow, current_user.id, body)


@router.put(
    "/{direccion_id}",
    response_model=DireccionRead,
)
def actualizar_direccion(
    direccion_id: int,
    body: DireccionUpdate,
    current_user=Depends(get_current_user),
):
    """Actualiza los campos de una dirección. No modifica es_principal."""
    with UnitOfWork() as uow:
        return direccion_service.actualizar(uow, current_user.id, direccion_id, body)


@router.patch(
    "/{direccion_id}/principal",
    response_model=DireccionSetPrincipalResponse,
)
def set_principal(
    direccion_id: int,
    current_user=Depends(get_current_user),
):
    """Cambia la dirección principal del usuario (RN-DI02). Idempotente."""
    with UnitOfWork() as uow:
        return direccion_service.set_principal(uow, current_user.id, direccion_id)


@router.delete(
    "/{direccion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def eliminar_direccion(
    direccion_id: int,
    current_user=Depends(get_current_user),
):
    """Soft delete de una dirección. No se puede eliminar la principal si hay otras."""
    with UnitOfWork() as uow:
        direccion_service.eliminar(uow, current_user.id, direccion_id)
