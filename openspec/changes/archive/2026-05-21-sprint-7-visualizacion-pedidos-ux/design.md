## Context

Sprints 5–6 dejaron el ciclo de vida del pedido funcional en backend (creación atómica, FSM, pagos MercadoPago, webhook). El módulo `pedidos` tiene `POST /pedidos`, `PATCH /pedidos/{id}/estado` y `GET /pedidos/formas-pago`. Lo que falta son los endpoints de lectura y la feature frontend completa. El frontend `features/pedidos/` no existe todavía.

Estado actual del backend `pedidos`:
- `router.py`: 3 endpoints (POST crear, PATCH estado, GET formas-pago)
- `service.py`: `crear()`, `cambiar_estado()`, `confirmar_pedido()` (webhook)
- `schemas.py`: `PedidoCreate`, `PedidoRead` (básico), `CambiarEstadoRequest/Response`

## Goals / Non-Goals

**Goals:**
- Exponer `GET /pedidos`, `GET /pedidos/{id}`, `GET /pedidos/{id}/historial` y `DELETE /pedidos/{id}` en el backend.
- Implementar la feature `pedidos` frontend: `PedidosList`, `PedidoDetail`, `HistorialTimeline`, estado de pago en tiempo real.
- Implementar `GestionPedidos` en el panel admin: listado global con avance de FSM.

**Non-Goals:**
- Dashboard de métricas (Sprint 8).
- CRUD de usuarios (Sprint 8).
- Notificaciones push o email al cliente.
- Exportación de historial.

## Decisions

### D1 — GET /pedidos filtra por rol en el service, no en el router
El router expone un único endpoint `GET /pedidos`. El service inspecciona `actor_roles`: si incluye `CLIENT`, filtra `usuario_id = actor_id`; si incluye `ADMIN` o `PEDIDOS`, devuelve todos. Rationale: mantiene el router limpio y el service stateless — el mismo patrón usado en `cambiar_estado()`.

### D2 — PedidoDetailRead: schema anidado con historial y pago
Para `GET /pedidos/{id}` se crea `PedidoDetailRead` que extiende `PedidoRead` con campos:
- `items: List[DetallePedidoRead]` (incluye `nombre_snapshot`, `precio_snapshot`, `cantidad`, `personalizacion`)
- `historial: List[HistorialEstadoRead]` (append-only, orden `created_at ASC`)
- `pago: PagoRead | None` (puede ser None si el pago aún no se inició)
- `direccion_snapshot: dict` (ya en el modelo)

El schema de lista (`PedidoRead`) permanece sin historial/items para evitar N+1 en el listado.

### D3 — DELETE /pedidos/{id} como alias de cancelación propia del CLIENT
`DELETE /pedidos/{id}` solo lo puede llamar un CLIENT sobre su propio pedido. Internamente llama al mismo `pedido_service.cambiar_estado()` con `nuevo_estado=CANCELADO`. El `motivo` viene del query param `?motivo=...` o body `{ "motivo": "..." }`. Rationale: semánticamente un DELETE en REST, y simplifica el frontend del cliente (no necesita conocer la FSM).

**Alternativa descartada**: reutilizar directamente `PATCH /pedidos/{id}/estado` desde el frontend del cliente. Descartado porque expone la FSM al cliente, y la restricción de "solo propios y solo PENDIENTE" es más clara con un endpoint dedicado.

### D4 — Polling de estado de pago en frontend: TanStack Query refetchInterval
El componente `PaymentStatus` usa `useQuery` con `refetchInterval: 30_000` (30 s) mientras el pago esté en estado no terminal (`PENDIENTE` o `EN_PROCESO`). Al llegar a `APROBADO`, `RECHAZADO` o `ERROR` se desactiva el polling. Rationale: ya establecido en US-072 (Sprint 6). Se usa el mismo endpoint `GET /pagos/{pedido_id}`.

### D5 — GestionPedidos: un solo componente con filtro de estado
Panel admin con tabla paginada de todos los pedidos. Filtro por estado (chips de colores). Botón de avance de estado usando `PATCH /pedidos/{id}/estado` existente. No es un CRUD completo — solo lectura + avance de FSM.

## Risks / Trade-offs

- [N+1 en lista de pedidos] Si `PedidoRead` incluye items, el listado genera N queries. → Mitigación: `PedidoRead` no incluye items. Solo `PedidoDetailRead` los expone, con eager loading via `joinedload`.
- [Autorización de DELETE] Un CLIENT podría intentar cancelar el pedido de otro. → Mitigación: el service verifica `pedido.usuario_id == actor_id` antes de proceder.
- [Polling agresivo] 30 s por tab abierta puede generar carga. → Mitigación: aceptable para el alcance del TPI (pocos usuarios concurrentes en sandbox).
