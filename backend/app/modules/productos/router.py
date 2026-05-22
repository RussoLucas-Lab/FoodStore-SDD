"""Router de Producto — endpoints REST bajo /api/v1/productos."""

from typing import List, Optional

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials

from app.core.security import bearer_scheme, decode_token, get_current_user, require_role
from app.core.uow import UnitOfWork
from app.modules.productos.schemas import (
    DisponibilidadUpdate,
    ProductoCreate,
    ProductoListResponse,
    ProductoRead,
    ProductoUpdate,
    StockUpdate,
)
from app.modules.ingredientes.schemas import IngredienteRead
from app.modules.productos.service import producto_service

router = APIRouter()


@router.get("/", response_model=ProductoListResponse)
def listar_productos(
    page: int = 1,
    size: int = 20,
    categoria_id: Optional[int] = None,
    q: Optional[str] = None,
    excluir_alergenos: Optional[bool] = None,
    disponible: Optional[bool] = None,
    include_deleted: bool = False,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """Lista productos con filtros opcionales. Público. include_deleted solo para ADMIN."""
    # Resolver el rol del usuario actual (si está autenticado)
    user_rol: Optional[str] = None
    if credentials is not None:
        try:
            payload = decode_token(credentials.credentials, "access")
            user_rol = payload.get("rol")
        except Exception:
            user_rol = None

    with UnitOfWork() as uow:
        return producto_service.list_all(
            uow,
            page=page,
            size=size,
            categoria_id=categoria_id,
            q=q,
            excluir_alergenos=excluir_alergenos,
            disponible=disponible,
            include_deleted=include_deleted if user_rol == "ADMIN" else False,
        )


@router.get("/{producto_id}", response_model=ProductoRead)
def obtener_producto(producto_id: int):
    """Obtiene un producto por ID. Público."""
    with UnitOfWork() as uow:
        return producto_service.get_by_id(uow, producto_id)


@router.post(
    "/",
    response_model=ProductoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(["ADMIN", "STOCK"]))],
)
def crear_producto(body: ProductoCreate):
    """Crea un nuevo producto. Solo ADMIN o STOCK."""
    with UnitOfWork() as uow:
        return producto_service.create(uow, body)


@router.put(
    "/{producto_id}",
    response_model=ProductoRead,
    dependencies=[Depends(require_role(["ADMIN", "STOCK"]))],
)
def actualizar_producto(producto_id: int, body: ProductoUpdate):
    """Actualiza un producto existente. Solo ADMIN o STOCK."""
    with UnitOfWork() as uow:
        return producto_service.update(uow, producto_id, body)


@router.patch(
    "/{producto_id}/disponibilidad",
    response_model=ProductoRead,
    dependencies=[Depends(require_role(["ADMIN", "STOCK"]))],
)
def patch_disponibilidad(producto_id: int, body: DisponibilidadUpdate):
    """Actualiza la disponibilidad de un producto. Solo ADMIN o STOCK."""
    with UnitOfWork() as uow:
        return producto_service.patch_disponibilidad(uow, producto_id, body)


@router.patch(
    "/{producto_id}/stock",
    response_model=ProductoRead,
    dependencies=[Depends(require_role(["ADMIN", "STOCK"]))],
)
def patch_stock(producto_id: int, body: StockUpdate):
    """Actualiza el stock de un producto. Solo ADMIN o STOCK."""
    with UnitOfWork() as uow:
        return producto_service.patch_stock(uow, producto_id, body)


@router.delete(
    "/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def eliminar_producto(producto_id: int):
    """Elimina (soft delete) un producto. Solo ADMIN."""
    with UnitOfWork() as uow:
        producto_service.delete(uow, producto_id)


@router.get("/{producto_id}/ingredientes", response_model=List[IngredienteRead])
def listar_ingredientes_producto(producto_id: int):
    """Lista los ingredientes de un producto. Público."""
    with UnitOfWork() as uow:
        return producto_service.get_ingredientes(uow, producto_id)
