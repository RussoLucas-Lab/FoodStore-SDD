## 1. Backend — Módulo admin: estructura base

- [x] 1.1 Crear directorio `backend/app/modules/admin/` con archivos vacíos: `__init__.py`, `router.py`, `service.py`, `repository.py`, `schemas.py`
- [x] 1.2 Implementar `AdminRepository` en `repository.py` con inyección de sesión (patrón `BaseRepository`)
- [x] 1.3 Implementar `AdminService` en `service.py` — stateless, recibe UoW
- [x] 1.4 Registrar router en `app/main.py` con prefijo `/api/v1/admin` y tag `admin`

## 2. Backend — Schemas admin

- [x] 2.1 Crear `UsuarioAdminRead` (id, nombre, apellido, email, activo, roles: list[str], created_at)
- [x] 2.2 Crear `UsuarioAdminUpdate` (nombre, apellido, email — todos opcionales)
- [x] 2.3 Crear `AsignarRolesRequest` (roles: list[str])
- [x] 2.4 Crear `ActivarUsuarioRequest` (activo: bool)
- [x] 2.5 Crear `MetricasResumenResponse` (total_pedidos, ventas_mes, productos_activos, usuarios_activos)
- [x] 2.6 Crear `VentasPorPeriodoResponse` (periodo: str, series: list[{fecha, total}])
- [x] 2.7 Crear `ProductoTopItem` y `ProductosTopResponse` (lista de {producto_id, nombre, unidades_vendidas, total_generado})
- [x] 2.8 Crear `PedidosPorEstadoItem` y `PedidosPorEstadoResponse` (lista de {estado, cantidad})

## 3. Backend — Endpoints de gestión de usuarios

- [x] 3.1 Implementar `AdminRepository.list_usuarios(q, activo, page, size)` — query con filtros opcionales sobre tabla `Usuario` join `UsuarioRol`
- [x] 3.2 Implementar `AdminRepository.get_usuario_by_id(id)` — con roles precargados
- [x] 3.3 Implementar `AdminRepository.update_usuario(id, data)` — actualiza nombre, apellido, email; valida unicidad de email
- [x] 3.4 Implementar `AdminRepository.set_roles(usuario_id, roles)` — reemplaza filas en `UsuarioRol`
- [x] 3.5 Implementar `AdminRepository.set_activo(usuario_id, activo)` — actualiza campo `activo`
- [x] 3.6 Implementar `AdminService.list_usuarios(uow, q, activo, page, size)` — delega al repository
- [x] 3.7 Implementar `AdminService.update_usuario(uow, id, data)` — lanza 404 si no existe, 409 si email duplicado
- [x] 3.8 Implementar `AdminService.asignar_roles(uow, id, roles, current_user_id)` — valida RN-RB03 (count ADMINs activos > 0 tras cambio), RN-RB04 (id != current_user_id)
- [x] 3.9 Implementar `AdminService.activar_usuario(uow, id, activo)` — valida que no sea el último ADMIN activo al desactivar
- [x] 3.10 Agregar endpoint `GET /admin/usuarios` en router — requiere rol ADMIN
- [x] 3.11 Agregar endpoint `PUT /admin/usuarios/{id}` en router — requiere rol ADMIN
- [x] 3.12 Agregar endpoint `PATCH /admin/usuarios/{id}/roles` en router — requiere rol ADMIN
- [x] 3.13 Agregar endpoint `PATCH /admin/usuarios/{id}/activar` en router — requiere rol ADMIN

## 4. Backend — Endpoints de métricas

- [x] 4.1 Implementar `AdminRepository.get_resumen()` — 4 queries: count pedidos, sum total donde estado=ENTREGADO en mes corriente, count productos activos, count usuarios activos
- [x] 4.2 Implementar `AdminRepository.get_ventas_por_periodo(periodo)` — query con `group_by(date_trunc)` sobre `Pedido` donde estado=ENTREGADO, según `periodo: Literal["dia","semana","mes"]`
- [x] 4.3 Implementar `AdminRepository.get_productos_top(limit)` — JOIN `DetallePedido` + `Producto` + filter estado=ENTREGADO, group_by producto_id, order_by sum(cantidad) DESC, limit N
- [x] 4.4 Implementar `AdminRepository.get_pedidos_por_estado()` — count pedidos group_by estado
- [x] 4.5 Implementar `AdminService` — métodos delgados que llaman al repository y retornan schemas
- [x] 4.6 Agregar endpoint `GET /admin/metricas/resumen` — requiere rol ADMIN
- [x] 4.7 Agregar endpoint `GET /admin/metricas/ventas` — requiere rol ADMIN, query param `periodo`
- [x] 4.8 Agregar endpoint `GET /admin/metricas/productos-top` — requiere rol ADMIN, query param `limit` (default 10, max 50)
- [x] 4.9 Agregar endpoint `GET /admin/metricas/pedidos-por-estado` — requiere rol ADMIN

## 5. Backend — Productos: soporte include_deleted para ADMIN

