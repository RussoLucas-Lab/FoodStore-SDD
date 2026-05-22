"""Tests de POST /api/v1/auth/refresh."""

import pytest
from fastapi.testclient import TestClient

from app.modules.usuarios.model import Usuario


def _login(client: TestClient, email: str, password: str) -> dict:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return resp.json()


class TestRefresh:
    URL = "/api/v1/auth/refresh"

    def test_refresh_exitoso_rota_token(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        tokens = _login(client, "client@test.com", "Client1234!")
        old_refresh = tokens["refresh_token"]

        resp = client.post(self.URL, json={"refresh_token": old_refresh})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # Token nuevo diferente al anterior
        assert data["refresh_token"] != old_refresh

    def test_refresh_revoca_token_anterior(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        tokens = _login(client, "client@test.com", "Client1234!")
        old_refresh = tokens["refresh_token"]

        # Primer refresh — exitoso
        client.post(self.URL, json={"refresh_token": old_refresh})

        # Segundo refresh con el mismo token — replay detectado
        resp = client.post(self.URL, json={"refresh_token": old_refresh})
        assert resp.status_code == 401
        assert resp.json()["code"] == "REPLAY_DETECTED"

    def test_token_invalido_devuelve_401(self, client: TestClient) -> None:
        resp = client.post(self.URL, json={"refresh_token": "token.invalido.firma"})
        assert resp.status_code == 401

    def test_replay_revoca_todos_los_tokens(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        # Login 2 veces → 2 refresh tokens
        tokens1 = _login(client, "client@test.com", "Client1234!")
        tokens2 = _login(client, "client@test.com", "Client1234!")

        old_refresh = tokens1["refresh_token"]

        # Usar tokens1 una vez
        new_tokens = client.post(self.URL, json={"refresh_token": old_refresh}).json()

        # Replay del tokens1 → revoca todos
        client.post(self.URL, json={"refresh_token": old_refresh})

        # tokens2 también debería estar revocado
        resp = client.post(self.URL, json={"refresh_token": tokens2["refresh_token"]})
        assert resp.status_code == 401
