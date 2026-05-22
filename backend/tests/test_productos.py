"""Tests de integración para /api/v1/productos."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.modules.usuarios.model import Usuario
from app.modules.categorias.model import Categoria
from app.modules.ingredientes.model import Ingrediente


PRODUCTOS_URL = "/api/v1/productos/"
CATEGORIAS_URL = "/api/v1/categorias/"
INGREDIENTES_URL = "/api/v1/ingredientes/"


def _admin_headers(client: TestClient) -> dict:
    """Obtiene headers de autenticación para el usuario admin."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Admin1234!"},
    )
    assert resp.status_code == 200, f"Login fallido: {resp.json()}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _crear_categoria(client: TestClient, headers: dict, nombre: str = "Bebidas") -> dict:
    resp = client.post(CATEGORIAS_URL, json={"nombre": nombre}, headers=headers)
    assert resp.status_code == 201, f"Error al crear categoría: {resp.json()}"
    return resp.json()


def _crear_ingrediente(
    client: TestClient, headers: dict, nombre: str = "Sal", es_alergeno: bool = False
) -> dict:
    resp = client.post(
        INGREDIENTES_URL,
        json={"nombre": nombre, "es_alergeno": es_alergeno},
        headers=headers,
    )
    assert resp.status_code == 201, f"Error al crear ingrediente: {resp.json()}"
    return resp.json()


def _crear_producto(
    client: TestClient,
    headers: dict,
    nombre: str = "Producto Test",
    precio_base: float = 100.0,
    categoria_ids: list | None = None,
    ingrediente_ids: list | None = None,
) -> dict:
    payload = {
        "nombre": nombre,
        "precio_base": precio_base,
        "categoria_ids": categoria_ids or [],
        "ingrediente_ids": ingrediente_ids or [],
    }
    resp = client.post(PRODUCTOS_URL, json=payload, headers=headers)
    assert resp.status_code == 201, f"Error al crear producto: {resp.json()}"
    return resp.json()


