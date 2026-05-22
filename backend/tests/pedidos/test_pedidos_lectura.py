"""Tests para los nuevos endpoints de lectura y cancelación de pedidos (Sprint 7).

Cubre:
  - GET /api/v1/pedidos         (6.1)
  - GET /api/v1/pedidos/{id}    (6.2)
  - GET /api/v1/pedidos/{id}/historial (6.3)
  - DELETE /api/v1/pedidos/{id} (6.4)
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import hash_password
from app.modules.usuarios.model import Usuario
from app.modules.roles.model import UsuarioRol
from app.modules.pedidos.model import EstadoPedido, HistorialEstadoPedido, Pedido
from app.modules.pagos.model import FormaPago
from app.modules.productos.model import Producto
from app.modules.direcciones.model import Direccion
from .conftest import client_headers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def login(client: TestClient, email: str, password: str) -> dict:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login fallido: {resp.json()}"
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def crear_pedido_en_bd(client_tc: TestClient, headers: dict, env: dict) -> int:
    body = {
        "direccion_id": env["direccion_id"],
        "forma_pago_codigo": "MERCADOPAGO",
        "items": [{"producto_id": env["producto_id"], "cantidad": 1}],
    }
    resp = client_tc.post("/api/v1/pedidos", json=body, headers=headers)
    assert resp.status_code == 201, f"Error al crear pedido: {resp.json()}"
    return resp.json()["id"]


def forzar_estado(session: Session, pedido_id: int, estado: str) -> None:
    pedido = session.get(Pedido, pedido_id)
    assert pedido is not None
    pedido.estado_codigo = estado
    session.add(pedido)
    session.commit()


# ---------------------------------------------------------------------------
# Fixture de entorno compartido
# ---------------------------------------------------------------------------

@pytest.fixture
def env_lectura(session: Session):
    """Entorno con CLIENT, ADMIN, PEDIDOS, producto y dirección."""
    # Estados
    for codigo, orden, terminal in [
        ("PENDIENTE", 1, False),
        ("CONFIRMADO", 2, False),
        ("EN_PREP", 3, False),
        ("EN_CAMINO", 4, False),
        ("ENTREGADO", 5, True),
        ("CANCELADO", 6, True),
    ]:
        session.merge(EstadoPedido(codigo=codigo, descripcion=codigo, orden=orden, es_terminal=terminal))

    session.merge(FormaPago(codigo="MERCADOPAGO", descripcion="MercadoPago", habilitado=True))

    # CLIENT principal
    client1 = Usuario(
        nombre="Lectura",
        apellido="Client1",
        email="lectura_client1@test.com",
        password_hash=hash_password("Client1234!"),
        activo=True,
    )
    session.add(client1)
    session.flush()
    session.add(UsuarioRol(usuario_id=client1.id, rol_codigo="CLIENT"))

    # CLIENT secundario (para pruebas de acceso ajeno)
    client2 = Usuario(
        nombre="Lectura",
        apellido="Client2",
        email="lectura_client2@test.com",
        password_hash=hash_password("Client1234!"),
        activo=True,
    )
    session.add(client2)
    session.flush()
    session.add(UsuarioRol(usuario_id=client2.id, rol_codigo="CLIENT"))

    # ADMIN
    admin = Usuario(
        nombre="Lectura",
        apellido="Admin",
        email="lectura_admin@test.com",
        password_hash=hash_password("Admin1234!"),
        activo=True,
    )
    session.add(admin)
    session.flush()
    session.add(UsuarioRol(usuario_id=admin.id, rol_codigo="ADMIN"))

    # PEDIDOS
    pedidos_user = Usuario(
        nombre="Lectura",
        apellido="Pedidos",
        email="lectura_pedidos@test.com",
        password_hash=hash_password("Pedidos1234!"),
        activo=True,
    )
    session.add(pedidos_user)
    session.flush()
    session.add(UsuarioRol(usuario_id=pedidos_user.id, rol_codigo="PEDIDOS"))

    # Producto
    producto = Producto(
        nombre="Producto Lectura",
        descripcion="Test",
        precio_base=Decimal("100.00"),
        stock_cantidad=20,
        disponible=True,
    )
    session.add(producto)
    session.flush()

    # Dirección del client1
    direccion = Direccion(
        usuario_id=client1.id,
        calle="Calle Test",
        numero="123",
        ciudad="Buenos Aires",
        provincia="CABA",
        codigo_postal="C1000",
        es_principal=True,
    )
    session.add(direccion)
    session.commit()

    return {
        "client1_id": client1.id,
        "client2_id": client2.id,
        "admin_id": admin.id,
        "pedidos_id": pedidos_user.id,
        "producto_id": producto.id,
        "direccion_id": direccion.id,
    }


# ---------------------------------------------------------------------------
# 6.1 — Tests GET /api/v1/pedidos
# ---------------------------------------------------------------------------

class TestListarPedidos:
    def test_client_ve_solo_propios(
        self, client: TestClient, session: Session, env_lectura: dict
    ):
        """CLIENT solo ve sus propios pedidos (no los de otro cliente)."""
        h1 = login(client, "lectura_client1@test.com", "Client1234!")
        h2 = login(client, "lectura_client2@test.com", "Client1234!")

        # CLIENT1 crea un pedido
        crear_pedido_en_bd(client, h1, env_lectura)

        # CLIENT2 no tiene pedidos → lista vacía
        resp = client.get("/api/v1/pedidos", headers=h2)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

        # CLIENT1 ve su pedido
        resp = client.get("/api/v1/pedidos", headers=h1)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_admin_ve_todos(
        self, client: TestClient, session: Session, env_lectura: dict
    ):
        """ADMIN ve todos los pedidos de todos los usuarios."""
        h1 = login(client, "lectura_client1@test.com", "Client1234!")
        h_admin = login(client, "lectura_admin@test.com", "Admin1234!")

        crear_pedido_en_bd(client, h1, env_lectura)

        resp = client.get("/api/v1/pedidos", headers=h_admin)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_filtro_por_estado_codigo(
        self, client: TestClient, session: Session, env_lectura: dict
    ):
        """Filtro ?estado_codigo devuelve solo pedidos con ese estado."""
        h1 = login(client, "lectura_client1@test.com", "Client1234!")
        h_admin = login(client, "lectura_admin@test.com", "Admin1234!")

        pedido_id = crear_pedido_en_bd(client, h1, env_lectura)

        # Filtro por PENDIENTE → debe aparecer
        resp = client.get("/api/v1/pedidos?estado_codigo=PENDIENTE", headers=h_admin)
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()["items"]]
        assert pedido_id in ids

        # Filtro por CANCELADO → no debe aparecer
        resp = client.get("/api/v1/pedidos?estado_codigo=CANCELADO", headers=h_admin)
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()["items"]]
        assert pedido_id not in ids

    def test_paginacion(
        self, client: TestClient, session: Session, env_lectura: dict
    ):
        """Paginación: page y size respetados correctamente."""
        h_admin = login(client, "lectura_admin@test.com", "Admin1234!")
        h1 = login(client, "lectura_client1@test.com", "Client1234!")

        # Crear 3 pedidos
        for _ in range(3):
            crear_pedido_en_bd(client, h1, env_lectura)

        # Pedir página 1 con size=2
        resp = client.get("/api/v1/pedidos?page=1&size=2", headers=h_admin)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["size"] == 2

    def test_sin_token_retorna_401(self, client: TestClient, env_lectura: dict):
        """Sin JWT retorna 401."""
        resp = client.get("/api/v1/pedidos")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 6.2 — Tests GET /api/v1/pedidos/{id}
# ---------------------------------------------------------------------------

class TestGetPedidoDetalle:
    def test_client_accede_a_propio(
        self, client: TestClient, session: Session, env_lectura: dict
    ):
        """CLIENT accede al detalle de su propio pedido."""
        h1 = login(client, "lectura_client1@test.com", "Client1234!")
        pedido_id = crear_pedido_en_bd(client, h1, env_lectura)

        resp = client.get(f"/api/v1/pedidos/{pedido_id}", headers=h1)
        assert resp.status_code == 200, resp.json()
        data = resp.json()
        assert data["id"] == pedido_id
        assert "items" in data
        assert "historial" in data
        assert "direccion_snapshot" in data

    def test_client_bloqueado_en_ajeno_retorna_404(
        self, client: TestClient, session: Session, env_lectura: dict
    ):
        """CLIENT recibe 404 al intentar ver el pedido de otro usuario."""
        h1 = login(client, "lectura_client1@test.com", "Client1234!")
        h2 = login(client, "lectura_client2@test.com", "Client1234!")
        pedido_id = crear_pedido_en_bd(client, h1, env_lectura)

        resp = client.get(f"/api/v1/pedidos/{pedido_id}", headers=h2)
        assert resp.status_code == 404

    def test_admin_accede_a_cualquier_pedido(
        self, client: TestClient, session: Session, env_lectura: dict
    ):
        """ADMIN puede acceder al detalle de cualquier pedido."""
        h1 = login(client, "lectura_client1@test.com", "Client1234!")
        h_admin = login(client, "lectura_admin@test.com", "Admin1234!")
        pedido_id = crear_pedido_en_bd(client, h1, env_lectura)

        resp = client.get(f"/api/v1/pedidos/{pedido_id}", headers=h_admin)
        assert resp.status_code == 200

    def test_pedido_inexistente_retorna_404(
        self, client: TestClient, session: Session, env_lectura: dict
    ):
        """ID inexistente retorna 404."""
        h_admin = login(client, "lectura_admin@test.com", "Admin1234!")
        resp = client.get("/api/v1/pedidos/99999", headers=h_admin)
        assert resp.status_code == 404

    def test_estructura_anidada_correcta(
        self, client: TestClient, session: Session, env_lectura: dict
    ):
        """La respuesta incluye items con snapshots y historial."""
        h1 = login(client, "lectura_client1@test.com", "Client1234!")
        pedido_id = crear_pedido_en_bd(client, h1, env_lectura)

        resp = client.get(f"/api/v1/pedidos/{pedido_id}", headers=h1)
        assert resp.status_code == 200
        data = resp.json()

        # Items con snapshots
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert "nombre_snapshot" in item
        assert "precio_snapshot" in item
        assert "cantidad" in item

        # Historial con al menos el estado inicial
        assert len(data["historial"]) >= 1
        primer_nodo = data["historial"][0]
        assert primer_nodo["estado_desde"] is None
        assert primer_nodo["estado_hasta"] == "PENDIENTE"


# ---------------------------------------------------------------------------
# 6.3 — Tests GET /api/v1/pedidos/{id}/historial
# ---------------------------------------------------------------------------

class TestGetHistorialPedido:
    def test_orden_cronologico(
        self, client: TestClient, session: Session, env_lectura: dict
    ):
        """El historial retorna los nodos en orden cronológico (ASC)."""
        h1 = login(client, "lectura_client1@test.com", "Client1234!")
        h_admin = login(client, "lectura_admin@test.com", "Admin1234!")
        pedido_id = crear_pedido_en_bd(client, h1, env_lectura)
        forzar_estado(session, pedido_id, "CONFIRMADO")

        # Insertar registro de historial manual para simular transición
        from app.modules.pedidos.model import HistorialEstadoPedido
        from datetime import datetime, timezone, timedelta
        h_entry = HistorialEstadoPedido(
            pedido_id=pedido_id,
            estado_desde="PENDIENTE",
            estado_hasta="CONFIRMADO",
            cambiado_por_id=None,
            created_at=datetime.now(timezone.utc) + timedelta(seconds=1),
        )
        session.add(h_entry)
        session.commit()

        resp = client.get(f"/api/v1/pedidos/{pedido_id}/historial", headers=h_admin)
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 1
        # Primer nodo tiene estado_desde=None (creación)
        assert items[0]["estado_desde"] is None

    def test_primer_nodo_estado_desde_null(
        self, client: TestClient, session: Session, env_lectura: dict
    ):
        """El primer nodo del historial tiene estado_desde=None."""
        h1 = login(client, "lectura_client1@test.com", "Client1234!")
        pedido_id = crear_pedido_en_bd(client, h1, env_lectura)

        resp = client.get(f"/api/v1/pedidos/{pedido_id}/historial", headers=h1)
        assert resp.status_code == 200
        items = resp.json()
        assert items[0]["estado_desde"] is None
        assert items[0]["estado_hasta"] == "PENDIENTE"

    def test_client_ajeno_retorna_404(
        self, client: TestClient, session: Session, env_lectura: dict
    ):
        """CLIENT no puede ver el historial de un pedido ajeno."""
        h1 = login(client, "lectura_client1@test.com", "Client1234!")
        h2 = login(client, "lectura_client2@test.com", "Client1234!")
        pedido_id = crear_pedido_en_bd(client, h1, env_lectura)

        resp = client.get(f"/api/v1/pedidos/{pedido_id}/historial", headers=h2)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 6.4 — Tests DELETE /api/v1/pedidos/{id}
# ---------------------------------------------------------------------------

class TestCancelarPedidoPropio:
    def test_cancelacion_exitosa_con_motivo(
        self, client: TestClient, session: Session, env_lectura: dict
    ):
        """CLIENT cancela su propio pedido PENDIENTE con motivo válido."""
        h1 = login(client, "lectura_client1@test.com", "Client1234!")
        pedido_id = crear_pedido_en_bd(client, h1, env_lectura)

        resp = client.delete(
            f"/api/v1/pedidos/{pedido_id}",
            json={"motivo": "Ya no lo necesito"},
            headers=h1,
        )
        assert resp.status_code == 200, resp.json()
        data = resp.json()
        assert data["estado_codigo"] == "CANCELADO"

    def test_pedido_ajeno_retorna_404(
        self, client: TestClient, session: Session, env_lectura: dict
    ):
        """CLIENT no puede cancelar el pedido de otro usuario."""
        h1 = login(client, "lectura_client1@test.com", "Client1234!")
        h2 = login(client, "lectura_client2@test.com", "Client1234!")
        pedido_id = crear_pedido_en_bd(client, h1, env_lectura)

        resp = client.delete(
            f"/api/v1/pedidos/{pedido_id}",
            json={"motivo": "Quiero cancelar"},
            headers=h2,
        )
        assert resp.status_code == 404

    def test_pedido_en_confirmado_retorna_422(
        self, client: TestClient, session: Session, env_lectura: dict
    ):
        """CLIENT no puede cancelar un pedido en estado CONFIRMADO (solo ADMIN)."""
        h1 = login(client, "lectura_client1@test.com", "Client1234!")
        pedido_id = crear_pedido_en_bd(client, h1, env_lectura)
        forzar_estado(session, pedido_id, "CONFIRMADO")

        resp = client.delete(
            f"/api/v1/pedidos/{pedido_id}",
            json={"motivo": "Quiero cancelar"},
            headers=h1,
        )
        assert resp.status_code == 422

    def test_sin_motivo_retorna_422(
        self, client: TestClient, session: Session, env_lectura: dict
    ):
        """Body sin campo motivo devuelve 422 (validación Pydantic)."""
        h1 = login(client, "lectura_client1@test.com", "Client1234!")
        pedido_id = crear_pedido_en_bd(client, h1, env_lectura)

        resp = client.delete(
            f"/api/v1/pedidos/{pedido_id}",
            json={},
            headers=h1,
        )
        assert resp.status_code == 422

    def test_rol_no_client_retorna_403(
        self, client: TestClient, session: Session, env_lectura: dict
    ):
        """ADMIN no puede usar el endpoint DELETE /pedidos/{id} (es exclusivo de CLIENT)."""
        h1 = login(client, "lectura_client1@test.com", "Client1234!")
        h_admin = login(client, "lectura_admin@test.com", "Admin1234!")
        pedido_id = crear_pedido_en_bd(client, h1, env_lectura)

        resp = client.delete(
            f"/api/v1/pedidos/{pedido_id}",
            json={"motivo": "Cancelar"},
            headers=h_admin,
        )
        assert resp.status_code == 403