- [x] 5.1 Agregar query param `include_deleted: bool = False` a `GET /api/v1/productos` en `productos/router.py`
- [x] 5.2 Modificar `ProductosService.list_productos(uow, filters, current_user)` para pasar `include_deleted` solo si el usuario tiene rol ADMIN
- [x] 5.3 Modificar `ProductosRepository.list_productos(...)` para condicionar el filtro `deleted_at IS NULL` según `include_deleted`

## 6. Frontend — Tipos y API cliente

- [x] 6.1 Crear `src/types/admin.ts` con interfaces: `UsuarioAdmin`, `AsignarRolesRequest`, `ActivarRequest`, `MetricasResumen`, `VentasSeries`, `ProductoTop`, `PedidoPorEstado`
- [x] 6.2 Crear `src/api/endpoints/admin.ts` con funciones: `getUsuariosAdmin`, `updateUsuarioAdmin`, `asignarRoles`, `activarUsuario`, `getMetricasResumen`, `getVentasPorPeriodo`, `getProductosTop`, `getPedidosPorEstado`

## 7. Frontend — Hooks TanStack Query para admin

- [x] 7.1 Crear `features/admin/hooks/useMetricasResumen.ts` — `useQuery` sobre `/admin/metricas/resumen`, staleTime 5min
- [x] 7.2 Crear `features/admin/hooks/useVentasPorPeriodo.ts` — `useQuery` parametrizado por `periodo`
- [x] 7.3 Crear `features/admin/hooks/useProductosTop.ts` — `useQuery` con `limit`
- [x] 7.4 Crear `features/admin/hooks/usePedidosPorEstado.ts` — `useQuery`
- [x] 7.5 Crear `features/admin/hooks/useUsuariosAdmin.ts` — `useQuery` paginado con `q` y `activo`
- [x] 7.6 Crear `features/admin/hooks/useAdminMutations.ts` — mutations: `useUpdateUsuario`, `useAsignarRoles`, `useActivarUsuario`

## 8. Frontend — Componente Dashboard

- [x] 8.1 Crear `features/admin/components/KpiCard.tsx` — tarjeta con título, valor y Skeleton de carga
- [x] 8.2 Crear `features/admin/components/VentasLineChart.tsx` — recharts `LineChart` con selector de período (día/semana/mes) y estado vacío
- [x] 8.3 Crear `features/admin/components/ProductosTopBarChart.tsx` — recharts `BarChart` con top 10 productos por unidades vendidas
- [x] 8.4 Crear `features/admin/components/PedidosPieChart.tsx` — recharts `PieChart` con distribución de estados
- [x] 8.5 Crear `features/admin/components/Dashboard.tsx` — composición de 4 KpiCards + 3 gráficos usando los hooks de métricas

## 9. Frontend — Componente UsuariosCRUD

- [x] 9.1 Crear `features/admin/components/UsuariosTable.tsx` — tabla con columnas nombre, email, roles (badges), activo (toggle), acciones; paginada
- [x] 9.2 Crear `features/admin/components/EditarRolesModal.tsx` — modal con checkboxes de roles; botón "Guardar" llama `useAsignarRoles`; deshabilita botón si es el usuario actual (RN-RB04)
- [x] 9.3 Crear `features/admin/components/UsuariosCRUD.tsx` — barra de búsqueda (debounce 300ms) + `UsuariosTable`; maneja errores de API (LAST_ADMIN → toast, revert toggle)

## 10. Frontend — Componente StockTable

- [x] 10.1 Crear `features/admin/components/StockTable.tsx` — tabla de productos con columnas: nombre, stock (editable inline), disponible (toggle), acciones; con filtro "Mostrar eliminados" (solo ADMIN)
- [x] 10.2 Integrar `PATCH /productos/{id}/stock` y `PATCH /productos/{id}/disponibilidad` con optimistic update en la tabla
- [x] 10.3 Para ADMIN: pasar `include_deleted=true` al listar productos cuando el filtro esté activo; marcar filas eliminadas con badge visual

## 11. Frontend — Componente ConfiguracionPanel

- [x] 11.1 Crear `features/admin/components/ConfiguracionPanel.tsx` — tabla key-value con valores hardcodeados en estado local (nombre del sitio, contacto, moneda); edición inline con feedback de guardado local

## 12. Frontend — Rutas y navegación admin

- [x] 12.1 Agregar ruta `/admin` → `Dashboard` en React Router
- [x] 12.2 Agregar ruta `/admin/usuarios` → `UsuariosCRUD` en React Router
- [x] 12.3 Agregar ruta `/admin/stock` → `StockTable` en React Router
- [x] 12.4 Agregar ruta `/admin/configuracion` → `ConfiguracionPanel` en React Router
- [x] 12.5 Actualizar `AdminLayout` sidebar: agregar entradas Dashboard, Usuarios, Stock, Configuración con filtro por rol (ADMIN ve todo; STOCK ve solo Stock y Productos; PEDIDOS ve solo Pedidos)
- [x] 12.6 Exportar todos los nuevos componentes en `features/admin/index.ts`
