## 1. Backend — Schemas de respuesta

- [x] 1.1 Agregar `DetallePedidoRead` en `schemas.py` con campos: `id`, `producto_id`, `nombre_snapshot`, `precio_snapshot`, `cantidad`, `personalizacion`
- [x] 1.2 Agregar `HistorialEstadoRead` en `schemas.py` con campos: `id`, `estado_desde`, `estado_hasta`, `cambiado_por_id`, `motivo`, `created_at`
- [x] 1.3 Agregar `PedidoDetailRead` en `schemas.py` extendiendo `PedidoRead` con `items: List[DetallePedidoRead]`, `historial: List[HistorialEstadoRead]`, `pago: PagoRead | None` y `direccion_snapshot: dict`
- [x] 1.4 Agregar `CancelarPedidoRequest` en `schemas.py` con campo `motivo: str` requerido

## 2. Backend — Repository: queries de lectura

- [x] 2.1 Implementar `PedidoRepository.listar_paginado(usuario_id, solo_propios, estado_codigo, page, size)` — query paginada con filtro opcional de estado y usuario
- [x] 2.2 Implementar `PedidoRepository.get_detalle(pedido_id)` — query con `joinedload` de `DetallePedido`, `HistorialEstadoPedido` y `Pago`
- [x] 2.3 Implementar `PedidoRepository.get_historial(pedido_id)` — lista de `HistorialEstadoPedido` ordenada por `created_at ASC`

## 3. Backend — Service: listar y detalle

- [x] 3.1 Implementar `PedidoService.listar(uow, actor_id, actor_roles, estado_codigo, page, size)` — delega al repo; si `CLIENT` en roles usa `solo_propios=True`; retorna estructura de paginación
- [x] 3.2 Implementar `PedidoService.get_detalle(uow, pedido_id, actor_id, actor_roles)` — si `CLIENT`, verifica `pedido.usuario_id == actor_id` (404 si no); retorna `PedidoDetailRead` con datos anidados
- [x] 3.3 Implementar `PedidoService.get_historial(uow, pedido_id, actor_id, actor_roles)` — misma verificación de propiedad para CLIENT; retorna lista de `HistorialEstadoRead`

## 4. Backend — Service: cancelación propia del cliente

- [x] 4.1 Implementar `PedidoService.cancelar_propio(uow, pedido_id, actor_id, motivo)` — verifica que el pedido exista y `usuario_id == actor_id` (404 si no); delega a `cambiar_estado()` con `nuevo_estado=CANCELADO`, `actor_roles=["CLIENT"]`

## 5. Backend — Router: nuevos endpoints

- [x] 5.1 Agregar `GET /pedidos` en `router.py` con params `estado_codigo`, `page`, `size`; delegación a `pedido_service.listar()`
- [x] 5.2 Agregar `GET /pedidos/{pedido_id}` en `router.py` con respuesta `PedidoDetailRead`; delegación a `pedido_service.get_detalle()`
- [x] 5.3 Agregar `GET /pedidos/{pedido_id}/historial` en `router.py`; delegación a `pedido_service.get_historial()`
- [x] 5.4 Agregar `DELETE /pedidos/{pedido_id}` en `router.py` (solo rol CLIENT via `require_role`); body `CancelarPedidoRequest`; delegación a `pedido_service.cancelar_propio()`

## 6. Backend — Tests de nuevos endpoints

- [x] 6.1 Tests de `GET /pedidos`: CLIENT ve solo los propios, ADMIN ve todos, filtro por `estado_codigo`, paginación correcta, 401 sin token
- [x] 6.2 Tests de `GET /pedidos/{id}`: CLIENT accede a propio, CLIENT bloqueado en ajenos (404), ADMIN accede a cualquiera, 404 en inexistente, estructura anidada correcta
- [x] 6.3 Tests de `GET /pedidos/{id}/historial`: orden cronológico, primer nodo con `estado_desde=null`, acceso denegado para CLIENT ajeno
- [x] 6.4 Tests de `DELETE /pedidos/{id}`: cancelación exitosa con motivo, 404 en pedido ajeno, 422 si pedido en CONFIRMADO, 422 sin motivo, 403 si rol no es CLIENT

## 7. Frontend — Tipos TypeScript y cliente API

- [x] 7.1 Crear `frontend/src/types/pedidos.ts` con interfaces: `PedidoRead`, `PedidoDetailRead`, `DetallePedidoRead`, `HistorialEstadoRead`, `PedidoListResponse`
- [x] 7.2 Crear `frontend/src/api/endpoints/pedidos.ts` con funciones: `getPedidos(params)`, `getPedidoById(id)`, `getPedidoHistorial(id)`, `cancelarPedido(id, motivo)`

## 8. Frontend — Hooks de la feature pedidos

