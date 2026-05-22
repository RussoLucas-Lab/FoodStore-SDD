"""7.1 — Happy path: crear pedido con 1 item."""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.modules.pedidos.model import DetallePedido, HistorialEstadoPedido, Pedido
from .conftest import client_headers


class TestCrearPedidoHappy:
    def test_crear_pedido_un_item(
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
            "items": [{"producto_id": producto_disponible.id, "cantidad": 2}],
        }
        resp = client.post("/api/v1/pedidos", json=body, headers=headers)
        assert resp.status_code == 201, resp.json()

        data = resp.json()
        assert data["estado_codigo"] == "PENDIENTE"
        assert Decimal(str(data["total"])) == Decimal("300.00")
        assert data["id"] is not None

        # Verificar en BD
        pedido = session.get(Pedido, data["id"])
        assert pedido is not None
        assert pedido.estado_codigo == "PENDIENTE"
        assert pedido.forma_pago_codigo == "MERCADOPAGO"

        detalles = session.exec(
            select(DetallePedido).where(DetallePedido.pedido_id == pedido.id)
        ).all()
        assert len(detalles) == 1
        assert detalles[0].precio_snapshot == Decimal("150.00")
        assert detalles[0].nombre_snapshot == "Pizza Test"
        assert detalles[0].cantidad == 2

        historial = session.exec(
            select(HistorialEstadoPedido).where(HistorialEstadoPedido.pedido_id == pedido.id)
        ).all()
        assert len(historial) == 1
        assert historial[0].estado_desde is None
        assert historial[0].estado_hasta == "PENDIENTE"

    def test_sin_autenticacion_retorna_401(
        self,
        client: TestClient,
        estados_pedido,
        formas_pago,
    ):
        resp = client.post("/api/v1/pedidos", json={"direccion_id": 1, "forma_pago_codigo": "MERCADOPAGO", "items": []})
        assert resp.status_code == 401
