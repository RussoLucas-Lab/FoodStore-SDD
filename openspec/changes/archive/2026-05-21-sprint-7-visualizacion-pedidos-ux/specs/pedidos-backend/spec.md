## ADDED Requirements

### Requirement: GET /pedidos — lista paginada filtrada por rol
El sistema SHALL exponer `GET /api/v1/pedidos` autenticado. Si el actor tiene rol `CLIENT`, SHALL devolver únicamente los pedidos cuyo `usuario_id` coincida con el del token. Si tiene rol `ADMIN` o `PEDIDOS`, SHALL devolver todos los pedidos. La respuesta SHALL seguir la estructura de paginación estándar: `{ "items": [...], "total": N, "page": 1, "size": 20, "pages": P }`. Parámetros opcionales: `page` (default 1), `size` (default 20, máx 100), `estado_codigo` (filtro por estado).

#### Scenario: CLIENT ve solo sus pedidos
- **WHEN** un usuario CLIENT con `id=5` llama `GET /api/v1/pedidos`
- **THEN** responde HTTP 200 con solo los pedidos donde `usuario_id=5`

#### Scenario: ADMIN ve todos los pedidos
- **WHEN** un usuario ADMIN llama `GET /api/v1/pedidos`
- **THEN** responde HTTP 200 con todos los pedidos de todos los usuarios

#### Scenario: PEDIDOS ve todos los pedidos
- **WHEN** un usuario con rol PEDIDOS llama `GET /api/v1/pedidos`
- **THEN** responde HTTP 200 con todos los pedidos de todos los usuarios

#### Scenario: Filtro por estado
- **WHEN** un ADMIN llama `GET /api/v1/pedidos?estado_codigo=PENDIENTE`
- **THEN** responde solo pedidos con `estado_codigo="PENDIENTE"`

#### Scenario: Paginación
- **WHEN** existen 45 pedidos y se llama `GET /api/v1/pedidos?page=2&size=20`
- **THEN** responde `{ "items": [<20 pedidos>], "total": 45, "page": 2, "size": 20, "pages": 3 }`

#### Scenario: Sin autenticación
- **WHEN** se llama sin token
- **THEN** responde HTTP 401 con `{ "code": "NOT_AUTHENTICATED" }`

### Requirement: GET /pedidos/{id} — detalle completo con items, historial y pago
El sistema SHALL exponer `GET /api/v1/pedidos/{id}` autenticado. SHALL devolver un `PedidoDetailRead` con campos anidados: `items` (lista de `DetallePedidoRead` con `nombre_snapshot`, `precio_snapshot`, `cantidad`, `personalizacion`), `historial` (lista de `HistorialEstadoRead` en orden `created_at ASC`) y `pago` (objeto `PagoRead` o null si no existe). Un CLIENT solo puede consultar sus propios pedidos. ADMIN y PEDIDOS pueden consultar cualquier pedido.

#### Scenario: CLIENT consulta su propio pedido
- **WHEN** el CLIENT con `usuario_id=5` consulta `GET /api/v1/pedidos/10` y el pedido 10 pertenece al usuario 5
- **THEN** responde HTTP 200 con `PedidoDetailRead` completo incluyendo items, historial y pago

#### Scenario: CLIENT intenta consultar pedido ajeno
- **WHEN** el CLIENT con `usuario_id=5` consulta `GET /api/v1/pedidos/99` y el pedido 99 pertenece al usuario 7
- **THEN** responde HTTP 404 con `{ "code": "PEDIDO_NOT_FOUND" }`

#### Scenario: ADMIN consulta cualquier pedido
- **WHEN** un ADMIN consulta `GET /api/v1/pedidos/99`
- **THEN** responde HTTP 200 independientemente del `usuario_id` del pedido

#### Scenario: Pedido con múltiples items
- **WHEN** el pedido tiene 3 DetallePedido
- **THEN** `items` contiene exactamente 3 objetos con `nombre_snapshot`, `precio_snapshot`, `cantidad` y `personalizacion`

