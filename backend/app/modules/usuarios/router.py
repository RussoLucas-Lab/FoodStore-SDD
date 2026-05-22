"""Router de Usuario — endpoints REST para perfil propio bajo /api/v1/usuarios."""

from fastapi import APIRouter, Depends, status

from app.core.security import get_current_user
from app.core.uow import UnitOfWork
from app.modules.usuarios.model import Usuario
from app.modules.usuarios.schemas import (
    PasswordChangeRequest,
    UsuarioMeRead,
    UsuarioMeUpdate,
)
from app.modules.usuarios.service import usuario_service

router = APIRouter()


@router.get("/me", response_model=UsuarioMeRead)
def obtener_perfil(
    current_user: Usuario = Depends(get_current_user),
):
    """Retorna el perfil del usuario autenticado."""
    with UnitOfWork() as uow:
        return usuario_service.get_me(uow, current_user.id)  # type: ignore[arg-type]


@router.put("/me", response_model=UsuarioMeRead)
def actualizar_perfil(
    body: UsuarioMeUpdate,
    current_user: Usuario = Depends(get_current_user),
):
    """Actualiza nombre y/o apellido del usuario autenticado."""
    with UnitOfWork() as uow:
        return usuario_service.update_me(uow, current_user.id, body)  # type: ignore[arg-type]


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def cambiar_password(
    body: PasswordChangeRequest,
    current_user: Usuario = Depends(get_current_user),
):
    """Cambia la contraseña del usuario autenticado."""
    with UnitOfWork() as uow:
        usuario_service.change_password(uow, current_user.id, body)  # type: ignore[arg-type]
