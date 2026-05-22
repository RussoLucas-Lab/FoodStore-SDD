"""Tests de POST /api/v1/auth/login."""

import pytest
from fastapi.testclient import TestClient

from app.modules.usuarios.model import Usuario


class TestLogin:
    URL = "/api/v1/auth/login"

    def test_login_exitoso(self, client: TestClient, client_user: Usuario) -> None:
        resp = client.post(
            self.URL,
            json={"email": "client@test.com", "password": "Client1234!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800

    def test_email_inexistente_devuelve_401(self, client: TestClient) -> None:
        resp = client.post(
            self.URL,
            json={"email": "noexiste@test.com", "password": "cualquier"},
        )
        assert resp.status_code == 401
        assert resp.json()["code"] == "INVALID_CREDENTIALS"

    def test_password_incorrecto_devuelve_mismo_401(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        resp = client.post(
            self.URL,
            json={"email": "client@test.com", "password": "wrongpass"},
        )
        assert resp.status_code == 401
        # Mismo código — no diferencia email de password
        assert resp.json()["code"] == "INVALID_CREDENTIALS"

    def test_mismo_mensaje_email_vs_password_incorrecto(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        resp_no_email = client.post(
            self.URL,
            json={"email": "noexiste@test.com", "password": "cualquier"},
        )
        resp_mal_pass = client.post(
            self.URL,
            json={"email": "client@test.com", "password": "wrongpass"},
        )
        # Mismo detail y code
        assert resp_no_email.json()["code"] == resp_mal_pass.json()["code"]
        assert resp_no_email.json()["detail"] == resp_mal_pass.json()["detail"]
