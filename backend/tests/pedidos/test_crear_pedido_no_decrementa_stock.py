"""7.6 — Stock no se decrementa al crear pedido (RN-FS03 difiere a Sprint 6)."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from .conftest import client_headers


class TestCrearPedidoNoDecrementaStock:
    def test_stock_sin_cambios_tras_crear(
        self,
        client: TestClient,
        session: Session,
        client_pedidos,
        estados_pedido,
        formas_pago,
        producto_disponible,
        direccion_cliente,
    ):
        stock_original = producto_disponible.stock_cantidad

        headers = client_headers(client)
        body = {
            "direccion_id": direccion_cliente.id,
            "forma_pago_codigo": "MERCADOPAGO",
            "items": [{"producto_id": producto_disponible.id, "cantidad": 3}],
        }
        resp = client.post("/api/v1/pedidos", json=body, headers=headers)
        assert resp.status_code == 201

        from app.modules.productos.model import Producto
        p = session.get(Producto, producto_disponible.id)
        assert p.stock_cantidad == stock_original
