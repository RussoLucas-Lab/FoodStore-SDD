"""7.3 — Rollback: stock insuficiente en tercer item no deja nada en BD."""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.modules.pedidos.model import DetallePedido, HistorialEstadoPedido, Pedido
from app.modules.productos.model import Producto
from .conftest import client_headers


class TestCrearPedidoRollback:
    def test_rollback_stock_insuficiente_tercer_item(
        self,
        client: TestClient,
        session: Session,
        client_pedidos,
        estados_pedido,
        formas_pago,
        producto_disponible,
        direccion_cliente,
    ):
        p2 = Producto(nombre="Prod2", descripcion="", precio_base=Decimal("50.00"), stock_cantidad=5, disponible=True)
        p3_sin_stock = Producto(nombre="Prod3 Sin Stock", descripcion="", precio_base=Decimal("30.00"), stock_cantidad=1, disponible=True)
        session.add(p2)
        session.add(p3_sin_stock)
        session.commit()
        session.refresh(p2)
        session.refresh(p3_sin_stock)
        p2_id = p2.id
        p3_sin_stock_id = p3_sin_stock.id

        headers = client_headers(client)
        body = {
            "direccion_id": direccion_cliente.id,
            "forma_pago_codigo": "MERCADOPAGO",
            "items": [
                {"producto_id": producto_disponible.id, "cantidad": 1},
                {"producto_id": p2_id, "cantidad": 1},
                {"producto_id": p3_sin_stock_id, "cantidad": 99},  # stock insuficiente
            ],
        }
        resp = client.post("/api/v1/pedidos", json=body, headers=headers)
        assert resp.status_code == 409
        assert resp.json()["code"] == "STOCK_INSUFICIENTE"

        # No debe haber ningún pedido creado
        pedidos = session.exec(select(Pedido).where(Pedido.usuario_id == client_pedidos)).all()
        assert len(pedidos) == 0
