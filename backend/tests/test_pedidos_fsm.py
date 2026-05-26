"""Tests para la FSM de pedidos (RN-FS01 a RN-FS10)."""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.modules.pedidos.fsm import order_fsm, OrderStateMachine
from app.modules.pedidos.model import EstadoPedido, HistorialEstadoPedido, Pedido
from app.modules.pedidos.service import pedido_service
from app.modules.pagos.model import FormaPago
from app.modules.productos.model import Producto
from app.modules.direcciones.model import Direccion
from app.modules.usuarios.model import Usuario
from app.modules.roles.model import UsuarioRol
from app.core.security import hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def login(client: TestClient, email: str, password: str) -> dict:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login fallido: {resp.json()}"
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fsm_env(session: Session):
    """Entorno completo para tests FSM con CLIENT y ADMIN."""
    # Estados de pedido
    for codigo, orden, terminal in [
        ("PENDIENTE", 1, False),
        ("CONFIRMADO", 2, False),
        ("EN_PREP", 3, False),
        ("EN_CAMINO", 4, False),
        ("ENTREGADO", 5, True),
        ("CANCELADO", 6, True),
    ]:
        session.merge(EstadoPedido(codigo=codigo, descripcion=codigo, orden=orden, es_terminal=terminal))

    # Forma de pago
    session.merge(FormaPago(codigo="MERCADOPAGO", descripcion="MercadoPago", habilitado=True))

    # Usuario CLIENT
    client_user = Usuario(
        nombre="FSM",
        apellido="Client",
        email="fsm_client@test.com",
        password_hash=hash_password("Client1234!"),
        activo=True,
    )
    session.add(client_user)
    session.flush()
    session.add(UsuarioRol(usuario_id=client_user.id, rol_codigo="CLIENT"))

    # Usuario ADMIN
    admin_user = Usuario(
        nombre="FSM",
        apellido="Admin",
        email="fsm_admin@test.com",
        password_hash=hash_password("Admin1234!"),
        activo=True,
    )
    session.add(admin_user)
    session.flush()
    session.add(UsuarioRol(usuario_id=admin_user.id, rol_codigo="ADMIN"))

    # Usuario PEDIDOS
    pedidos_user = Usuario(
        nombre="FSM",
        apellido="Pedidos",
        email="fsm_pedidos@test.com",
        password_hash=hash_password("Pedidos1234!"),
        activo=True,
    )
    session.add(pedidos_user)
    session.flush()
    session.add(UsuarioRol(usuario_id=pedidos_user.id, rol_codigo="PEDIDOS"))

    # Producto con stock
    producto = Producto(
        nombre="Producto FSM",
        descripcion="Para FSM tests",
        precio_base=Decimal("100.00"),
        stock_cantidad=10,
        disponible=True,
    )
    session.add(producto)
    session.flush()

    # Dirección del cliente
    direccion = Direccion(
        usuario_id=client_user.id,
        calle="FSM Calle",
        numero="1",
        ciudad="BA",
        provincia="CABA",
        codigo_postal="C1000",
        es_principal=True,
    )
    session.add(direccion)
    session.commit()
    session.refresh(client_user)
    session.refresh(admin_user)
    session.refresh(pedidos_user)
    session.refresh(producto)
    session.refresh(direccion)

    return {
        "client_id": client_user.id,
        "admin_id": admin_user.id,
        "pedidos_id": pedidos_user.id,
        "producto_id": producto.id,
        "direccion_id": direccion.id,
    }


def _crear_pedido(client_tc: TestClient, env: dict, headers: dict) -> int:
    body = {
        "direccion_id": env["direccion_id"],
        "forma_pago_codigo": "MERCADOPAGO",
        "items": [{"producto_id": env["producto_id"], "cantidad": 1}],
    }
    resp = client_tc.post("/api/v1/pedidos", json=body, headers=headers)
    assert resp.status_code == 201, f"Error: {resp.json()}"
    return resp.json()["id"]


