"""7.4 — Validaciones: todos los errores de negocio."""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlmodel import Session

from .conftest import client_headers


class TestCrearPedidoValidaciones:
    def _base_body(self, direccion_id: int, producto_id: int, cantidad: int = 1, forma_pago: str = "MERCADOPAGO") -> dict:
        return {
            "direccion_id": direccion_id,
            "forma_pago_codigo": forma_pago,
            "items": [{"producto_id": producto_id, "cantidad": cantidad}],
        }

    def test_carrito_vacio_retorna_400(
        self,
        client: TestClient,
        client_pedidos,
        estados_pedido,
        formas_pago,
        direccion_cliente,
    ):
        headers = client_headers(client)
        resp = client.post(
            "/api/v1/pedidos",
            json={"direccion_id": direccion_cliente.id, "forma_pago_codigo": "MERCADOPAGO", "items": []},
            headers=headers,
        )
        assert resp.status_code == 422  # Pydantic min_length validation

    def test_forma_pago_inexistente_retorna_400(
        self,
        client: TestClient,
        client_pedidos,
        estados_pedido,
        formas_pago,
        producto_disponible,
        direccion_cliente,
    ):
        headers = client_headers(client)
        body = self._base_body(direccion_cliente.id, producto_disponible.id, forma_pago="INEXISTENTE")
        resp = client.post("/api/v1/pedidos", json=body, headers=headers)
        assert resp.status_code == 400
        assert resp.json()["code"] == "FORMA_PAGO_NOT_FOUND"

    def test_forma_pago_deshabilitada_retorna_400(
        self,
        client: TestClient,
        client_pedidos,
        estados_pedido,
        formas_pago,
        producto_disponible,
        direccion_cliente,
    ):
        headers = client_headers(client)
        body = self._base_body(direccion_cliente.id, producto_disponible.id, forma_pago="DESHABILITADA")
        resp = client.post("/api/v1/pedidos", json=body, headers=headers)
        assert resp.status_code == 400
        assert resp.json()["code"] == "FORMA_PAGO_NOT_FOUND"

    def test_direccion_inexistente_retorna_404(
        self,
        client: TestClient,
        client_pedidos,
        estados_pedido,
        formas_pago,
        producto_disponible,
    ):
        headers = client_headers(client)
        body = self._base_body(99999, producto_disponible.id)
        resp = client.post("/api/v1/pedidos", json=body, headers=headers)
        assert resp.status_code == 404
        assert resp.json()["code"] == "DIRECCION_NOT_FOUND"

    def test_producto_inexistente_retorna_400(
        self,
        client: TestClient,
        client_pedidos,
        estados_pedido,
        formas_pago,
        direccion_cliente,
    ):
        headers = client_headers(client)
        body = self._base_body(direccion_cliente.id, 99999)
        resp = client.post("/api/v1/pedidos", json=body, headers=headers)
        assert resp.status_code == 400
        assert resp.json()["code"] == "PRODUCTO_NOT_FOUND"

    def test_producto_no_disponible_retorna_409(
        self,
        client: TestClient,
        client_pedidos,
        estados_pedido,
        formas_pago,
        producto_no_disponible,
        direccion_cliente,
    ):
        headers = client_headers(client)
        body = self._base_body(direccion_cliente.id, producto_no_disponible.id)
        resp = client.post("/api/v1/pedidos", json=body, headers=headers)
        assert resp.status_code == 409
        assert resp.json()["code"] == "PRODUCTO_NO_DISPONIBLE"

    def test_stock_insuficiente_retorna_409(
        self,
        client: TestClient,
        client_pedidos,
        estados_pedido,
        formas_pago,
        producto_sin_stock,
        direccion_cliente,
    ):
        headers = client_headers(client)
        body = self._base_body(direccion_cliente.id, producto_sin_stock.id, cantidad=5)
        resp = client.post("/api/v1/pedidos", json=body, headers=headers)
        assert resp.status_code == 409
        assert resp.json()["code"] == "STOCK_INSUFICIENTE"
