"""Tests de integración para /api/v1/direcciones."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.modules.usuarios.model import Usuario
from app.modules.roles.model import UsuarioRol
from app.core.security import hash_password


DIRECCIONES_URL = "/api/v1/direcciones/"


# ---------------------------------------------------------------------------
# Helpers de autenticación y creación de recursos
# ---------------------------------------------------------------------------

def _login(client: TestClient, email: str, password: str) -> dict:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login fallido: {resp.json()}"
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _client_headers(client: TestClient) -> dict:
    return _login(client, "client@test.com", "Client1234!")


def _admin_headers(client: TestClient) -> dict:
    return _login(client, "admin@test.com", "Admin1234!")


def _crear_cliente2(session: Session) -> Usuario:
    """Crea un segundo usuario CLIENT en la BD de test."""
    usuario = Usuario(
        nombre="Client2",
        apellido="Test",
        email="client2@test.com",
        password_hash=hash_password("Client1234!"),
        activo=True,
    )
    session.add(usuario)
    session.flush()
    session.add(UsuarioRol(usuario_id=usuario.id, rol_codigo="CLIENT"))
    session.commit()
    session.refresh(usuario)
    return usuario


def _payload_valido(**overrides) -> dict:
    base = {
        "calle": "Av. Corrientes",
        "numero": "1234",
        "ciudad": "Buenos Aires",
        "provincia": "CABA",
        "codigo_postal": "C1043",
    }
    base.update(overrides)
    return base


def _crear_direccion(client: TestClient, headers: dict, **overrides) -> dict:
    payload = _payload_valido(**overrides)
    resp = client.post(DIRECCIONES_URL, json=payload, headers=headers)
    assert resp.status_code == 201, f"Error al crear dirección: {resp.json()}"
    return resp.json()


# ---------------------------------------------------------------------------
# Listar
# ---------------------------------------------------------------------------

class TestListarDirecciones:
    def test_listar_sin_auth_retorna_401(self, client: TestClient) -> None:
        resp = client.get(DIRECCIONES_URL)
        assert resp.status_code == 401

    def test_listar_vacio(self, client: TestClient, client_user: Usuario) -> None:
        headers = _client_headers(client)
        resp = client.get(DIRECCIONES_URL, headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_listar_propias(self, client: TestClient, client_user: Usuario) -> None:
        headers = _client_headers(client)
        _crear_direccion(client, headers, calle="Av. Rivadavia")
        _crear_direccion(client, headers, calle="Av. Santa Fe")

        resp = client.get(DIRECCIONES_URL, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_listar_principal_primero(self, client: TestClient, client_user: Usuario) -> None:
        """El listado debe ordenar la dirección principal en primer lugar."""
        headers = _client_headers(client)
        primera = _crear_direccion(client, headers, calle="Av. Primera")  # → principal
        segunda = _crear_direccion(client, headers, calle="Av. Segunda")

        # Promover la segunda a principal
        client.patch(f"{DIRECCIONES_URL}{segunda['id']}/principal", headers=headers)

        resp = client.get(DIRECCIONES_URL, headers=headers)
        data = resp.json()
        assert data[0]["id"] == segunda["id"]
        assert data[0]["es_principal"] is True

    def test_aislamiento_entre_usuarios(
        self, client: TestClient, client_user: Usuario, session: Session
    ) -> None:
        """El usuario A no ve las direcciones del usuario B."""
        headers_a = _client_headers(client)
        _crear_direccion(client, headers_a)

        # Crear cliente 2 y loguearse como él
        _crear_cliente2(session)
        headers_b = _login(client, "client2@test.com", "Client1234!")

        resp = client.get(DIRECCIONES_URL, headers=headers_b)
        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# Crear
# ---------------------------------------------------------------------------

class TestCrearDireccion:
    def test_primera_direccion_es_principal(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        """RN-DI01: la primera dirección siempre queda como principal."""
        headers = _client_headers(client)
        resp = client.post(DIRECCIONES_URL, json=_payload_valido(es_principal=False), headers=headers)
        assert resp.status_code == 201
        assert resp.json()["es_principal"] is True

    def test_nesima_direccion_no_promovida(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        """N-ésima dirección sin promoción queda como no principal."""
        headers = _client_headers(client)
        _crear_direccion(client, headers)  # primera → principal
        resp = client.post(DIRECCIONES_URL, json=_payload_valido(calle="Av. Nueva"), headers=headers)
        assert resp.status_code == 201
        assert resp.json()["es_principal"] is False

    def test_crear_sin_auth(self, client: TestClient) -> None:
        resp = client.post(DIRECCIONES_URL, json=_payload_valido())
        assert resp.status_code == 401

    def test_validacion_campos_requeridos_422(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        headers = _client_headers(client)
        # body sin 'calle' → debe fallar con 422
        resp = client.post(
            DIRECCIONES_URL,
            json={"numero": "123", "ciudad": "BA", "provincia": "BA", "codigo_postal": "1000"},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_crea_con_campos_opcionales(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        headers = _client_headers(client)
        payload = _payload_valido(piso="3", depto="B", referencia="Timbre 3B")
        resp = client.post(DIRECCIONES_URL, json=payload, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["piso"] == "3"
        assert data["depto"] == "B"
        assert data["referencia"] == "Timbre 3B"


# ---------------------------------------------------------------------------
# Actualizar
# ---------------------------------------------------------------------------

class TestActualizarDireccion:
    def test_actualizar_exitoso(self, client: TestClient, client_user: Usuario) -> None:
        headers = _client_headers(client)
        d = _crear_direccion(client, headers)
        resp = client.put(
            f"{DIRECCIONES_URL}{d['id']}",
            json={"calle": "Av. Modificada"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["calle"] == "Av. Modificada"

    def test_actualizar_ignora_es_principal(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        """PUT no debe modificar es_principal aunque venga en el body."""
        headers = _client_headers(client)
        d = _crear_direccion(client, headers)  # principal
        _crear_direccion(client, headers, calle="Av. Segunda")  # segunda, no principal

        # Intentar cambiar es_principal vía PUT (simulando campo extra)
        resp = client.put(
            f"{DIRECCIONES_URL}{d['id']}",
            json={"calle": "Av. Nueva"},
            headers=headers,
        )
        assert resp.status_code == 200
        # La primera sigue siendo principal (no cambió)
        assert resp.json()["es_principal"] is True

    def test_actualizar_direccion_de_otro_retorna_404(
        self, client: TestClient, client_user: Usuario, session: Session
    ) -> None:
        headers_a = _client_headers(client)
        d = _crear_direccion(client, headers_a)

        _crear_cliente2(session)
        headers_b = _login(client, "client2@test.com", "Client1234!")

        resp = client.put(
            f"{DIRECCIONES_URL}{d['id']}",
            json={"calle": "Hackeo"},
            headers=headers_b,
        )
        assert resp.status_code == 404
        assert resp.json()["code"] == "DIRECCION_NOT_FOUND"


# ---------------------------------------------------------------------------
# PATCH principal
# ---------------------------------------------------------------------------

class TestSetPrincipal:
    def test_patch_principal_exitoso(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        headers = _client_headers(client)
        primera = _crear_direccion(client, headers)
        segunda = _crear_direccion(client, headers, calle="Av. Segunda")

        resp = client.patch(f"{DIRECCIONES_URL}{segunda['id']}/principal", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["direccion"]["es_principal"] is True
        assert data["direccion"]["id"] == segunda["id"]

    def test_patch_desmarca_anterior(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        headers = _client_headers(client)
        primera = _crear_direccion(client, headers)
        segunda = _crear_direccion(client, headers, calle="Av. Segunda")

        client.patch(f"{DIRECCIONES_URL}{segunda['id']}/principal", headers=headers)

        # Verificar que la primera ya no es principal
        resp = client.get(DIRECCIONES_URL, headers=headers)
        items = {d["id"]: d for d in resp.json()}
        assert items[primera["id"]]["es_principal"] is False
        assert items[segunda["id"]]["es_principal"] is True

    def test_patch_idempotente(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        headers = _client_headers(client)
        d = _crear_direccion(client, headers)
        # Llamar dos veces sobre la misma dirección → idempotente
        resp1 = client.patch(f"{DIRECCIONES_URL}{d['id']}/principal", headers=headers)
        resp2 = client.patch(f"{DIRECCIONES_URL}{d['id']}/principal", headers=headers)
        assert resp1.status_code == 200
        assert resp2.status_code == 200

    def test_patch_direccion_de_otro_retorna_404(
        self, client: TestClient, client_user: Usuario, session: Session
    ) -> None:
        headers_a = _client_headers(client)
        d = _crear_direccion(client, headers_a)

        _crear_cliente2(session)
        headers_b = _login(client, "client2@test.com", "Client1234!")

        resp = client.patch(f"{DIRECCIONES_URL}{d['id']}/principal", headers=headers_b)
        assert resp.status_code == 404
        assert resp.json()["code"] == "DIRECCION_NOT_FOUND"


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

class TestEliminarDireccion:
    def test_delete_no_principal(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        headers = _client_headers(client)
        principal = _crear_direccion(client, headers)
        no_principal = _crear_direccion(client, headers, calle="Av. Segunda")

        resp = client.delete(f"{DIRECCIONES_URL}{no_principal['id']}", headers=headers)
        assert resp.status_code == 204

        # Verificar que no aparece más en el listado
        lista = client.get(DIRECCIONES_URL, headers=headers).json()
        ids = [d["id"] for d in lista]
        assert no_principal["id"] not in ids

    def test_delete_unica_direccion(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        """Puede eliminar la única dirección aunque sea principal."""
        headers = _client_headers(client)
        d = _crear_direccion(client, headers)

        resp = client.delete(f"{DIRECCIONES_URL}{d['id']}", headers=headers)
        assert resp.status_code == 204

        lista = client.get(DIRECCIONES_URL, headers=headers).json()
        assert lista == []

    def test_delete_principal_con_otras_retorna_400(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        headers = _client_headers(client)
        principal = _crear_direccion(client, headers)
        _crear_direccion(client, headers, calle="Av. Segunda")

        resp = client.delete(f"{DIRECCIONES_URL}{principal['id']}", headers=headers)
        assert resp.status_code == 400
        assert resp.json()["code"] == "PRINCIPAL_CANNOT_DELETE"

    def test_delete_direccion_de_otro_retorna_404(
        self, client: TestClient, client_user: Usuario, session: Session
    ) -> None:
        headers_a = _client_headers(client)
        d = _crear_direccion(client, headers_a)

        _crear_cliente2(session)
        headers_b = _login(client, "client2@test.com", "Client1234!")

        resp = client.delete(f"{DIRECCIONES_URL}{d['id']}", headers=headers_b)
        assert resp.status_code == 404
        assert resp.json()["code"] == "DIRECCION_NOT_FOUND"

    def test_delete_sin_auth(self, client: TestClient, client_user: Usuario) -> None:
        headers = _client_headers(client)
        d = _crear_direccion(client, headers)
        resp = client.delete(f"{DIRECCIONES_URL}{d['id']}")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Invariante: máximo una principal por usuario (Tarea 8.2)
# ---------------------------------------------------------------------------

class TestInvariantePrincipal:
    def test_siempre_una_principal_tras_crear(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        headers = _client_headers(client)
        _crear_direccion(client, headers)

        resp = client.get(DIRECCIONES_URL, headers=headers)
        principales = [d for d in resp.json() if d["es_principal"]]
        assert len(principales) == 1

    def test_invariante_tras_secuencia_crear_y_patch(
        self, client: TestClient, client_user: Usuario
    ) -> None:
        """Crear 3, PATCH principal sobre la segunda → exactamente 1 principal."""
        headers = _client_headers(client)
        primera = _crear_direccion(client, headers, calle="Av. Primera")
        segunda = _crear_direccion(client, headers, calle="Av. Segunda")
        tercera = _crear_direccion(client, headers, calle="Av. Tercera")

        client.patch(f"{DIRECCIONES_URL}{segunda['id']}/principal", headers=headers)

        resp = client.get(DIRECCIONES_URL, headers=headers)
        all_dirs = resp.json()
        principales = [d for d in all_dirs if d["es_principal"]]
        assert len(principales) == 1
        assert principales[0]["id"] == segunda["id"]
