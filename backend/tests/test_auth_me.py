"""Tests de GET /api/v1/auth/me."""

import pytest
from fastapi.testclient import TestClient

from app.modules.usuarios.model import Usuario


def _login(client: TestClient, email: str, password: str) -> dict:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return resp.json()


class TestGetMe:
    URL = "/api/v1/auth/me"

    def test_me_con_token_valido(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        tokens = _login(client, "client@test.com", "Client1234!")

        resp = client.get(
            self.URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "client@test.com"
        assert data["rol"] == "CLIENT"
        assert "password_hash" not in data

    def test_me_sin_token_devuelve_401(self, client: TestClient) -> None:
        resp = client.get(self.URL)
        assert resp.status_code == 401

    def test_me_con_token_invalido_devuelve_401(self, client: TestClient) -> None:
        resp = client.get(
            self.URL,
            headers={"Authorization": "Bearer token.invalido.firma"},
        )
        assert resp.status_code == 401

    def test_me_admin_tiene_rol_admin(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        tokens = _login(client, "admin@test.com", "Admin1234!")
        resp = client.get(
            self.URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 200
        assert resp.json()["rol"] == "ADMIN"
