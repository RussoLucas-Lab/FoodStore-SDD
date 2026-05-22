"""Fixtures específicas para tests de pedidos.

NOTA: Después de cualquier request HTTP, la sesión de test puede quedar cerrada
(el UoW del endpoint cierra la sesión compartida). Por eso los IDs de fixtures
se capturan ANTES de la primera request y se usan como enteros simples.
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import make_transient
from sqlmodel import Session

from app.core.security import hash_password
from app.modules.usuarios.model import Usuario
from app.modules.roles.model import UsuarioRol
from app.modules.categorias.model import Categoria
from app.modules.productos.model import Producto
from app.modules.direcciones.model import Direccion
from app.modules.pedidos.model import EstadoPedido
from app.modules.pagos.model import FormaPago


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def login(client: TestClient, email: str, password: str) -> dict:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login fallido: {resp.json()}"
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def client_headers(client: TestClient) -> dict:
    return login(client, "client_pedidos@test.com", "Client1234!")


# ---------------------------------------------------------------------------
# Fixtures base
# ---------------------------------------------------------------------------

@pytest.fixture
def estados_pedido(session: Session):
    """Crea los estados de pedido necesarios."""
    estados = [
        EstadoPedido(codigo="PENDIENTE", descripcion="Pendiente", orden=1, es_terminal=False),
        EstadoPedido(codigo="CONFIRMADO", descripcion="Confirmado", orden=2, es_terminal=False),
        EstadoPedido(codigo="CANCELADO", descripcion="Cancelado", orden=6, es_terminal=True),
    ]
    for e in estados:
        session.merge(e)
    session.commit()


@pytest.fixture
def formas_pago(session: Session):
    """Crea las formas de pago."""
    formas = [
        FormaPago(codigo="MERCADOPAGO", descripcion="MercadoPago", habilitado=True),
        FormaPago(codigo="EFECTIVO", descripcion="Efectivo", habilitado=True),
        FormaPago(codigo="DESHABILITADA", descripcion="Deshabilitada", habilitado=False),
    ]
    for f in formas:
        session.merge(f)
    session.commit()


@pytest.fixture
def client_pedidos(session: Session) -> int:
    """Crea un usuario CLIENT y retorna su ID (int, seguro post-commit)."""
    usuario = Usuario(
        nombre="Cliente",
        apellido="Pedidos",
        email="client_pedidos@test.com",
        password_hash=hash_password("Client1234!"),
        activo=True,
    )
    session.add(usuario)
    session.flush()
    uid = usuario.id
    session.add(UsuarioRol(usuario_id=uid, rol_codigo="CLIENT"))
    session.commit()
    return uid


@pytest.fixture
def producto_disponible(session: Session) -> Producto:
    """Producto con stock disponible. Retorna objeto con make_transient."""
    producto = Producto(
        nombre="Pizza Test",
        descripcion="Una pizza",
        precio_base=Decimal("150.00"),
        stock_cantidad=10,
        disponible=True,
    )
    session.add(producto)
    session.commit()
    session.refresh(producto)
    make_transient(producto)
    return producto


@pytest.fixture
def producto_sin_stock(session: Session) -> Producto:
    """Producto sin stock."""
    producto = Producto(
        nombre="Sin Stock",
        descripcion="Sin stock",
        precio_base=Decimal("100.00"),
        stock_cantidad=0,
        disponible=True,
    )
    session.add(producto)
    session.commit()
    session.refresh(producto)
    make_transient(producto)
    return producto


@pytest.fixture
def producto_no_disponible(session: Session) -> Producto:
    """Producto marcado como no disponible."""
    producto = Producto(
        nombre="No Disponible",
        descripcion="No disponible",
        precio_base=Decimal("80.00"),
        stock_cantidad=5,
        disponible=False,
    )
    session.add(producto)
    session.commit()
    session.refresh(producto)
    make_transient(producto)
    return producto


@pytest.fixture
def direccion_cliente(session: Session, client_pedidos: int) -> Direccion:
    """Dirección activa del cliente. Retorna objeto con make_transient."""
    dir_ = Direccion(
        usuario_id=client_pedidos,
        calle="Av. Corrientes",
        numero="1234",
        ciudad="Buenos Aires",
        provincia="CABA",
        codigo_postal="C1043",
        es_principal=True,
    )
    session.add(dir_)
    session.commit()
    session.refresh(dir_)
    make_transient(dir_)
    return dir_
