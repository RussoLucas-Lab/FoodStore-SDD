"""Tests de POST /api/v1/auth/register."""

import pytest
from fastapi.testclient import TestClient

from app.modules.usuarios.model import Usuario


class TestRegister:
    URL = "/api/v1/auth/register"

    def test_registro_exitoso(self, client: TestClient) -> None:
        resp = client.post(
            self.URL,
            json={
                "email": "nuevo@test.com",
                "password": "Segura123!",
                "nombre": "Juan",
                "apellido": "Pérez",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "nuevo@test.com"
        assert data["rol"] == "CLIENT"
        assert "password" not in data
        assert "password_hash" not in data

    def test_email_duplicado_devuelve_409(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        resp = client.post(
            self.URL,
            json={
                "email": "client@test.com",
                "password": "OtraPass1!",
                "nombre": "Otro",
                "apellido": "Usuario",
            },
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "EMAIL_ALREADY_EXISTS"
        assert resp.json()["field"] == "email"

    def test_password_debil_devuelve_error(self, client: TestClient) -> None:
        resp = client.post(
            self.URL,
            json={
                "email": "otro@test.com",
                "password": "123",
                "nombre": "Juan",
                "apellido": "Pérez",
            },
        )
        assert resp.status_code == 422

    def test_no_puede_escalar_rol(self, client: TestClient) -> None:
        resp = client.post(
            self.URL,
            json={
                "email": "hacker@test.com",
                "password": "HackPass1!",
                "nombre": "Hacker",
                "apellido": "Test",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["rol"] == "CLIENT"
