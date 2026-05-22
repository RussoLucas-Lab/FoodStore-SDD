"""7.8 — GET /formas-pago: solo devuelve habilitadas, requiere auth."""

import pytest
from fastapi.testclient import TestClient

from .conftest import client_headers


FORMAS_PAGO_URL = "/api/v1/pedidos/formas-pago"


class TestFormasPago:
    def test_sin_auth_retorna_401(self, client: TestClient, formas_pago):
        resp = client.get(FORMAS_PAGO_URL)
        assert resp.status_code == 401

    def test_autenticado_retorna_solo_habilitadas(
        self,
        client: TestClient,
        client_pedidos,
        formas_pago,
    ):
        headers = client_headers(client)
        resp = client.get(FORMAS_PAGO_URL, headers=headers)
        assert resp.status_code == 200

        data = resp.json()
        codigos = [f["codigo"] for f in data]
        assert "MERCADOPAGO" in codigos
        assert "EFECTIVO" in codigos
        assert "DESHABILITADA" not in codigos

    def test_lista_vacia_si_todas_deshabilitadas(
        self,
        client: TestClient,
        session,
        client_pedidos,
        formas_pago,
    ):
        # Deshabilitar todas
        from app.modules.pagos.model import FormaPago
        from sqlmodel import select
        todas = session.exec(select(FormaPago)).all()
        for f in todas:
            f.habilitado = False
        session.commit()

        headers = client_headers(client)
        resp = client.get(FORMAS_PAGO_URL, headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []
