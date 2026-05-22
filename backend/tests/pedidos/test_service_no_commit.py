"""7.9 — Service no contiene session.commit() ni session.rollback()."""

import ast
import pathlib


def test_pedido_service_no_tiene_session_commit():
    service_path = pathlib.Path(__file__).parent.parent.parent / "app" / "modules" / "pedidos" / "service.py"
    source = service_path.read_text(encoding="utf-8")
    assert "session.commit()" not in source, "PedidoService NO debe llamar session.commit()"
    assert "session.rollback()" not in source, "PedidoService NO debe llamar session.rollback()"
    assert "session.close()" not in source, "PedidoService NO debe llamar session.close()"
