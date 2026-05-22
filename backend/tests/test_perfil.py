"""Tests de integración para /api/v1/usuarios/me (perfil propio)."""

import pytest
from fastapi.testclient import TestClient

from app.modules.usuarios.model import Usuario


USUARIOS_URL = "/api/v1/usuarios"


def _admin_headers(client: TestClient) -> dict:
    """Obtiene headers de autenticación para el usuario admin."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Admin1234!"},
    )
    assert resp.status_code == 200, f"Login fallido: {resp.json()}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _client_headers(client: TestClient) -> dict:
    """Obtiene headers de autenticación para el usuario cliente."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "client@test.com", "password": "Client1234!"},
    )
    assert resp.status_code == 200, f"Login fallido: {resp.json()}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestGetMe:
    def test_get_me_autenticado(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """GET /me autenticado retorna 200 con UsuarioMeRead."""
        headers = _admin_headers(client)
        resp = client.get(f"{USUARIOS_URL}/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "admin@test.com"
        assert data["nombre"] == "Admin"
        assert data["apellido"] == "Test"
        assert data["activo"] is True
        assert "password_hash" not in data
        assert "id" in data
        assert "created_at" in data

    def test_get_me_sin_auth_401(self, client: TestClient) -> None:
        """GET /me sin token retorna 401."""
        resp = client.get(f"{USUARIOS_URL}/me")
        assert resp.status_code == 401

    def test_get_me_cliente(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        """GET /me con usuario CLIENT retorna sus propios datos."""
        headers = _client_headers(client)
        resp = client.get(f"{USUARIOS_URL}/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "client@test.com"
        assert data["nombre"] == "Client"


class TestUpdateMe:
    def test_actualizar_nombre_y_apellido(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """PUT /me actualiza nombre y apellido correctamente."""
        headers = _admin_headers(client)
        resp = client.put(
            f"{USUARIOS_URL}/me",
            json={"nombre": "NuevoNombre", "apellido": "NuevoApellido"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["nombre"] == "NuevoNombre"
        assert data["apellido"] == "NuevoApellido"

    def test_actualizar_solo_nombre(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """PUT /me actualiza solo nombre, apellido queda igual."""
        headers = _admin_headers(client)
        resp = client.put(
            f"{USUARIOS_URL}/me",
            json={"nombre": "SoloNombre"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["nombre"] == "SoloNombre"
        assert data["apellido"] == "Test"  # unchanged

    def test_actualizar_body_vacio_200(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """PUT /me con body vacío (campos null) retorna 200 sin cambios."""
        headers = _admin_headers(client)
        resp = client.put(
            f"{USUARIOS_URL}/me",
            json={},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["nombre"] == "Admin"  # no change
        assert data["apellido"] == "Test"  # no change

    def test_actualizar_sin_auth_401(self, client: TestClient) -> None:
        """PUT /me sin token retorna 401."""
        resp = client.put(
            f"{USUARIOS_URL}/me",
            json={"nombre": "Test"},
        )
        assert resp.status_code == 401


class TestChangePassword:
    def test_cambiar_password_exitoso(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """PATCH /me/password exitoso retorna 204."""
        headers = _admin_headers(client)
        resp = client.patch(
            f"{USUARIOS_URL}/me/password",
            json={
                "password_actual": "Admin1234!",
                "password_nuevo": "NuevoPass123!",
                "password_nuevo_confirmar": "NuevoPass123!",
            },
            headers=headers,
        )
        assert resp.status_code == 204

        # Verificar que se puede hacer login con la nueva contraseña
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@test.com", "password": "NuevoPass123!"},
        )
        assert login_resp.status_code == 200

    def test_cambiar_password_actual_incorrecta_400(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """PATCH /me/password con contraseña actual incorrecta retorna 400."""
        headers = _admin_headers(client)
        resp = client.patch(
            f"{USUARIOS_URL}/me/password",
            json={
                "password_actual": "ContraseñaIncorrecta!",
                "password_nuevo": "NuevoPass123!",
                "password_nuevo_confirmar": "NuevoPass123!",
            },
            headers=headers,
        )
        assert resp.status_code == 400
        assert resp.json()["code"] == "PASSWORD_INCORRECTO"

    def test_cambiar_password_confirmacion_no_coincide_422(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """PATCH /me/password con confirmación que no coincide retorna 422."""
        headers = _admin_headers(client)
        resp = client.patch(
            f"{USUARIOS_URL}/me/password",
            json={
                "password_actual": "Admin1234!",
                "password_nuevo": "NuevoPass123!",
                "password_nuevo_confirmar": "DistintaConfirmacion!",
            },
            headers=headers,
        )
        assert resp.status_code == 422

    def test_cambiar_password_nueva_muy_corta_422(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """PATCH /me/password con nueva contraseña < 8 caracteres retorna 422."""
        headers = _admin_headers(client)
        resp = client.patch(
            f"{USUARIOS_URL}/me/password",
            json={
                "password_actual": "Admin1234!",
                "password_nuevo": "corta",
                "password_nuevo_confirmar": "corta",
            },
            headers=headers,
        )
        assert resp.status_code == 422

    def test_cambiar_password_sin_auth_401(self, client: TestClient) -> None:
        """PATCH /me/password sin token retorna 401."""
        resp = client.patch(
            f"{USUARIOS_URL}/me/password",
            json={
                "password_actual": "Admin1234!",
                "password_nuevo": "NuevoPass123!",
                "password_nuevo_confirmar": "NuevoPass123!",
            },
        )
        assert resp.status_code == 401
