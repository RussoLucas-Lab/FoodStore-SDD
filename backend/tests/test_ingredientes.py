"""Tests de integración para /api/v1/ingredientes."""

import pytest
from fastapi.testclient import TestClient

from app.modules.usuarios.model import Usuario


def _admin_headers(client: TestClient) -> dict:
    """Obtiene headers de autenticación para el usuario admin."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Admin1234!"},
    )
    assert resp.status_code == 200, f"Login fallido: {resp.json()}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestListarIngredientes:
    URL = "/api/v1/ingredientes/"

    def test_listar_vacio(self, client: TestClient) -> None:
        """GET / retorna lista vacía cuando no hay ingredientes."""
        resp = client.get(self.URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    def test_listar_con_items(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """GET / retorna ingredientes después de crearlos."""
        headers = _admin_headers(client)
        client.post(self.URL, json={"nombre": "Sal", "es_alergeno": False}, headers=headers)
        client.post(self.URL, json={"nombre": "Maní", "es_alergeno": True}, headers=headers)

        resp = client.get(self.URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_filtrar_solo_alergenos(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """GET /?es_alergeno=true retorna solo los alérgenos."""
        headers = _admin_headers(client)
        client.post(self.URL, json={"nombre": "Sal", "es_alergeno": False}, headers=headers)
        client.post(self.URL, json={"nombre": "Gluten", "es_alergeno": True}, headers=headers)
        client.post(self.URL, json={"nombre": "Maní", "es_alergeno": True}, headers=headers)

        resp = client.get(self.URL, params={"es_alergeno": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        for item in data["items"]:
            assert item["es_alergeno"] is True

    def test_filtrar_solo_no_alergenos(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """GET /?es_alergeno=false retorna solo los no alérgenos."""
        headers = _admin_headers(client)
        client.post(self.URL, json={"nombre": "Sal", "es_alergeno": False}, headers=headers)
        client.post(self.URL, json={"nombre": "Gluten", "es_alergeno": True}, headers=headers)

        resp = client.get(self.URL, params={"es_alergeno": False})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["nombre"] == "Sal"

    def test_paginacion(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """GET / respeta page y size."""
        headers = _admin_headers(client)
        for i in range(5):
            client.post(
                self.URL,
                json={"nombre": f"Ingrediente {i}", "es_alergeno": False},
                headers=headers,
            )

        resp = client.get(self.URL, params={"page": 1, "size": 3})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 3
        assert data["total"] == 5
        assert data["pages"] == 2


class TestCrearIngrediente:
    URL = "/api/v1/ingredientes/"

    def test_crear_ingrediente(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """POST / crea un ingrediente correctamente."""
        headers = _admin_headers(client)
        resp = client.post(
            self.URL,
            json={"nombre": "Azúcar", "es_alergeno": False},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["nombre"] == "Azúcar"
        assert data["es_alergeno"] is False
        assert data["id"] is not None

    def test_crear_alergeno(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """POST / crea un ingrediente alérgeno correctamente."""
        headers = _admin_headers(client)
        resp = client.post(
            self.URL,
            json={"nombre": "Nueces", "es_alergeno": True},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["es_alergeno"] is True

    def test_nombre_duplicado_409(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """POST / retorna 409 si el nombre ya existe."""
        headers = _admin_headers(client)
        client.post(
            self.URL, json={"nombre": "Pimienta"}, headers=headers
        )
        resp = client.post(
            self.URL, json={"nombre": "Pimienta"}, headers=headers
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "INGREDIENTE_DUPLICATE"

    def test_crear_sin_auth_401(self, client: TestClient) -> None:
        """POST / sin token retorna 401."""
        resp = client.post(self.URL, json={"nombre": "Sin auth"})
        assert resp.status_code == 401

    def test_crear_con_rol_cliente_403(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        """POST / con rol CLIENT retorna 403."""
        resp_login = client.post(
            "/api/v1/auth/login",
            json={"email": "client@test.com", "password": "Client1234!"},
        )
        token = resp_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(self.URL, json={"nombre": "Sin permiso"}, headers=headers)
        assert resp.status_code == 403


class TestObtenerIngrediente:
    URL = "/api/v1/ingredientes/"

    def test_obtener_por_id(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """GET /{id} retorna el ingrediente correcto."""
        headers = _admin_headers(client)
        created = client.post(
            self.URL, json={"nombre": "Aceite"}, headers=headers
        ).json()
        resp = client.get(f"{self.URL}{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "Aceite"

    def test_obtener_404(self, client: TestClient) -> None:
        """GET /{id} retorna 404 para ID inexistente."""
        resp = client.get(f"{self.URL}99999")
        assert resp.status_code == 404
        assert resp.json()["code"] == "INGREDIENTE_NOT_FOUND"


class TestActualizarIngrediente:
    URL = "/api/v1/ingredientes/"

    def test_actualizar_nombre(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """PUT /{id} actualiza el nombre correctamente."""
        headers = _admin_headers(client)
        created = client.post(
            self.URL, json={"nombre": "OldName"}, headers=headers
        ).json()
        resp = client.put(
            f"{self.URL}{created['id']}",
            json={"nombre": "NewName"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "NewName"

    def test_actualizar_es_alergeno(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """PUT /{id} actualiza es_alergeno correctamente."""
        headers = _admin_headers(client)
        created = client.post(
            self.URL, json={"nombre": "Leche", "es_alergeno": False}, headers=headers
        ).json()
        resp = client.put(
            f"{self.URL}{created['id']}",
            json={"es_alergeno": True},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["es_alergeno"] is True

    def test_actualizar_404(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """PUT /{id} retorna 404 para ID inexistente."""
        headers = _admin_headers(client)
        resp = client.put(
            f"{self.URL}99999",
            json={"nombre": "X"},
            headers=headers,
        )
        assert resp.status_code == 404
        assert resp.json()["code"] == "INGREDIENTE_NOT_FOUND"


class TestEliminarIngrediente:
    URL = "/api/v1/ingredientes/"

    def test_eliminar_ingrediente(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """DELETE /{id} elimina (soft delete) el ingrediente correctamente."""
        headers = _admin_headers(client)
        created = client.post(
            self.URL, json={"nombre": "Para eliminar"}, headers=headers
        ).json()
        resp = client.delete(f"{self.URL}{created['id']}", headers=headers)
        assert resp.status_code == 204

        # Ya no debe ser accesible por GET /{id}
        resp2 = client.get(f"{self.URL}{created['id']}")
        assert resp2.status_code == 404

    def test_eliminar_404(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """DELETE /{id} retorna 404 para ID inexistente."""
        headers = _admin_headers(client)
        resp = client.delete(f"{self.URL}99999", headers=headers)
        assert resp.status_code == 404
        assert resp.json()["code"] == "INGREDIENTE_NOT_FOUND"

    def test_eliminar_sin_auth_401(self, client: TestClient) -> None:
        """DELETE /{id} sin token retorna 401."""
        resp = client.delete(f"{self.URL}1")
        assert resp.status_code == 401

    def test_ingrediente_no_aparece_en_lista_tras_eliminar(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """Tras eliminación el ingrediente no aparece en GET /."""
        headers = _admin_headers(client)
        created = client.post(
            self.URL, json={"nombre": "Eliminar de lista"}, headers=headers
        ).json()
        client.delete(f"{self.URL}{created['id']}", headers=headers)

        lista = client.get(self.URL).json()
        ids = [item["id"] for item in lista["items"]]
        assert created["id"] not in ids
