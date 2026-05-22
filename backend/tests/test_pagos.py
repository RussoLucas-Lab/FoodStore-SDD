"""Tests para el módulo de pagos (RN-MP01, RN-MP02)."""

import hashlib
import hmac
import json
import os
import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.modules.pagos.model import FormaPago, Pago
from app.modules.pedidos.model import EstadoPedido, Pedido
from app.modules.productos.model import Producto
from app.modules.direcciones.model import Direccion
from app.modules.usuarios.model import Usuario
from app.modules.roles.model import UsuarioRol
from app.core.security import hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def login_client(client: TestClient) -> dict:
    resp = client.post("/api/v1/auth/login", json={"email": "pagos_client@test.com", "password": "Client1234!"})
    assert resp.status_code == 200, f"Login fallido: {resp.json()}"
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def setup_pagos(session: Session):
    """Configura el entorno completo para tests de pagos."""
    # Estados de pedido
    for codigo, orden, terminal in [
        ("PENDIENTE", 1, False),
        ("CONFIRMADO", 2, False),
        ("CANCELADO", 6, True),
    ]:
        session.merge(EstadoPedido(codigo=codigo, descripcion=codigo, orden=orden, es_terminal=terminal))

    # Formas de pago
    session.merge(FormaPago(codigo="MERCADOPAGO", descripcion="MercadoPago", habilitado=True))

    # Usuario CLIENT
    usuario = Usuario(
        nombre="Pagos",
        apellido="Test",
        email="pagos_client@test.com",
        password_hash=hash_password("Client1234!"),
        activo=True,
    )
    session.add(usuario)
    session.flush()
    session.add(UsuarioRol(usuario_id=usuario.id, rol_codigo="CLIENT"))

    # Producto con stock
    producto = Producto(
        nombre="Producto Pago",
        descripcion="Para tests",
        precio_base=Decimal("200.00"),
        stock_cantidad=10,
        disponible=True,
    )
    session.add(producto)
    session.flush()

    # Dirección del usuario
    direccion = Direccion(
        usuario_id=usuario.id,
        calle="Av. Test",
        numero="100",
        ciudad="Buenos Aires",
        provincia="CABA",
        codigo_postal="C1000",
        es_principal=True,
    )
    session.add(direccion)
    session.commit()
    session.refresh(usuario)
    session.refresh(producto)
    session.refresh(direccion)

    return {
        "usuario_id": usuario.id,
        "producto_id": producto.id,
        "direccion_id": direccion.id,
    }


def _crear_pedido(client: TestClient, setup_pagos: dict, headers: dict) -> int:
    """Crea un pedido PENDIENTE y retorna su ID."""
    body = {
        "direccion_id": setup_pagos["direccion_id"],
        "forma_pago_codigo": "MERCADOPAGO",
        "items": [{"producto_id": setup_pagos["producto_id"], "cantidad": 1}],
    }
    resp = client.post("/api/v1/pedidos", json=body, headers=headers)
    assert resp.status_code == 201, f"Error creando pedido: {resp.json()}"
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Tests: POST /api/v1/pagos/crear
# ---------------------------------------------------------------------------

class TestCrearPreferencia:
    def test_crear_preferencia_exitosa(
        self,
        client: TestClient,
        setup_pagos: dict,
    ):
        """Test creación exitosa de preferencia (RN-MP01)."""
        headers = login_client(client)
        pedido_id = _crear_pedido(client, setup_pagos, headers)

        resp = client.post("/api/v1/pagos/crear", json={"pedido_id": pedido_id}, headers=headers)
        assert resp.status_code == 201, resp.json()

        data = resp.json()
        assert "preference_id" in data
        assert "init_point" in data
        assert data["preference_id"] != ""

    def test_idempotencia_crear_preferencia(
        self,
        client: TestClient,
        setup_pagos: dict,
    ):
        """Test que segunda llamada devuelve la misma preferencia (idempotencia)."""
        headers = login_client(client)
        pedido_id = _crear_pedido(client, setup_pagos, headers)

        # Primera llamada
        resp1 = client.post("/api/v1/pagos/crear", json={"pedido_id": pedido_id}, headers=headers)
        assert resp1.status_code == 201, resp1.json()
        pref_id_1 = resp1.json()["preference_id"]

        # Segunda llamada — debe devolver la misma preferencia
        resp2 = client.post("/api/v1/pagos/crear", json={"pedido_id": pedido_id}, headers=headers)
        assert resp2.status_code in (200, 201), resp2.json()
        pref_id_2 = resp2.json()["preference_id"]

        assert pref_id_1 == pref_id_2

    def test_pedido_no_existe_retorna_404(
        self,
        client: TestClient,
        setup_pagos: dict,
    ):
        """Test que pedido inexistente retorna 404."""
        headers = login_client(client)

        resp = client.post("/api/v1/pagos/crear", json={"pedido_id": 99999}, headers=headers)
        assert resp.status_code == 404
        assert resp.json()["code"] == "PEDIDO_NOT_FOUND"

    def test_pedido_no_en_pendiente_retorna_409(
        self,
        client: TestClient,
        session: Session,
        setup_pagos: dict,
    ):
        """Test que pedido no en PENDIENTE retorna 409."""
        headers = login_client(client)
        pedido_id = _crear_pedido(client, setup_pagos, headers)

        # Cambiar estado a CONFIRMADO directamente en BD
        pedido = session.get(Pedido, pedido_id)
        pedido.estado_codigo = "CONFIRMADO"
        session.add(pedido)
        session.commit()

        resp = client.post("/api/v1/pagos/crear", json={"pedido_id": pedido_id}, headers=headers)
        assert resp.status_code == 409
        assert resp.json()["code"] == "PEDIDO_ESTADO_INVALIDO"


