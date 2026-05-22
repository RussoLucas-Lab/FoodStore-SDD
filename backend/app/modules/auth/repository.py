"""Repositorio de RefreshToken."""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import select

from app.core.repository import BaseRepository
from app.modules.auth.model import RefreshToken


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Operaciones de BD para RefreshToken."""

    def __init__(self, session) -> None:
        super().__init__(session, RefreshToken)

    def create_token(
        self,
        jti: str,
        usuario_id: int,
        expires_at: datetime,
    ) -> RefreshToken:
        """Persiste un nuevo jti de refresh token."""
        token = RefreshToken(
            jti=uuid.UUID(jti),
            usuario_id=usuario_id,
            expires_at=expires_at,
        )
        return self.create(token)

    def get_by_jti(self, jti: str) -> Optional[RefreshToken]:
        """Retorna el RefreshToken por jti, o None si no existe."""
        stmt = select(RefreshToken).where(RefreshToken.jti == uuid.UUID(jti))
        return self.session.exec(stmt).first()

    def revoke(self, jti: str) -> None:
        """Marca un token específico como revocado."""
        token = self.get_by_jti(jti)
        if token and token.revoked_at is None:
            token.revoked_at = datetime.now(timezone.utc)
            self.session.add(token)
            self.session.flush()

    def revoke_all_by_user(self, usuario_id: int) -> None:
        """Revoca todos los refresh tokens activos del usuario (anti-replay)."""
        stmt = select(RefreshToken).where(
            RefreshToken.usuario_id == usuario_id,
            RefreshToken.revoked_at.is_(None),  # type: ignore[union-attr]
        )
        tokens = self.session.exec(stmt).all()
        now = datetime.now(timezone.utc)
        for token in tokens:
            token.revoked_at = now
            self.session.add(token)
        self.session.flush()