#### Scenario: Pedido sin pago iniciado
- **WHEN** el pedido existe pero no tiene un registro en `pago`
- **THEN** `pago: null` en la respuesta

#### Scenario: Historial en orden cronológico
- **WHEN** el pedido hizo 3 transiciones de estado
- **THEN** `historial` contiene 4 entradas (incluyendo la inicial de creación) en orden `created_at ASC`

#### Scenario: Pedido no encontrado
- **WHEN** el `id` no existe
- **THEN** responde HTTP 404 con `{ "code": "PEDIDO_NOT_FOUND" }`

### Requirement: GET /pedidos/{id}/historial — timeline de estados
El sistema SHALL exponer `GET /api/v1/pedidos/{id}/historial` autenticado. SHALL devolver la lista completa de `HistorialEstadoRead` del pedido en orden `created_at ASC`. Aplican las mismas restricciones de acceso que `GET /pedidos/{id}`: CLIENT solo ve sus propios pedidos; ADMIN y PEDIDOS ven cualquiera.

#### Scenario: Timeline con múltiples transiciones
- **WHEN** un CLIENT consulta `GET /api/v1/pedidos/10/historial` y el pedido le pertenece
- **THEN** responde HTTP 200 con lista de `HistorialEstadoRead` en orden `created_at ASC`

#### Scenario: Primera entrada tiene estado_desde null
- **WHEN** se consulta el historial de cualquier pedido
- **THEN** el primer elemento tiene `estado_desde: null` y `estado_hasta: "PENDIENTE"`

#### Scenario: Acceso denegado a pedido ajeno
- **WHEN** un CLIENT intenta consultar el historial de un pedido que no es suyo
- **THEN** responde HTTP 404 con `{ "code": "PEDIDO_NOT_FOUND" }`

### Requirement: DELETE /pedidos/{id} — cancelación propia del cliente
El sistema SHALL exponer `DELETE /api/v1/pedidos/{id}` accesible para usuarios con rol CLIENT. Solo permite cancelar pedidos propios (verificar `pedido.usuario_id == actor_id`). Solo permite cancelar pedidos en estado `PENDIENTE` (cualquier otro estado devuelve error de transición). El body SHALL aceptar `{ "motivo": string }` (obligatorio). Internamente delega al mismo `pedido_service.cambiar_estado()` con `nuevo_estado=CANCELADO`.

#### Scenario: Cancelación exitosa de pedido propio en PENDIENTE
- **WHEN** el CLIENT con `usuario_id=5` llama `DELETE /api/v1/pedidos/10` con body `{ "motivo": "Ya no lo necesito" }` y el pedido 10 le pertenece y está en PENDIENTE
- **THEN** responde HTTP 200 con el `PedidoDetailRead` actualizado con `estado_codigo="CANCELADO"`; existe nuevo registro en `historial_estado_pedido`

#### Scenario: Intento sobre pedido ajeno
- **WHEN** el CLIENT llama DELETE sobre un pedido que no le pertenece
- **THEN** responde HTTP 404 con `{ "code": "PEDIDO_NOT_FOUND" }`

#### Scenario: Intento sobre pedido en CONFIRMADO
- **WHEN** el CLIENT intenta cancelar un pedido propio en estado CONFIRMADO
- **THEN** responde HTTP 422 con `{ "code": "TRANSICION_NO_PERMITIDA" }`

#### Scenario: Sin motivo
- **WHEN** el CLIENT llama DELETE sin body o con `motivo: null`
- **THEN** responde HTTP 422 con `{ "code": "MOTIVO_REQUERIDO", "field": "motivo" }`

#### Scenario: ADMIN no puede usar este endpoint
- **WHEN** un ADMIN llama `DELETE /api/v1/pedidos/{id}`
- **THEN** responde HTTP 403 (este endpoint es exclusivo de CLIENT; ADMIN usa PATCH /estado)
