"""Seguridad: JWT HS256, bcrypt, dependencias FastAPI."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Generator, List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# --- Contexto bcrypt (cost = 12) ---
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)

# --- Bearer token extractor ---
bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Contraseñas
# ---------------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """Hashea la contraseña con bcrypt (cost = 12). Nunca almacenar texto plano."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña en texto plano coincide con el hash almacenado."""
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT Tokens
# ---------------------------------------------------------------------------

def create_access_token(sub: str, rol: str) -> str:
    """Crea un JWT de acceso HS256 (exp 30 min).

    Claims: sub (user_id str), rol, type: "access", exp, iat.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": sub,
        "rol": rol,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(sub: str) -> tuple[str, str]:
    """Crea un JWT de refresh HS256 (exp 7 días).

    Returns:
        (token_jwt, jti_str) — el jti debe persistirse en refresh_tokens.

    Claims: sub, jti, type: "refresh", exp, iat.
    """
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": sub,
        "jti": jti,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti


def decode_token(token: str, expected_type: str) -> dict:
    """Decodifica y valida un JWT. Verifica firma, expiración y tipo.

    Raises:
        HTTPException 401 con code ACCESS_TOKEN_EXPIRED si el token expiró.
        HTTPException 401 con code INVALID_TOKEN si es inválido.
    """
    try:
        payload: dict = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Token expirado", "code": "ACCESS_TOKEN_EXPIRED"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Token inválido", "code": "INVALID_TOKEN"},
        )

    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Tipo de token incorrecto", "code": "INVALID_TOKEN"},
        )

    return payload


# ---------------------------------------------------------------------------
# Dependencias FastAPI
# ---------------------------------------------------------------------------

def get_uow() -> "Generator":
    """Dependencia FastAPI: provee un UnitOfWork para la duración del request."""
    from app.core.uow import UnitOfWork

    with UnitOfWork() as uow:
        yield uow


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    uow: "UnitOfWork" = Depends(get_uow),  # type: ignore[name-defined]
) -> "Usuario":  # type: ignore[name-defined]
    """Dependencia FastAPI: extrae JWT, valida y retorna el Usuario de BD.

    Raises:
        HTTPException 401: token ausente, inválido, expirado, o usuario inactivo.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "No autenticado", "code": "NOT_AUTHENTICATED"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials, "access")
    user_id_str: Optional[str] = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Token inválido: falta sub", "code": "INVALID_TOKEN"},
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Token inválido: sub no numérico", "code": "INVALID_TOKEN"},
        )

    usuario = uow.usuarios.get_by_id(user_id)
    if usuario is None or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Usuario no encontrado o inactivo", "code": "INVALID_TOKEN"},
        )

    # Cargar roles en memoria mientras la sesión está abierta
    _ = list(usuario.roles)

    return usuario


def require_role(allowed_roles: List[str]):
    """Fábrica de dependencias FastAPI: verifica que el usuario tenga el rol requerido.

    Valida el rol desde el claim JWT (sin consulta adicional a BD).

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role(["ADMIN"]))])
    """

    def _check_role(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
        current_user: "Usuario" = Depends(get_current_user),  # type: ignore[name-defined]
    ) -> "Usuario":  # type: ignore[name-defined]
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"detail": "No autenticado", "code": "NOT_AUTHENTICATED"},
            )
        payload = decode_token(credentials.credentials, "access")
        user_rol: str = payload.get("rol", "")
        if user_rol not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"detail": "Permisos insuficientes", "code": "FORBIDDEN"},
            )
        return current_user

    return _check_role