def _set_estado(session: Session, pedido_id: int, estado: str):
    """Fuerza el estado del pedido directamente en BD."""
    pedido = session.get(Pedido, pedido_id)
    pedido.estado_codigo = estado
    session.add(pedido)
    session.commit()


# ---------------------------------------------------------------------------
# Tests: OrderStateMachine (unidad)
# ---------------------------------------------------------------------------

class TestOrderStateMachineUnit:
    def test_confirmado_a_en_prep_admin(self):
        """CONFIRMADO → EN_PREP está permitido para ADMIN."""
        assert order_fsm.is_allowed("CONFIRMADO", "EN_PREP", ["ADMIN"]) is True

    def test_confirmado_a_en_prep_pedidos(self):
        """CONFIRMADO → EN_PREP está permitido para PEDIDOS."""
        assert order_fsm.is_allowed("CONFIRMADO", "EN_PREP", ["PEDIDOS"]) is True

    def test_en_prep_a_en_camino(self):
        """EN_PREP → EN_CAMINO está permitido para PEDIDOS."""
        assert order_fsm.is_allowed("EN_PREP", "EN_CAMINO", ["PEDIDOS"]) is True

    def test_en_camino_a_entregado(self):
        """EN_CAMINO → ENTREGADO está permitido para ADMIN."""
        assert order_fsm.is_allowed("EN_CAMINO", "ENTREGADO", ["ADMIN"]) is True

    def test_pendiente_a_cancelado_client(self):
        """PENDIENTE → CANCELADO está permitido para CLIENT (propio pedido)."""
        assert order_fsm.is_allowed("PENDIENTE", "CANCELADO", ["CLIENT"]) is True

    def test_confirmado_a_cancelado_admin(self):
        """CONFIRMADO → CANCELADO está permitido para ADMIN."""
        assert order_fsm.is_allowed("CONFIRMADO", "CANCELADO", ["ADMIN"]) is True

    def test_en_prep_a_cancelado_admin(self):
        """EN_PREP → CANCELADO solo permitido para ADMIN."""
        assert order_fsm.is_allowed("EN_PREP", "CANCELADO", ["ADMIN"]) is True

    def test_en_prep_a_cancelado_pedidos_rechazado(self):
        """EN_PREP → CANCELADO NO está permitido para PEDIDOS."""
        assert order_fsm.is_allowed("EN_PREP", "CANCELADO", ["PEDIDOS"]) is False

    def test_client_no_puede_cancelar_en_prep(self):
        """CLIENT NO puede cancelar desde EN_PREP."""
        assert order_fsm.is_allowed("EN_PREP", "CANCELADO", ["CLIENT"]) is False

    def test_pendiente_a_confirmado_rechazado_para_client(self):
        """PENDIENTE → CONFIRMADO rechazado para CLIENT."""
        assert order_fsm.is_allowed("PENDIENTE", "CONFIRMADO", ["CLIENT"]) is False

    def test_pendiente_a_confirmado_permitido_para_admin_y_pedidos(self):
        """PENDIENTE → CONFIRMADO permitido para ADMIN y PEDIDOS (confirmación manual EFECTIVO/TRANSFERENCIA)."""
        assert order_fsm.is_allowed("PENDIENTE", "CONFIRMADO", ["ADMIN"]) is True
        assert order_fsm.is_allowed("PENDIENTE", "CONFIRMADO", ["PEDIDOS"]) is True
        assert order_fsm.is_allowed("PENDIENTE", "CONFIRMADO", ["ADMIN", "PEDIDOS"]) is True

    def test_pendiente_a_confirmado_permitido_para_sistema(self):
        """PENDIENTE → CONFIRMADO permitido para el sistema (webhook)."""
        assert order_fsm.is_allowed_for_system("PENDIENTE", "CONFIRMADO") is True

    def test_terminal_entregado_sin_salidas(self):
        """ENTREGADO es terminal — sin transiciones salientes."""
        for estado in ["CONFIRMADO", "EN_PREP", "EN_CAMINO", "CANCELADO", "PENDIENTE"]:
            assert order_fsm.is_allowed("ENTREGADO", estado, ["ADMIN"]) is False

    def test_terminal_cancelado_sin_salidas(self):
        """CANCELADO es terminal — sin transiciones salientes."""
        for estado in ["CONFIRMADO", "PENDIENTE", "EN_PREP"]:
            assert order_fsm.is_allowed("CANCELADO", estado, ["ADMIN"]) is False

    def test_requiere_motivo_cancelado(self):
        """requiere_motivo retorna True solo para CANCELADO."""
        assert order_fsm.requiere_motivo("CANCELADO") is True
        assert order_fsm.requiere_motivo("EN_PREP") is False
        assert order_fsm.requiere_motivo("ENTREGADO") is False

    def test_transicion_invalida_en_mapa(self):
        """Transición no definida en el mapa retorna False."""
        assert order_fsm.is_allowed("CONFIRMADO", "PENDIENTE", ["ADMIN"]) is False
        assert order_fsm.is_allowed("EN_CAMINO", "PENDIENTE", ["ADMIN"]) is False


