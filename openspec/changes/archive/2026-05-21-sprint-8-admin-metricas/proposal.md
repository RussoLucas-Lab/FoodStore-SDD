## Why

Sprint 8 cierra el backlog del proyecto completando el panel de administración: gestión de usuarios con RBAC, métricas del negocio con gráficos, control de stock y configuración del sistema. Es la última épica antes de la entrega final (CE-01 a CE-14).

## What Changes

- **Módulo `admin` backend**: nuevos endpoints de gestión de usuarios (listar, editar, asignar roles, activar/desactivar) y endpoints de métricas agregadas (KPIs, ventas por período, ranking de productos, distribución de estados de pedido).
- **Dashboard frontend**: componente `Dashboard` con gráficos recharts (`LineChart` ventas, `BarChart` productos top, `PieChart` estados de pedido).
- **UsuariosCRUD frontend**: tabla con búsqueda, edición inline de roles y toggle de estado activo.
- **StockTable frontend**: tabla de gestión de stock y disponibilidad de productos (admin/STOCK).
- **ConfiguracionPanel frontend**: panel key-value de configuración del sistema (US-060).
- **Catálogo admin completo**: endpoint y vista que incluyen productos con soft-delete.
- `productos-backend` **BREAKING**: nuevo query param `include_deleted=true` solo para ADMIN.

## Capabilities

### New Capabilities
- `admin-usuarios-backend`: Endpoints de gestión de usuarios — `GET /admin/usuarios`, `PUT /admin/usuarios/{id}`, `PATCH /admin/usuarios/{id}/roles`, `PATCH /admin/usuarios/{id}/activar` con validaciones RBAC (RN-RB03, RN-RB04).
- `admin-metricas-backend`: Endpoints de métricas agregadas — `GET /admin/metricas/resumen`, `/ventas`, `/productos-top`, `/pedidos-por-estado`.
- `admin-panel-frontend`: Feature `admin` completa — `Dashboard` (recharts), `UsuariosCRUD`, `StockTable`, `ConfiguracionPanel` y catálogo admin con soft-deleted.

### Modified Capabilities
- `productos-backend`: Se agrega visibilidad de productos con soft-delete para ADMIN mediante `include_deleted=true`.

## Impact

- **Backend**: nuevo módulo `app/modules/admin/` (router, service, repository, schemas). Queries de agregación sobre `Pedido`, `DetallePedido`, `Producto`, `Usuario`.
- **Frontend**: `features/admin/` completado — nuevos componentes, hooks TanStack Query para métricas y usuarios.
- **Dependencias**: `recharts` ya declarado en stack; sin nuevas dependencias externas.
- **Sin impacto en auth ni en módulos de cliente** (carrito, checkout, pedidos de cliente).
