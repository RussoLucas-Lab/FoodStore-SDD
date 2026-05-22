"""Servicio de lógica de negocio para Usuario (perfil propio)."""

from fastapi import HTTPException, status

from app.core.security import hash_password, verify_password
from app.modules.usuarios.schemas import (
    PasswordChangeRequest,
    UsuarioMeRead,
    UsuarioMeUpdate,
)


class UsuarioService:
    """Lógica de negocio stateless para el perfil del usuario. Nunca llama session.commit()."""

    def get_me(self, uow, user_id: int) -> UsuarioMeRead:
        """Retorna el perfil del usuario autenticado."""
        usuario = uow.usuarios.get_by_id(user_id)
        if usuario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "Usuario no encontrado.",
                    "code": "USUARIO_NOT_FOUND",
                },
            )
        return UsuarioMeRead.model_validate(usuario)

    def update_me(self, uow, user_id: int, body: UsuarioMeUpdate) -> UsuarioMeRead:
        """Actualiza nombre y/o apellido del usuario autenticado."""
        usuario = uow.usuarios.get_by_id(user_id)
        if usuario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "Usuario no encontrado.",
                    "code": "USUARIO_NOT_FOUND",
                },
            )

        if body.nombre is not None:
            usuario.nombre = body.nombre
        if body.apellido is not None:
            usuario.apellido = body.apellido

        updated = uow.usuarios.update(usuario)
        return UsuarioMeRead.model_validate(updated)

    def change_password(
        self, uow, user_id: int, body: PasswordChangeRequest
    ) -> None:
        """Cambia la contraseña del usuario autenticado.

        Valida:
        - password_actual coincide con el hash almacenado.
        - password_nuevo == password_nuevo_confirmar.
        - password_nuevo tiene mínimo 8 caracteres (validado en schema).
        """
        usuario = uow.usuarios.get_by_id(user_id)
        if usuario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "Usuario no encontrado.",
                    "code": "USUARIO_NOT_FOUND",
                },
            )

        if not verify_password(body.password_actual, usuario.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "detail": "La contraseña actual es incorrecta.",
                    "code": "PASSWORD_INCORRECTO",
                },
            )

        if body.password_nuevo != body.password_nuevo_confirmar:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "detail": "La nueva contraseña y la confirmación no coinciden.",
                    "code": "PASSWORD_CONFIRMACION_NO_COINCIDE",
                },
            )

        usuario.password_hash = hash_password(body.password_nuevo)
        uow.usuarios.update(usuario)


usuario_service = UsuarioService()