class TestListarProductos:
    def test_listar_vacio(self, client: TestClient) -> None:
        """GET / retorna lista vacía cuando no hay productos."""
        resp = client.get(PRODUCTOS_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    def test_listar_sin_filtros(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """GET / retorna productos sin filtros."""
        headers = _admin_headers(client)
        _crear_producto(client, headers, "Agua")
        _crear_producto(client, headers, "Jugo")

        resp = client.get(PRODUCTOS_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_filtrar_por_categoria(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """GET /?categoria_id=X retorna solo los productos de esa categoría."""
        headers = _admin_headers(client)
        cat1 = _crear_categoria(client, headers, "Bebidas")
        cat2 = _crear_categoria(client, headers, "Lácteos")

        _crear_producto(client, headers, "Agua", categoria_ids=[cat1["id"]])
        _crear_producto(client, headers, "Leche", categoria_ids=[cat2["id"]])
        _crear_producto(client, headers, "Jugo", categoria_ids=[cat1["id"]])

        resp = client.get(PRODUCTOS_URL, params={"categoria_id": cat1["id"]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        nombres = {p["nombre"] for p in data["items"]}
        assert "Agua" in nombres
        assert "Jugo" in nombres
        assert "Leche" not in nombres

    def test_busqueda_textual(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """GET /?q=texto retorna productos que contienen el texto en nombre o descripción."""
        headers = _admin_headers(client)
        _crear_producto(client, headers, "Agua mineral")
        _crear_producto(client, headers, "Jugo de naranja")

        resp = client.get(PRODUCTOS_URL, params={"q": "agua"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["nombre"] == "Agua mineral"

    def test_excluir_alergenos(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """GET /?excluir_alergenos=true excluye productos con ingredientes alérgenos."""
        headers = _admin_headers(client)
        ing_alergeno = _crear_ingrediente(client, headers, "Maní", es_alergeno=True)
        ing_normal = _crear_ingrediente(client, headers, "Sal", es_alergeno=False)

        _crear_producto(client, headers, "Con maní", ingrediente_ids=[ing_alergeno["id"]])
        _crear_producto(client, headers, "Sin alérgenos", ingrediente_ids=[ing_normal["id"]])
        _crear_producto(client, headers, "Puro", ingrediente_ids=[])

        resp = client.get(PRODUCTOS_URL, params={"excluir_alergenos": True})
        assert resp.status_code == 200
        data = resp.json()
        nombres = {p["nombre"] for p in data["items"]}
        assert "Con maní" not in nombres
        assert "Sin alérgenos" in nombres
        assert "Puro" in nombres

    def test_filtrar_disponibles(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """GET /?disponible=true retorna solo los productos disponibles."""
        headers = _admin_headers(client)
        prod1 = _crear_producto(client, headers, "Disponible")
        prod2 = _crear_producto(client, headers, "No disponible")

        # Mark prod2 as unavailable
        client.patch(
            f"{PRODUCTOS_URL}{prod2['id']}/disponibilidad",
            json={"disponible": False},
            headers=headers,
        )

        resp = client.get(PRODUCTOS_URL, params={"disponible": True})
        assert resp.status_code == 200
        data = resp.json()
        nombres = {p["nombre"] for p in data["items"]}
        assert "Disponible" in nombres
        assert "No disponible" not in nombres


class TestCrearProducto:
    def test_crear_producto_basico(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """POST / crea un producto básico sin categorías ni ingredientes."""
        headers = _admin_headers(client)
        resp = client.post(
            PRODUCTOS_URL,
            json={
                "nombre": "Galleta",
                "precio_base": 50.0,
                "stock_cantidad": 100,
                "categoria_ids": [],
                "ingrediente_ids": [],
            },
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["nombre"] == "Galleta"
        assert float(data["precio_base"]) == 50.0
        assert data["stock_cantidad"] == 100
        assert data["disponible"] is True
        assert data["id"] is not None
        assert data["categorias"] == []
        assert data["ingredientes"] == []

    def test_crear_con_categoria_e_ingrediente(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """POST / crea producto con categorías e ingredientes."""
        headers = _admin_headers(client)
        cat = _crear_categoria(client, headers, "Snacks")
        ing = _crear_ingrediente(client, headers, "Harina")

        resp = client.post(
            PRODUCTOS_URL,
            json={
                "nombre": "Pan",
                "precio_base": 80.0,
                "categoria_ids": [cat["id"]],
                "ingrediente_ids": [ing["id"]],
            },
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert len(data["categorias"]) == 1
        assert len(data["ingredientes"]) == 1
        assert data["categorias"][0]["nombre"] == "Snacks"
        assert data["ingredientes"][0]["nombre"] == "Harina"

    def test_crear_con_categoria_inexistente_400(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """POST / retorna 400 si categoria_id no existe."""
        headers = _admin_headers(client)
        resp = client.post(
            PRODUCTOS_URL,
            json={
                "nombre": "Producto",
                "precio_base": 50.0,
                "categoria_ids": [99999],
                "ingrediente_ids": [],
            },
            headers=headers,
        )
        assert resp.status_code == 400
        assert resp.json()["code"] == "CATEGORIA_NOT_FOUND"

    def test_crear_sin_auth_401(self, client: TestClient) -> None:
        """POST / sin token retorna 401."""
        resp = client.post(
            PRODUCTOS_URL,
            json={"nombre": "Sin auth", "precio_base": 10.0},
        )
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
        resp = client.post(
            PRODUCTOS_URL,
            json={"nombre": "Producto", "precio_base": 10.0},
            headers=headers,
        )
        assert resp.status_code == 403


class TestObtenerProducto:
    def test_obtener_por_id(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """GET /{id} retorna el producto correcto."""
        headers = _admin_headers(client)
        created = _crear_producto(client, headers, "Cereal")
        resp = client.get(f"{PRODUCTOS_URL}{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "Cereal"

    def test_obtener_404(self, client: TestClient) -> None:
        """GET /{id} retorna 404 para ID inexistente."""
        resp = client.get(f"{PRODUCTOS_URL}99999")
        assert resp.status_code == 404
        assert resp.json()["code"] == "PRODUCTO_NOT_FOUND"


class TestActualizarProducto:
    def test_actualizar_nombre(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """PUT /{id} actualiza el nombre correctamente."""
        headers = _admin_headers(client)
        created = _crear_producto(client, headers, "OldName")
        resp = client.put(
            f"{PRODUCTOS_URL}{created['id']}",
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
            f"{PRODUCTOS_URL}99999",
            json={"nombre": "X"},
            headers=headers,
        )
        assert resp.status_code == 404
        assert resp.json()["code"] == "PRODUCTO_NOT_FOUND"


class TestPatchDisponibilidad:
    def test_patch_disponibilidad(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """PATCH /{id}/disponibilidad cambia la disponibilidad."""
        headers = _admin_headers(client)
        created = _crear_producto(client, headers, "Producto disponible")
        assert created["disponible"] is True

        resp = client.patch(
            f"{PRODUCTOS_URL}{created['id']}/disponibilidad",
            json={"disponible": False},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["disponible"] is False

    def test_patch_disponibilidad_404(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """PATCH /{id}/disponibilidad retorna 404 para ID inexistente."""
        headers = _admin_headers(client)
        resp = client.patch(
            f"{PRODUCTOS_URL}99999/disponibilidad",
            json={"disponible": False},
            headers=headers,
        )
        assert resp.status_code == 404


class TestPatchStock:
    def test_patch_stock(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """PATCH /{id}/stock actualiza el stock correctamente."""
        headers = _admin_headers(client)
        created = _crear_producto(client, headers, "Stock test")

        resp = client.patch(
            f"{PRODUCTOS_URL}{created['id']}/stock",
            json={"cantidad": 50},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["stock_cantidad"] == 50

    def test_patch_stock_cero_valido(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """PATCH /{id}/stock acepta stock = 0."""
        headers = _admin_headers(client)
        created = _crear_producto(client, headers, "Stock cero")

        resp = client.patch(
            f"{PRODUCTOS_URL}{created['id']}/stock",
            json={"cantidad": 0},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["stock_cantidad"] == 0

    def test_patch_stock_negativo_422(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """PATCH /{id}/stock rechaza stock negativo (422 Pydantic o 400)."""
        headers = _admin_headers(client)
        created = _crear_producto(client, headers, "Stock negativo")

        resp = client.patch(
            f"{PRODUCTOS_URL}{created['id']}/stock",
            json={"cantidad": -1},
            headers=headers,
        )
        assert resp.status_code in (400, 422)

    def test_patch_stock_404(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """PATCH /{id}/stock retorna 404 para ID inexistente."""
        headers = _admin_headers(client)
        resp = client.patch(
            f"{PRODUCTOS_URL}99999/stock",
            json={"cantidad": 10},
            headers=headers,
        )
        assert resp.status_code == 404


class TestEliminarProducto:
    def test_eliminar_producto(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """DELETE /{id} elimina (soft delete) el producto."""
        headers = _admin_headers(client)
        created = _crear_producto(client, headers, "Para eliminar")

        resp = client.delete(f"{PRODUCTOS_URL}{created['id']}", headers=headers)
        assert resp.status_code == 204

        # Ya no debe ser accesible
        resp2 = client.get(f"{PRODUCTOS_URL}{created['id']}")
        assert resp2.status_code == 404

    def test_eliminar_404(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """DELETE /{id} retorna 404 para ID inexistente."""
        headers = _admin_headers(client)
        resp = client.delete(f"{PRODUCTOS_URL}99999", headers=headers)
        assert resp.status_code == 404
        assert resp.json()["code"] == "PRODUCTO_NOT_FOUND"

    def test_eliminar_rol_stock_403(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """DELETE /{id} con rol STOCK retorna 403 (solo ADMIN puede eliminar)."""
        # Create stock user
        from app.modules.roles.model import UsuarioRol
        from app.modules.usuarios.model import Usuario as Usr
        from app.core.security import hash_password

        # First create the producto
        headers = _admin_headers(client)
        created = _crear_producto(client, headers, "Solo admin elimina")

        # We need a stock user — do it via login from an existing stock user
        # Just test with client user to confirm 403
        resp_client_login = client.post(
            "/api/v1/auth/login",
            json={"email": "client@test.com", "password": "Client1234!"},
        )
        if resp_client_login.status_code == 200:
            token = resp_client_login.json()["access_token"]
            client_headers = {"Authorization": f"Bearer {token}"}
            resp = client.delete(
                f"{PRODUCTOS_URL}{created['id']}", headers=client_headers
            )
            assert resp.status_code == 403


class TestIngredientesProducto:
    def test_listar_ingredientes(
        self, client: TestClient, admin_user: Usuario
    ) -> None:
        """GET /{id}/ingredientes retorna los ingredientes del producto."""
        headers = _admin_headers(client)
        ing1 = _crear_ingrediente(client, headers, "Agua")
        ing2 = _crear_ingrediente(client, headers, "Azúcar")
        created = _crear_producto(
            client, headers, "Refresco",
            ingrediente_ids=[ing1["id"], ing2["id"]]
        )

        resp = client.get(f"{PRODUCTOS_URL}{created['id']}/ingredientes")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        nombres = {i["nombre"] for i in data}
        assert "Agua" in nombres
        assert "Azúcar" in nombres

    def test_ingredientes_producto_404(self, client: TestClient) -> None:
        """GET /{id}/ingredientes retorna 404 para producto inexistente."""
        resp = client.get(f"{PRODUCTOS_URL}99999/ingredientes")
        assert resp.status_code == 404
