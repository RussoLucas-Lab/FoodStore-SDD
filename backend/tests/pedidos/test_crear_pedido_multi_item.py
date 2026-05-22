"""7.2 — Multi-item: 3 items con total correcto."""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.modules.pedidos.model import DetallePedido, Pedido
from app.modules.productos.model import Producto
from .conftest import client_headers


class TestCrearPedidoMultiItem:
    def test_tres_items_total_correcto(
        self,
        client: TestClient,
        session: Session,
        client_pedidos,
        estados_pedido,
        formas_pago,
        producto_disponible,
        direccion_cliente,
    ):
        # Crear 2 productos adicionales
        p2 = Producto(nombre="Empanada", descripcion="", precio_base=Decimal("80.50"), stock_cantidad=5, disponible=True)
        p3 = Producto(nombre="Coca Cola", descripcion="", precio_base=Decimal("50.00"), stock_cantidad=10, disponible=True)
        session.add(p2)
        session.add(p3)
        session.commit()
        session.refresh(p2)
        session.refresh(p3)
        p2_id = p2.id
        p3_id = p3.id

        headers = client_headers(client)
        body = {
            "direccion_id": direccion_cliente.id,
            "forma_pago_codigo": "MERCADOPAGO",
            "items": [
                {"producto_id": producto_disponible.id, "cantidad": 2},  # 150 * 2 = 300
                {"producto_id": p2_id, "cantidad": 1},                   # 80.50 * 1 = 80.50
                {"producto_id": p3_id, "cantidad": 3},                   # 50 * 3 = 150
            ],
        }
        resp = client.post("/api/v1/pedidos", json=body, headers=headers)
        assert resp.status_code == 201, resp.json()

        data = resp.json()
        assert Decimal(str(data["total"])) == Decimal("530.50")

        detalles = session.exec(
            select(DetallePedido).where(DetallePedido.pedido_id == data["id"])
        ).all()
        assert len(detalles) == 3
