"""Servicio de autenticación — lógica de negocio stateless."""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.modules.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)
from app.modules.roles.model import UsuarioRol
from app.modules.usuarios.model import Usuario

# Nunca hace session.commit() — todo via UoW.


def _to_user_public(usuario: Usuario) -> UserPublic:
    """Convierte un modelo Usuario al schema público."""
    roles = [ur.rol_codigo for ur in usuario.roles]
    rol = roles[0] if roles else "CLIENT"
    return UserPublic(
        id=usuario.id,  # type: ignore[arg-type]
        email=usuario.email,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        rol=rol,
        fecha_alta=usuario.created_at,
    )


def register(uow: object, body: RegisterRequest) -> UserPublic:
    """Registra un nuevo usuario con rol CLIENT forzado.

    Raises:
        HTTPException 409: email ya registrado.
    """
    existing = uow.usuarios.get_by_email(body.email)  # type: ignore[attr-defined]
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "detail": "El email ya está registrado",
                "code": "EMAIL_ALREADY_EXISTS",
                "field": "email",
            },
        )

    usuario = Usuario(
        nombre=body.nombre,
        apellido=body.apellido,
        email=body.email,
        password_hash=hash_password(body.password),
        activo=True,
    )
    usuario = uow.usuarios.create(usuario)  # type: ignore[attr-defined]

    # Asignar rol CLIENT — nunca viene del request
    usuario_rol = UsuarioRol(usuario_id=usuario.id, rol_codigo="CLIENT")
    uow.session.add(usuario_rol)  # type: ignore[attr-defined]
    uow.flush()  # type: ignore[attr-defined]
    uow.session.refresh(usuario)  # type: ignore[attr-defined]

    return _to_user_public(usuario)


def login(uow: object, body: LoginRequest) -> TokenResponse:
    """Autentica un usuario y emite par de tokens JWT.

    No diferencia "email inexistente" de "password incorrecto" (D-4).
    """
    usuario = uow.usuarios.get_by_email(body.email)  # type: ignore[attr-defined]

    if usuario is None or not verify_password(body.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "detail": "Credenciales inválidas",
                "code": "INVALID_CREDENTIALS",
            },
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "detail": "Cuenta desactivada",
                "code": "ACCOUNT_DISABLED",
            },
        )

    roles = [ur.rol_codigo for ur in usuario.roles]
    rol = roles[0] if roles else "CLIENT"

    access_token = create_access_token(sub=str(usuario.id), rol=rol)
    refresh_token, jti = create_refresh_token(sub=str(usuario.id))

    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    uow.refresh_tokens.create_token(  # type: ignore[attr-defined]
        jti=jti,
        usuario_id=usuario.id,
        expires_at=expires_at,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


def refresh(uow: object, refresh_token: str) -> TokenResponse:
    """Rota un refresh token. Si llega uno revocado, revoca todos (anti-replay).

    Raises:
        HTTPException 401: token inválido, expirado o revocado (replay).
    """
    payload = decode_token(refresh_token, "refresh")
    jti: str = payload.get("jti", "")
    sub: str = payload.get("sub", "")

    stored = uow.refresh_tokens.get_by_jti(jti)  # type: ignore[attr-defined]
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Refresh token no encontrado", "code": "INVALID_TOKEN"},
        )

    if stored.revoked_at is not None:
        # Replay attack — revocar todos los tokens del usuario
        uow.refresh_tokens.revoke_all_by_user(stored.usuario_id)  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Token ya utilizado, sesión revocada", "code": "REPLAY_DETECTED"},
        )

    # SQLite devuelve datetimes sin timezone — normalizamos para comparar
    expires_at = stored.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Refresh token expirado", "code": "ACCESS_TOKEN_EXPIRED"},
        )

    # Rotar: revocar el actual y emitir uno nuevo
    uow.refresh_tokens.revoke(jti)  # type: ignore[attr-defined]

    usuario = uow.usuarios.get_by_id(int(sub))  # type: ignore[attr-defined]
    if usuario is None or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Usuario no encontrado", "code": "INVALID_TOKEN"},
        )

    roles = [ur.rol_codigo for ur in usuario.roles]
    rol = roles[0] if roles else "CLIENT"

    new_access = create_access_token(sub=sub, rol=rol)
    new_refresh, new_jti = create_refresh_token(sub=sub)

    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    uow.refresh_tokens.create_token(  # type: ignore[attr-defined]
        jti=new_jti,
        usuario_id=usuario.id,
        expires_at=expires_at,
    )

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


def logout(uow: object, refresh_token: str) -> None:
    """Revoca el refresh token enviado (logout de este dispositivo)."""
    try:
        payload = decode_token(refresh_token, "refresh")
        jti = payload.get("jti", "")
        uow.refresh_tokens.revoke(jti)  # type: ignore[attr-defined]
    except HTTPException:
        # Si el token ya expiró o es inválido, igual consideramos logout exitoso
        pass


def get_me(uow: object, usuario_id: int) -> UserPublic:
    """Retorna los datos públicos del usuario autenticado."""
    usuario = uow.usuarios.get_by_id(usuario_id)  # type: ignore[attr-defined]
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Usuario no encontrado", "code": "NOT_FOUND"},
        )
    return _to_user_public(usuario)
