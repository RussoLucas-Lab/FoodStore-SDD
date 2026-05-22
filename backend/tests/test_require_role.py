"""Tests de la dependencia require_role."""

import pytest
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from app.core.security import require_role
from app.main import app
from app.modules.usuarios.model import Usuario


def _login(client: TestClient, email: str, password: str) -> dict:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return resp.json()


# Router temporal de prueba
_test_router = APIRouter(prefix="/test-role")


@_test_router.get("/admin-only", dependencies=[Depends(require_role(["ADMIN"]))])
def admin_only_endpoint():
    return {"ok": True}


app.include_router(_test_router)


class TestRequireRole:
    URL = "/test-role/admin-only"

    def test_admin_puede_acceder(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        tokens = _login(client, "admin@test.com", "Admin1234!")
        resp = client.get(
            self.URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 200

    def test_client_deniega_403(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        tokens = _login(client, "client@test.com", "Client1234!")
        resp = client.get(
            self.URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 403

    def test_sin_token_devuelve_401(self, client: TestClient) -> None:
        resp = client.get(self.URL)
        assert resp.status_code == 401