# ---------------------------------------------------------------------------
# Tests: PATCH /api/v1/pedidos/{id}/estado
# ---------------------------------------------------------------------------

class TestCambiarEstadoEndpoint:
    def test_confirmado_a_en_prep_por_pedidos(
        self,
        client: TestClient,
        session: Session,
        fsm_env: dict,
    ):
        """CONFIRMADO → EN_PREP por usuario PEDIDOS retorna 200."""
        client_headers = login(client, "fsm_client@test.com", "Client1234!")
        pedido_id = _crear_pedido(client, fsm_env, client_headers)
        _set_estado(session, pedido_id, "CONFIRMADO")

        pedidos_headers = login(client, "fsm_pedidos@test.com", "Pedidos1234!")
        resp = client.patch(
            f"/api/v1/pedidos/{pedido_id}/estado",
            json={"nuevo_estado": "EN_PREP"},
            headers=pedidos_headers,
        )
        assert resp.status_code == 200, resp.json()
        assert resp.json()["estado_codigo"] == "EN_PREP"

        # Verificar historial
        session.expire_all()
        historial = session.exec(
            select(HistorialEstadoPedido)
            .where(HistorialEstadoPedido.pedido_id == pedido_id)
            .order_by(HistorialEstadoPedido.id.asc())
        ).all()
        # 1 de creación + 1 de transición
        assert len(historial) >= 2
        last = historial[-1]
        assert last.estado_desde == "CONFIRMADO"
        assert last.estado_hasta == "EN_PREP"

    def test_pendiente_a_confirmado_permitido_para_admin_patch(
        self,
        client: TestClient,
        session: Session,
        fsm_env: dict,
    ):
        """PENDIENTE → CONFIRMADO vía PATCH permitido para ADMIN (confirmación manual EFECTIVO/TRANSFERENCIA)."""
        admin_headers = login(client, "fsm_admin@test.com", "Admin1234!")
        client_headers = login(client, "fsm_client@test.com", "Client1234!")
        pedido_id = _crear_pedido(client, fsm_env, client_headers)

        resp = client.patch(
            f"/api/v1/pedidos/{pedido_id}/estado",
            json={"nuevo_estado": "CONFIRMADO"},
            headers=admin_headers,
        )
        assert resp.status_code == 200, resp.json()
        assert resp.json()["estado_codigo"] == "CONFIRMADO"

    def test_pendiente_a_confirmado_rechazado_para_client_patch(
        self,
        client: TestClient,
        session: Session,
        fsm_env: dict,
    ):
        """PENDIENTE → CONFIRMADO rechazado para CLIENT vía PATCH."""
        client_headers = login(client, "fsm_client@test.com", "Client1234!")
        pedido_id = _crear_pedido(client, fsm_env, client_headers)

        resp = client.patch(
            f"/api/v1/pedidos/{pedido_id}/estado",
            json={"nuevo_estado": "CONFIRMADO"},
            headers=client_headers,
        )
        assert resp.status_code == 422
        assert resp.json()["code"] == "TRANSICION_NO_PERMITIDA"

    def test_transicion_invalida_retorna_422(
        self,
        client: TestClient,
        session: Session,
        fsm_env: dict,
    ):
        """Transición no permitida retorna 422."""
        admin_headers = login(client, "fsm_admin@test.com", "Admin1234!")
        client_headers = login(client, "fsm_client@test.com", "Client1234!")
        pedido_id = _crear_pedido(client, fsm_env, client_headers)
        _set_estado(session, pedido_id, "EN_PREP")

        resp = client.patch(
            f"/api/v1/pedidos/{pedido_id}/estado",
            json={"nuevo_estado": "PENDIENTE"},
            headers=admin_headers,
        )
        assert resp.status_code == 422
        assert resp.json()["code"] == "TRANSICION_NO_PERMITIDA"

    def test_cancelar_con_motivo(
        self,
        client: TestClient,
        session: Session,
        fsm_env: dict,
    ):
        """Cancelar con motivo válido retorna 200."""
        client_headers = login(client, "fsm_client@test.com", "Client1234!")
        pedido_id = _crear_pedido(client, fsm_env, client_headers)

        resp = client.patch(
            f"/api/v1/pedidos/{pedido_id}/estado",
            json={"nuevo_estado": "CANCELADO", "motivo": "El cliente no puede recibirlo"},
            headers=client_headers,
        )
        assert resp.status_code == 200, resp.json()
        assert resp.json()["estado_codigo"] == "CANCELADO"

    def test_cancelar_sin_motivo_retorna_422(
        self,
        client: TestClient,
        session: Session,
        fsm_env: dict,
    ):
        """Cancelar sin motivo retorna 422 (RN-FS09)."""
        client_headers = login(client, "fsm_client@test.com", "Client1234!")
        pedido_id = _crear_pedido(client, fsm_env, client_headers)

        resp = client.patch(
            f"/api/v1/pedidos/{pedido_id}/estado",
            json={"nuevo_estado": "CANCELADO"},
            headers=client_headers,
        )
        assert resp.status_code == 422
        assert resp.json()["code"] == "MOTIVO_REQUERIDO"

    def test_cancelar_motivo_vacio_retorna_422(
        self,
        client: TestClient,
        session: Session,
        fsm_env: dict,
    ):
        """Cancelar con motivo vacío (solo espacios) retorna 422 (RN-FS09)."""
        client_headers = login(client, "fsm_client@test.com", "Client1234!")
        pedido_id = _crear_pedido(client, fsm_env, client_headers)

        resp = client.patch(
            f"/api/v1/pedidos/{pedido_id}/estado",
            json={"nuevo_estado": "CANCELADO", "motivo": "   "},
            headers=client_headers,
        )
        assert resp.status_code == 422
        assert resp.json()["code"] == "MOTIVO_REQUERIDO"

    def test_pedido_no_encontrado_retorna_404(
        self,
        client: TestClient,
        fsm_env: dict,
    ):
        """Pedido inexistente retorna 404."""
        admin_headers = login(client, "fsm_admin@test.com", "Admin1234!")

        resp = client.patch(
            "/api/v1/pedidos/99999/estado",
            json={"nuevo_estado": "EN_PREP"},
            headers=admin_headers,
        )
        assert resp.status_code == 404
        assert resp.json()["code"] == "PEDIDO_NOT_FOUND"

    def test_sin_autenticacion_retorna_401(self, client: TestClient, fsm_env: dict):
        """Sin JWT retorna 401."""
        resp = client.patch(
            "/api/v1/pedidos/1/estado",
            json={"nuevo_estado": "EN_PREP"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests: Decremento de stock (RN-FS03)
# ---------------------------------------------------------------------------

class TestDecrementoStock:
    def test_stock_decrementado_al_confirmar(
        self,
        client: TestClient,
        session: Session,
        fsm_env: dict,
    ):
        """Al confirmar pedido, el stock se decrementa (RN-FS03)."""
        client_headers = login(client, "fsm_client@test.com", "Client1234!")

        # Crear pedido con 2 unidades del producto
        body = {
            "direccion_id": fsm_env["direccion_id"],
            "forma_pago_codigo": "MERCADOPAGO",
            "items": [{"producto_id": fsm_env["producto_id"], "cantidad": 3}],
        }
        resp = client_tc = client.post("/api/v1/pedidos", json=body, headers=client_headers)
        assert resp.status_code == 201
        pedido_id = resp.json()["id"]

        # Stock antes: 10
        session.expire_all()
        producto = session.get(Producto, fsm_env["producto_id"])
        stock_antes = producto.stock_cantidad  # Debe ser 10

        # Confirmar vía service (simula webhook)
        from app.core.uow import UnitOfWork
        with UnitOfWork() as uow:
            pedido_service.confirmar_pedido(uow, pedido_id, actor_id=None)

        # Verificar stock decrementado
        session.expire_all()
        producto = session.get(Producto, fsm_env["producto_id"])
        assert producto.stock_cantidad == stock_antes - 3

    def test_stock_restaurado_al_cancelar_desde_confirmado(
        self,
        client: TestClient,
        session: Session,
        fsm_env: dict,
    ):
        """Al cancelar desde CONFIRMADO, el stock se restaura (RN-FS05)."""
        client_headers = login(client, "fsm_client@test.com", "Client1234!")
        admin_headers = login(client, "fsm_admin@test.com", "Admin1234!")

        body = {
            "direccion_id": fsm_env["direccion_id"],
            "forma_pago_codigo": "MERCADOPAGO",
            "items": [{"producto_id": fsm_env["producto_id"], "cantidad": 2}],
        }
        resp = client.post("/api/v1/pedidos", json=body, headers=client_headers)
        assert resp.status_code == 201
        pedido_id = resp.json()["id"]

        # Stock inicial
        session.expire_all()
        producto = session.get(Producto, fsm_env["producto_id"])
        stock_inicial = producto.stock_cantidad

        # Confirmar vía service
        from app.core.uow import UnitOfWork
        with UnitOfWork() as uow:
            pedido_service.confirmar_pedido(uow, pedido_id, actor_id=None)

        # Stock decrementado
        session.expire_all()
        producto = session.get(Producto, fsm_env["producto_id"])
        assert producto.stock_cantidad == stock_inicial - 2

        # Cancelar desde CONFIRMADO
        resp = client.patch(
            f"/api/v1/pedidos/{pedido_id}/estado",
            json={"nuevo_estado": "CANCELADO", "motivo": "Cancelación de prueba"},
            headers=admin_headers,
        )
        assert resp.status_code == 200, resp.json()

        # Stock restaurado
        session.expire_all()
        producto = session.get(Producto, fsm_env["producto_id"])
        assert producto.stock_cantidad == stock_inicial

    def test_cancelar_desde_pendiente_no_afecta_stock(
        self,
        client: TestClient,
        session: Session,
        fsm_env: dict,
    ):
        """Cancelar desde PENDIENTE no modifica el stock (RN-FS05)."""
        client_headers = login(client, "fsm_client@test.com", "Client1234!")

        body = {
            "direccion_id": fsm_env["direccion_id"],
            "forma_pago_codigo": "MERCADOPAGO",
            "items": [{"producto_id": fsm_env["producto_id"], "cantidad": 2}],
        }
        resp = client.post("/api/v1/pedidos", json=body, headers=client_headers)
        pedido_id = resp.json()["id"]

        session.expire_all()
        producto = session.get(Producto, fsm_env["producto_id"])
        stock_antes = producto.stock_cantidad

        resp = client.patch(
            f"/api/v1/pedidos/{pedido_id}/estado",
            json={"nuevo_estado": "CANCELADO", "motivo": "Cambié de opinión"},
            headers=client_headers,
        )
        assert resp.status_code == 200

        session.expire_all()
        producto = session.get(Producto, fsm_env["producto_id"])
        assert producto.stock_cantidad == stock_antes  # Sin cambio
