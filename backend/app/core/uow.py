"""Unit of Work — gestiona transacciones de BD de forma automática."""

from typing import Optional
from sqlmodel import Session
from fastapi import HTTPException
import app.db.database as _db_module


class UnitOfWork:
    """Context manager que garantiza atomicidad en las operaciones de BD.

    Usage:
        with UnitOfWork() as uow:
            result = service.hacer_algo(uow, datos)
            return result

    El commit se hace automáticamente al salir del bloque sin excepciones.
    En caso de excepción, se hace rollback automático.

    IMPORTANTE: Ningún Service debe llamar session.commit() directamente.
    """

    session: Session

    # Repositorios (instanciados en __enter__ cuando los modelos estén disponibles)
    # Se importan en __enter__ para evitar imports circulares

    def __enter__(self) -> "UnitOfWork":
        self.session = _db_module.SessionLocal()
        self._init_repositories()
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> None:
        if exc_type and not issubclass(exc_type, HTTPException):
            # Solo rollback ante errores inesperados; HTTPException es control
            # flow esperado (el servicio ya hizo flush de lo necesario).
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()

    def _init_repositories(self) -> None:
        """Instancia todos los repositorios con la sesión actual."""
        # Imports locales para evitar imports circulares al momento de carga
        from app.modules.usuarios.repository import UsuarioRepository
        from app.modules.roles.repository import RolRepository
        from app.modules.auth.repository import RefreshTokenRepository
        from app.modules.categorias.repository import CategoriaRepository
        from app.modules.ingredientes.repository import IngredienteRepository
        from app.modules.productos.repository import ProductoRepository
        from app.modules.direcciones.repository import DireccionRepository
        from app.modules.pedidos.repository import (
            PedidoRepository,
            DetallePedidoRepository,
            HistorialEstadoPedidoRepository,
            FormaPagoRepository,
        )
        from app.modules.pagos.repository import PagoRepository
        from app.modules.admin.repository import AdminRepository

        self.usuarios = UsuarioRepository(self.session)
        self.roles = RolRepository(self.session)
        self.refresh_tokens = RefreshTokenRepository(self.session)
        self.categorias = CategoriaRepository(self.session)
        self.ingredientes = IngredienteRepository(self.session)
        self.productos = ProductoRepository(self.session)
        self.direcciones = DireccionRepository(self.session)
        self.pedidos = PedidoRepository(self.session)
        self.detalle_pedido = DetallePedidoRepository(self.session)
        self.historial_pedido = HistorialEstadoPedidoRepository(self.session)
        self.formas_pago = FormaPagoRepository(self.session)
        self.pagos = PagoRepository(self.session)
        self.admin = AdminRepository(self.session)

    def flush(self) -> None:
        """Envía los cambios pendientes a la BD sin hacer commit."""
        self.session.flush()


def get_uow():
    """Generador FastAPI que provee un UnitOfWork para la duración del request."""
    with UnitOfWork() as uow:
        yield uow
