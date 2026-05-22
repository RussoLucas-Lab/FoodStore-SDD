"""Schemas Pydantic para el módulo de administración."""

import math
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class UsuarioAdminRead(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str
    activo: bool
    roles: List[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class UsuarioAdminUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[str] = None


class AsignarRolesRequest(BaseModel):
    roles: List[str]


class ActivarUsuarioRequest(BaseModel):
    activo: bool


class UsuariosListResponse(BaseModel):
    items: List[UsuarioAdminRead]
    total: int
    page: int
    size: int
    pages: int


class MetricasResumenResponse(BaseModel):
    total_pedidos: int
    ventas_mes: Decimal
    productos_activos: int
    usuarios_activos: int


class VentaItem(BaseModel):
    fecha: str
    total: Decimal


class VentasPorPeriodoResponse(BaseModel):
    periodo: str
    series: List[VentaItem]


class ProductoTopItem(BaseModel):
    producto_id: int
    nombre: str
    unidades_vendidas: int
    total_generado: Decimal


class ProductosTopResponse(BaseModel):
    items: List[ProductoTopItem]


class PedidosPorEstadoItem(BaseModel):
    estado: str
    cantidad: int


class PedidosPorEstadoResponse(BaseModel):
    items: List[PedidosPorEstadoItem]