# ---------------------------------------------------------------------------
# Tests: POST /api/v1/pagos/webhook
# ---------------------------------------------------------------------------

class TestWebhookIPN:
    def test_webhook_approved_confirma_pedido(
        self,
        client: TestClient,
        session: Session,
        setup_pagos: dict,
    ):
        """Test webhook aprobado transiciona pedido a CONFIRMADO."""
        headers = login_client(client)
        pedido_id = _crear_pedido(client, setup_pagos, headers)

        # Crear preferencia primero
        client.post("/api/v1/pagos/crear", json={"pedido_id": pedido_id}, headers=headers)

        # Simular webhook con status approved
        mp_payment_id = f"MP-{uuid.uuid4().hex[:8]}"
        payload = {
            "topic": "payment",
            "type": "payment",
            "data": {"id": mp_payment_id, "external_reference": str(pedido_id)},
        }
        raw_body = json.dumps(payload).encode("utf-8")

        # Mock del SDK para retornar status approved
        with patch.object(
            __import__("app.modules.pagos.service", fromlist=["PagoService"]).PagoService,
            "_get_payment_status_from_mp",
            return_value="approved",
        ):
            resp = client.post(
                "/api/v1/pagos/webhook",
                content=raw_body,
                headers={"Content-Type": "application/json"},
            )

        assert resp.status_code == 200

        # Verificar que el pedido pasó a CONFIRMADO
        session.expire_all()
        pedido = session.get(Pedido, pedido_id)
        assert pedido.estado_codigo == "CONFIRMADO"

    def test_webhook_firma_invalida_retorna_400(
        self,
        client: TestClient,
        setup_pagos: dict,
    ):
        """Test webhook con firma inválida retorna 400 (RN-MP02)."""
        # Configurar WEBHOOK_SECRET para activar la validación
        import app.core.config as config_module

        original_secret = config_module.settings.WEBHOOK_SECRET
        config_module.settings.WEBHOOK_SECRET = "test-secret-12345"

        try:
            payload = {"topic": "payment", "data": {"id": "MP-123"}}
            raw_body = json.dumps(payload).encode("utf-8")

            resp = client.post(
                "/api/v1/pagos/webhook",
                content=raw_body,
                headers={
                    "Content-Type": "application/json",
                    "x-signature": "ts=1234,v1=firma-invalida-xxxxxxxxxx",
                },
            )

            assert resp.status_code == 400
            assert resp.json()["code"] == "INVALID_SIGNATURE"
        finally:
            config_module.settings.WEBHOOK_SECRET = original_secret

    def test_webhook_idempotencia_no_reprocesa(
        self,
        client: TestClient,
        session: Session,
        setup_pagos: dict,
    ):
        """Test que IPN duplicado no reprocesa el pago (idempotencia)."""
        headers = login_client(client)
        pedido_id = _crear_pedido(client, setup_pagos, headers)

        # Crear pago con mp_payment_id ya marcado como APROBADO
        pago = Pago(
            pedido_id=pedido_id,
            forma_pago_codigo="MERCADOPAGO",
            monto=Decimal("200.00"),
            estado="APROBADO",
            mp_payment_id="MP-DUPLICATE-123",
            idempotency_key=str(uuid.uuid4()),
        )
        session.add(pago)
        session.commit()

        # Enviar IPN duplicado
        payload = {
            "topic": "payment",
            "data": {"id": "MP-DUPLICATE-123"},
        }
        raw_body = json.dumps(payload).encode("utf-8")

        resp = client.post(
            "/api/v1/pagos/webhook",
            content=raw_body,
            headers={"Content-Type": "application/json"},
        )

        assert resp.status_code == 200
        # El pedido debe seguir en PENDIENTE (no se reprocesó)
        session.expire_all()
        pedido = session.get(Pedido, pedido_id)
        assert pedido.estado_codigo == "PENDIENTE"

    def test_webhook_topic_distinto_ignorado(
        self,
        client: TestClient,
        setup_pagos: dict,
    ):
        """Test que topic diferente a payment no procesa nada."""
        payload = {"topic": "merchant_order", "data": {"id": "MO-123"}}
        raw_body = json.dumps(payload).encode("utf-8")

        resp = client.post(
            "/api/v1/pagos/webhook",
            content=raw_body,
            headers={"Content-Type": "application/json"},
        )

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Tests: GET /api/v1/pagos/{pedido_id}
# ---------------------------------------------------------------------------

class TestGetPago:
    def test_get_pago_existente(
        self,
        client: TestClient,
        session: Session,
        setup_pagos: dict,
    ):
        """Test consulta de pago existente."""
        headers = login_client(client)
        pedido_id = _crear_pedido(client, setup_pagos, headers)
        client.post("/api/v1/pagos/crear", json={"pedido_id": pedido_id}, headers=headers)

        resp = client.get(f"/api/v1/pagos/{pedido_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["pedido_id"] == pedido_id
        assert "estado_pago" in data

    def test_get_pago_no_existente_retorna_404(
        self,
        client: TestClient,
        setup_pagos: dict,
    ):
        """Test que pedido sin pago retorna 404."""
        headers = login_client(client)
        pedido_id = _crear_pedido(client, setup_pagos, headers)

        resp = client.get(f"/api/v1/pagos/{pedido_id}", headers=headers)
        assert resp.status_code == 404
        assert resp.json()["code"] == "PAGO_NOT_FOUND"
