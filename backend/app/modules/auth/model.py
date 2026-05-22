"""Modelo SQLModel para RefreshToken con jti UUID como PK."""

import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class RefreshToken(SQLModel, table=True):
    """Almacena el jti de cada refresh token JWT emitido.

    jti (JWT ID) es el identificador único del token. Se persiste para
    permitir revocación inmediata y detección de replay attacks.
    """

    __tablename__ = "refresh_tokens"

    jti: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    usuario_id: int = Field(foreign_key="usuario.id", nullable=False, index=True)
    expires_at: datetime = Field(nullable=False, index=True)
    revoked_at: Optional[datetime] = Field(default=None, nullable=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
