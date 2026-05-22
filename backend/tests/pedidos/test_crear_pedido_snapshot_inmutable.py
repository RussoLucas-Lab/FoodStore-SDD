"""7.7 — Snapshots inmutables tras cambios al producto y dirección."""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.modules.pedidos.model import DetallePedido, Pedido
from .conftest import client_headers


class TestCrearPedidoSnapshotInmutable:
    def test_snapshot_precio_nombre_inmutable(
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
        resp = client.post("/api/v1/pedidos", json=body, headers=headers)
        assert resp.status_code == 201

        pedido_id = resp.json()["id"]

        # Modificar precio y nombre del producto (re-fetch por ID, el objeto original es transient)
        from app.modules.productos.model import Producto
        p = session.get(Producto, producto_disponible.id)
        p.precio_base = Decimal("999.99")
        p.nombre = "NOMBRE MODIFICADO"
        session.commit()

        # El snapshot debe mantener los valores originales
        detalle = session.exec(
            select(DetallePedido).where(DetallePedido.pedido_id == pedido_id)
        ).first()
        assert detalle is not None
        assert detalle.precio_snapshot == Decimal("150.00")
        assert detalle.nombre_snapshot == "Pizza Test"

    def test_snapshot_direccion_inmutable_tras_soft_delete(
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
        resp = client.post("/api/v1/pedidos", json=body, headers=headers)
        assert resp.status_code == 201

        pedido_id = resp.json()["id"]

        # Soft delete de la dirección (re-fetch por ID, el objeto original es transient)
        from datetime import datetime, timezone
        from app.modules.direcciones.model import Direccion
        d = session.get(Direccion, direccion_cliente.id)
        d.deleted_at = datetime.now(timezone.utc)
        session.commit()

        # El snapshot del pedido debe mantenerse intacto
        pedido = session.get(Pedido, pedido_id)
        assert pedido is not None
        assert pedido.direccion_snapshot["calle"] == "Av. Corrientes"
        assert pedido.direccion_snapshot["ciudad"] == "Buenos Aires"
