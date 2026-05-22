"""Router de autenticación — 5 endpoints bajo /auth."""

from fastapi import APIRouter, Depends, Request, status

from app.core.limiter import limiter
from app.core.security import get_current_user
from app.core.uow import UnitOfWork
from app.modules.auth import service as auth_service
from app.modules.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)
from app.modules.usuarios.model import Usuario

router = APIRouter()


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest) -> UserPublic:
    """Registra un nuevo usuario. Rol CLIENT asignado automáticamente."""
    with UnitOfWork() as uow:
        return auth_service.register(uow, body)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/15minutes")
def login(request: Request, body: LoginRequest) -> TokenResponse:
    """Autentica al usuario y emite tokens JWT. Rate limit: 5 intentos / 15 min."""
    with UnitOfWork() as uow:
        return auth_service.login(uow, body)


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def refresh(body: RefreshRequest) -> TokenResponse:
    """Rota el refresh token. Anti-replay: token ya revocado revoca todos."""
    with UnitOfWork() as uow:
        return auth_service.refresh(uow, body.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    body: LogoutRequest,
    _current_user: Usuario = Depends(get_current_user),
) -> None:
    """Revoca el refresh token enviado. Requiere access token válido."""
    with UnitOfWork() as uow:
        auth_service.logout(uow, body.refresh_token)


@router.get("/me", response_model=UserPublic, status_code=status.HTTP_200_OK)
def get_me(current_user: Usuario = Depends(get_current_user)) -> UserPublic:
    """Retorna los datos del usuario autenticado."""
    with UnitOfWork() as uow:
        return auth_service.get_me(uow, current_user.id)  # type: ignore[arg-type]
