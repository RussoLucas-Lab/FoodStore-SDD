"""7.5 — Idempotencia: dos requests con misma key → 1 pedido."""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.modules.pedidos.model import Pedido
from .conftest import client_headers


class TestCrearPedidoIdempotency:
    def test_misma_key_no_duplica(
        self,
        client: TestClient,
        session: Session,
        client_pedidos,
        estados_pedido,
        formas_pago,
        producto_disponible,
        direccion_cliente,
    ):
        headers = client_headers(client)
        body = {
            "direccion_id": direccion_cliente.id,
            "forma_pago_codigo": "MERCADOPAGO",
            "items": [{"producto_id": producto_disponible.id, "cantidad": 1}],
        }
        key = "test-idempotency-key-12345"

        resp1 = client.post("/api/v1/pedidos", json=body, headers={**headers, "Idempotency-Key": key})
        assert resp1.status_code == 201

        resp2 = client.post("/api/v1/pedidos", json=body, headers={**headers, "Idempotency-Key": key})
        assert resp2.status_code == 201

        # Mismo ID en ambas respuestas
        assert resp1.json()["id"] == resp2.json()["id"]

        # Solo 1 fila en BD
        pedidos = session.exec(
            select(Pedido).where(Pedido.usuario_id == client_pedidos)
        ).all()
        assert len(pedidos) == 1

    def test_sin_key_crea_normalmente(
        self,
        client: TestClient,
        session: Session,
        client_pedidos,
        estados_pedido,
        formas_pago,
        producto_disponible,
        direccion_cliente,
    ):
        headers = client_headers(client)
        body = {
            "direccion_id": direccion_cliente.id,
            "forma_pago_codigo": "EFECTIVO",
            "items": [{"producto_id": producto_disponible.id, "cantidad": 1}],
        }
        resp = client.post("/api/v1/pedidos", json=body, headers=headers)
        assert resp.status_code == 201

        pedido = session.exec(select(Pedido).where(Pedido.usuario_id == client_pedidos)).first()
        assert pedido is not None
        assert pedido.idempotency_key is None
