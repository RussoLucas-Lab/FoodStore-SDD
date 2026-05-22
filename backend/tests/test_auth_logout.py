"""Tests de POST /api/v1/auth/logout."""

import pytest
from fastapi.testclient import TestClient

from app.modules.usuarios.model import Usuario


def _login(client: TestClient, email: str, password: str) -> dict:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return resp.json()


class TestLogout:
    URL = "/api/v1/auth/logout"

    def test_logout_revoca_refresh(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        tokens = _login(client, "client@test.com", "Client1234!")

        resp = client.post(
            self.URL,
            json={"refresh_token": tokens["refresh_token"]},
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 204

        # Intento de refresh con el token revocado
        resp2 = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp2.status_code == 401

    def test_logout_sin_auth_devuelve_401(self, client: TestClient) -> None:
        resp = client.post(
            self.URL,
            json={"refresh_token": "cualquier-token"},
        )
        assert resp.status_code == 401
