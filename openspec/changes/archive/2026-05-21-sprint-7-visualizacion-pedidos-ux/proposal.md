## Why

El cliente puede crear pedidos y pagar (Sprints 5–6), pero no tiene ninguna pantalla para ver su historial ni el estado de cada pedido. Además, los gestores de pedidos no tienen un panel para avanzar los estados FSM desde la UI. Sprint 7 cierra este gap crítico antes del sprint final de métricas.

## What Changes

- **Backend**: nuevos endpoints de lectura y cancelación propia de pedidos (`GET /pedidos`, `GET /pedidos/{id}`, `GET /pedidos/{id}/historial`, `DELETE /pedidos/{id}`).
- **Frontend — Feature `pedidos`**: pantalla de historial paginada, vista de detalle con snapshots, timeline visual de estados y estado de pago en tiempo real.
- **Frontend — Feature `admin`**: panel `GestionPedidos` para que roles PEDIDOS/ADMIN listen todos los pedidos y avancen estados FSM desde la UI.

## Capabilities

### New Capabilities

- `pedidos-frontend`: Feature del cliente para visualizar su historial de pedidos, detalle completo (items con snapshots, dirección, pago) y timeline de estados.
- `gestion-pedidos-admin-frontend`: Panel de gestión de pedidos para roles ADMIN/PEDIDOS: listado global, filtros por estado, avance manual de estados FSM.

### Modified Capabilities

- `pedidos-backend`: Se agregan los endpoints de consulta (`GET /pedidos`, `GET /pedidos/{id}`, `GET /pedidos/{id}/historial`) y el endpoint de cancelación propia del cliente (`DELETE /pedidos/{id}`). Los endpoints de creación y FSM definidos en Sprints 5–6 no cambian.

## Impact

- **Backend**: `backend/app/modules/pedidos/router.py`, `service.py`, `repository.py`, `schemas.py` — se extienden con 4 nuevos endpoints y schemas de respuesta enriquecidos.
- **Frontend**: nuevo directorio `frontend/src/features/pedidos/` con componentes, hooks y tipos. Extensión de `frontend/src/features/admin/` con `GestionPedidos`.
- **Router**: nuevas rutas `/pedidos`, `/pedidos/:id` para clientes; `/admin/pedidos` para gestores.
- **API**: los schemas `PedidoRead` y `DetallePedidoRead` deberán incluir datos anidados (historial, pago) en la respuesta de detalle.
