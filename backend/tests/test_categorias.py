"""Tests de integración para /api/v1/categorias."""

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


class TestListarArbol:
    URL = "/api/v1/categorias/"

    def test_arbol_vacio(self, client: TestClient) -> None:
        """GET / retorna lista vacía cuando no hay categorías."""
        resp = client.get(self.URL)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_arbol_con_categorias_raiz(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """GET / retorna categorías raíz después de crearlas."""
        headers = _admin_headers(client)
        client.post(self.URL, json={"nombre": "Bebidas"}, headers=headers)
        client.post(self.URL, json={"nombre": "Alimentos"}, headers=headers)

        resp = client.get(self.URL)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        nombres = {c["nombre"] for c in data}
        assert "Bebidas" in nombres
        assert "Alimentos" in nombres

    def test_arbol_con_subcategorias(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """GET / retorna árbol con subcategorías anidadas."""
        headers = _admin_headers(client)
        raiz = client.post(self.URL, json={"nombre": "Lácteos"}, headers=headers).json()
        client.post(
            self.URL,
            json={"nombre": "Quesos", "parent_id": raiz["id"]},
            headers=headers,
        )

        resp = client.get(self.URL)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1  # Solo una raíz
        assert data[0]["nombre"] == "Lácteos"
        assert len(data[0]["subcategorias"]) == 1
        assert data[0]["subcategorias"][0]["nombre"] == "Quesos"


class TestCrearCategoria:
    URL = "/api/v1/categorias/"

    def test_crear_categoria_raiz(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """POST / crea una categoría raíz correctamente."""
        headers = _admin_headers(client)
        resp = client.post(
            self.URL,
            json={"nombre": "Verduras"},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["nombre"] == "Verduras"
        assert data["parent_id"] is None
        assert data["id"] is not None

    def test_crear_con_padre_valido(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """POST / crea subcategoría con parent_id válido."""
        headers = _admin_headers(client)
        padre = client.post(self.URL, json={"nombre": "Frutas"}, headers=headers).json()
        resp = client.post(
            self.URL,
            json={"nombre": "Cítricos", "parent_id": padre["id"]},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["parent_id"] == padre["id"]
        assert data["nombre"] == "Cítricos"

    def test_crear_con_padre_invalido_400(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """POST / retorna 400 si el parent_id no existe."""
        headers = _admin_headers(client)
        resp = client.post(
            self.URL,
            json={"nombre": "Sin padre", "parent_id": 99999},
            headers=headers,
        )
        assert resp.status_code == 400
        assert resp.json()["code"] == "PARENT_CATEGORIA_NOT_FOUND"

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


class TestObtenerCategoria:
    URL = "/api/v1/categorias/"

    def test_obtener_por_id(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """GET /{id} retorna la categoría correcta."""
        headers = _admin_headers(client)
        created = client.post(
            self.URL, json={"nombre": "Carnes"}, headers=headers
        ).json()
        resp = client.get(f"{self.URL}{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "Carnes"

    def test_obtener_404(self, client: TestClient) -> None:
        """GET /{id} retorna 404 para ID inexistente."""
        resp = client.get(f"{self.URL}99999")
        assert resp.status_code == 404
        assert resp.json()["code"] == "CATEGORIA_NOT_FOUND"


class TestActualizarCategoria:
    URL = "/api/v1/categorias/"

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
        assert resp.json()["code"] == "CATEGORIA_NOT_FOUND"


class TestEliminarCategoria:
    URL = "/api/v1/categorias/"

    def test_eliminar_categoria(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """DELETE /{id} elimina (soft delete) la categoría correctamente."""
        headers = _admin_headers(client)
        created = client.post(
            self.URL, json={"nombre": "Para eliminar"}, headers=headers
        ).json()
        resp = client.delete(f"{self.URL}{created['id']}", headers=headers)
        assert resp.status_code == 204

        # Ya no debe aparecer en la lista
        lista = client.get(self.URL).json()
        ids = [c["id"] for c in lista]
        assert created["id"] not in ids

    def test_eliminar_404(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """DELETE /{id} retorna 404 para ID inexistente."""
        headers = _admin_headers(client)
        resp = client.delete(f"{self.URL}99999", headers=headers)
        assert resp.status_code == 404
        assert resp.json()["code"] == "CATEGORIA_NOT_FOUND"

    def test_eliminar_con_hijos_activos_400(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """DELETE /{id} retorna 400 si tiene subcategorías activas (CATEGORIA_HAS_CHILDREN)."""
        headers = _admin_headers(client)
        padre = client.post(
            self.URL, json={"nombre": "Padre con hijos"}, headers=headers
        ).json()
        client.post(
            self.URL,
            json={"nombre": "Hijo activo", "parent_id": padre["id"]},
            headers=headers,
        )

        resp = client.delete(f"{self.URL}{padre['id']}", headers=headers)
        assert resp.status_code == 400
        assert resp.json()["code"] == "CATEGORIA_HAS_CHILDREN"