- [x] 8.1 Crear `frontend/src/features/pedidos/hooks/usePedidos.ts` — `useQuery` sobre `GET /pedidos` con parámetros de paginación; query key `['pedidos', params]`
- [x] 8.2 Crear `frontend/src/features/pedidos/hooks/usePedido.ts` — `useQuery` sobre `GET /pedidos/{id}`; query key `['pedido', id]`
- [x] 8.3 Crear `frontend/src/features/pedidos/hooks/useCancelarPedido.ts` — `useMutation` sobre `DELETE /pedidos/{id}`; invalida `['pedidos']` y `['pedido', id]` en `onSuccess`

## 9. Frontend — Componentes base de la feature pedidos

- [x] 9.1 Crear `EstadoPedidoBadge` — badge con color semántico por estado (PENDIENTE=amarillo, CONFIRMADO=azul, EN_PREP=naranja, EN_CAMINO=violeta, ENTREGADO=verde, CANCELADO=rojo)
- [x] 9.2 Crear `HistorialTimeline` — timeline vertical; cada nodo muestra estado, fecha, actor y motivo (si no nulo); nodo actual destacado
- [x] 9.3 Crear `PaymentStatus` — badge de estado de pago; `refetchInterval: 30_000` en `useQuery` de `GET /pagos/{pedido_id}` cuando estado es no-terminal; se desactiva en estado terminal

## 10. Frontend — PedidoDetail y cancelación

- [x] 10.1 Crear `CancelarPedidoModal` — modal con campo de texto `motivo` requerido; botón confirmar deshabilitado si `motivo` vacío; llama `useCancelarPedido()`; muestra errores inline
- [x] 10.2 Crear `PedidoDetail` — usa `usePedido(id)`; renderiza dirección (`direccion_snapshot`), lista de items con snapshots, `HistorialTimeline`, `PaymentStatus`; muestra `CancelarPedidoModal` si `estado_codigo === "PENDIENTE"`

## 11. Frontend — PedidosList y páginas

- [x] 11.1 Crear `PedidoCard` — card con id, fecha formateada, `EstadoPedidoBadge`, total, enlace a `/pedidos/:id`
- [x] 11.2 Crear `PedidosList` — grid/lista paginada usando `usePedidos()`; skeleton loaders mientras carga; estado vacío con CTA al catálogo; controles de paginación
- [x] 11.3 Crear `frontend/src/pages/PedidosPage.tsx` — envuelve `PedidosList`
- [x] 11.4 Crear `frontend/src/pages/PedidoDetailPage.tsx` — extrae `id` de params, envuelve `PedidoDetail`; redirige a `/pedidos` con toast si 404

## 12. Frontend — GestionPedidos (admin)

- [x] 12.1 Crear `frontend/src/features/admin/hooks/useGestionPedidos.ts` — `useQuery` sobre `GET /pedidos` (el backend filtra por rol automáticamente); soporta params de filtro y paginación
- [x] 12.2 Crear `frontend/src/features/admin/hooks/useAvanzarEstado.ts` — `useMutation` sobre `PATCH /pedidos/{id}/estado`; invalida `['pedidos']` en `onSuccess`
- [x] 12.3 Crear `AvanzarEstadoModal` — modal de confirmación que muestra "estado_actual → siguiente_estado"; sin campo de motivo (solo admin/gestor avanzan, no cancelan con este modal)
- [x] 12.4 Crear `GestionPedidosTable` — tabla paginada con columnas id, fecha, estado, total y botón "Avanzar"; chips de filtro por cada estado FSM; búsqueda por id de pedido; botón deshabilitado en estados terminales
- [x] 12.5 Crear `frontend/src/pages/GestionPedidosPage.tsx` — envuelve `GestionPedidosTable`; protegida con `ProtectedRoute` para roles ADMIN y PEDIDOS

## 13. Frontend — Rutas y navegación

- [x] 13.1 Agregar rutas `/pedidos` y `/pedidos/:id` en `App.tsx` / router principal, protegidas para rol CLIENT
- [x] 13.2 Agregar ruta `/admin/pedidos` protegida para roles ADMIN y PEDIDOS
- [x] 13.3 Agregar enlace "Mis Pedidos" en la navbar para clientes autenticados
- [x] 13.4 Agregar enlace "Gestión de Pedidos" en el `AdminLayout` sidebar para roles ADMIN y PEDIDOS
- [x] 13.5 Crear `frontend/src/features/pedidos/index.ts` con exports públicos del feature

## 14. Frontend — Tests

- [x] 14.1 Tests de `PedidosList`: renderiza cards con datos, muestra empty state, muestra skeletons durante carga
- [x] 14.2 Tests de `PedidoDetail`: renderiza secciones correctamente, muestra botón cancelar solo si PENDIENTE, oculta botón en otros estados
- [x] 14.3 Tests de `CancelarPedidoModal`: deshabilita confirmar con motivo vacío, llama mutación con motivo correcto, muestra error de API
- [x] 14.4 Tests de `GestionPedidosTable`: filtros de estado, búsqueda por id, redirige si rol no autorizado
