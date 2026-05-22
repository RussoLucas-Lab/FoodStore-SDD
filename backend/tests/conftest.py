"""Configuración de pytest — fixtures para tests de integración.

Las variables de entorno deben setearse ANTES de importar cualquier módulo de la app
porque config.py instancia Settings() al nivel de módulo.
"""

import os

# --- Env vars mínimas para que Settings no falle al importarse ---
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-para-pytest-min32chars")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# Ahora sí importamos módulos de la app
from app.core.security import hash_password
from app.modules.roles.model import Rol, UsuarioRol
from app.modules.usuarios.model import Usuario

# Importar TODOS los modelos para que SQLAlchemy pueda resolver todas las
# relaciones (forward references) al inicializar los mappers.
import app.modules.auth.model  # noqa: F401  (RefreshToken)
import app.modules.direcciones.model  # noqa: F401  (Direccion)
import app.modules.categorias.model  # noqa: F401  (Categoria)
import app.modules.ingredientes.model  # noqa: F401  (Ingrediente)
import app.modules.productos.model  # noqa: F401  (Producto, ProductoCategoria, ProductoIngrediente)
import app.modules.pedidos.model  # noqa: F401  (EstadoPedido, Pedido, DetallePedido, HistorialEstadoPedido)
import app.modules.pagos.model  # noqa: F401  (FormaPago, Pago)

# ---------------------------------------------------------------------------
# Motor SQLite en memoria para tests
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Limpia el estado del rate limiter antes de cada test para evitar
    que los contadores persistan entre tests y disparen 429 prematuramente."""
    from app.core.limiter import limiter
    limiter._storage.reset()
    yield
    limiter._storage.reset()


@pytest.fixture(name="session", scope="function")
def session_fixture():
    """Sesión de BD limpia para cada test (SQLite in-memory)."""
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        _seed_test_data(session)
        yield session
    SQLModel.metadata.drop_all(test_engine)


def _seed_test_data(session: Session) -> None:
    """Datos mínimos de prueba: roles base."""
    for codigo, desc in [
        ("ADMIN", "Administrador"),
        ("CLIENT", "Cliente"),
        ("STOCK", "Stock"),
        ("PEDIDOS", "Pedidos"),
    ]:
        session.add(Rol(codigo=codigo, descripcion=desc))
    session.commit()


@pytest.fixture(name="client", scope="function")
def client_fixture(session: Session):
    """TestClient con BD de test (SQLite) inyectada vía override."""
    import app.db.database as db_module
    from app.core.uow import UnitOfWork
    from app.main import app

    # Guardar originales
    original_engine = db_module.engine
    original_session_local = db_module.SessionLocal

    # Parchear engine y SessionLocal para que UoW use SQLite
    db_module.engine = test_engine

    class _PatchedSessionLocal:
        def __call__(self):
            return session

    db_module.SessionLocal = _PatchedSessionLocal()  # type: ignore[assignment]

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    # Restaurar originales
    db_module.engine = original_engine
    db_module.SessionLocal = original_session_local


@pytest.fixture
def admin_user(session: Session) -> Usuario:
    """Crea y retorna un usuario ADMIN en la BD de test."""
    usuario = Usuario(
        nombre="Admin",
        apellido="Test",
        email="admin@test.com",
        password_hash=hash_password("Admin1234!"),
        activo=True,
    )
    session.add(usuario)
    session.flush()
    session.add(UsuarioRol(usuario_id=usuario.id, rol_codigo="ADMIN"))
    session.commit()
    session.refresh(usuario)
    return usuario


@pytest.fixture
def client_user(session: Session) -> Usuario:
    """Crea y retorna un usuario CLIENT en la BD de test."""
    usuario = Usuario(
        nombre="Client",
        apellido="Test",
        email="client@test.com",
        password_hash=hash_password("Client1234!"),
        activo=True,
    )
    session.add(usuario)
    session.flush()
    session.add(UsuarioRol(usuario_id=usuario.id, rol_codigo="CLIENT"))
    session.commit()
    session.refresh(usuario)
    return usuario
