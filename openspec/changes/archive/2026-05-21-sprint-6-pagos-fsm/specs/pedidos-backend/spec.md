## ADDED Requirements

### Requirement: PATCH /pedidos/{id}/estado — cambio de estado con FSM (RN-FS01)
El sistema SHALL exponer `PATCH /api/v1/pedidos/{id}/estado` autenticado. El body SHALL incluir `{ "nuevo_estado": string, "motivo": string | null }`. Antes de ejecutar la transición, el servicio SHALL validar: (a) el pedido existe, (b) la transición `estado_actual → nuevo_estado` está permitida en el mapa FSM, (c) el rol del solicitante tiene permiso para ejecutar esa transición. Si alguna validación falla, SHALL devolver el código de error correspondiente sin modificar nada.

#### Scenario: Transición válida — EN_PREP a EN_CAMINO (Gestor de Pedidos)
- **WHEN** un usuario con rol PEDIDOS envía `PATCH /api/v1/pedidos/42/estado` con `{ "nuevo_estado": "EN_CAMINO" }` y el pedido 42 está en EN_PREP
- **THEN** responde HTTP 200 con el `PedidoRead` actualizado; `pedido.estado_codigo="EN_CAMINO"`; existe un nuevo registro en `historial_estado_pedido` con `estado_desde="EN_PREP"`, `estado_hasta="EN_CAMINO"`, `cambiado_por_id=<usuario_id>`

#### Scenario: Transición no permitida en el mapa FSM
- **WHEN** se envía `nuevo_estado="PENDIENTE"` sobre un pedido en EN_PREP
- **THEN** responde HTTP 422 con `{ "code": "TRANSICION_NO_PERMITIDA", "detail": "No se puede pasar de EN_PREP a PENDIENTE" }`

#### Scenario: Pedido no encontrado
- **WHEN** el `id` del pedido no existe
- **THEN** responde HTTP 404 con `{ "code": "PEDIDO_NOT_FOUND" }`

#### Scenario: Sin autenticación
- **WHEN** se llama sin token
- **THEN** responde HTTP 401 con `{ "code": "NOT_AUTHENTICATED" }`

### Requirement: OrderStateMachine — mapa completo de transiciones (RN-FS01 a RN-FS10)
El sistema SHALL implementar una clase `OrderStateMachine` en `app/modules/pedidos/fsm.py` con el siguiente mapa de transiciones permitidas. La transición `PENDIENTE → CONFIRMADO` SHALL marcarse como `automática` (solo ejecutable por el sistema vía webhook, nunca por endpoint PATCH manual):

| Desde | Hacia | Roles permitidos |
|-------|-------|-----------------|
| PENDIENTE | CONFIRMADO | Sistema (webhook) — rechazar si viene de PATCH |
| CONFIRMADO | EN_PREP | ADMIN, PEDIDOS |
| EN_PREP | EN_CAMINO | ADMIN, PEDIDOS |
| EN_CAMINO | ENTREGADO | ADMIN, PEDIDOS |
| PENDIENTE | CANCELADO | CLIENT (propio), ADMIN, PEDIDOS |
| CONFIRMADO | CANCELADO | ADMIN, PEDIDOS |
| EN_PREP | CANCELADO | ADMIN únicamente |

ENTREGADO y CANCELADO son estados terminales. No tienen transiciones salientes.

#### Scenario: Mapa correcto para CONFIRMADO → EN_PREP
- **WHEN** se consulta `OrderStateMachine.is_allowed("CONFIRMADO", "EN_PREP", roles=["PEDIDOS"])`
- **THEN** retorna `True`

#### Scenario: Terminal ENTREGADO no tiene salidas
- **WHEN** se consulta cualquier transición desde ENTREGADO
- **THEN** `OrderStateMachine.is_allowed("ENTREGADO", *, *)` retorna `False` para cualquier destino

#### Scenario: CLIENT cancela su propio pedido PENDIENTE
- **WHEN** un usuario con rol CLIENT envía PATCH con `nuevo_estado=CANCELADO` sobre su propio pedido en PENDIENTE
- **THEN** la FSM permite la transición

#### Scenario: CLIENT intenta cancelar pedido EN_PREP
- **WHEN** un CLIENT envía PATCH con `nuevo_estado=CANCELADO` sobre un pedido en EN_PREP
- **THEN** responde HTTP 422 con `{ "code": "TRANSICION_NO_PERMITIDA" }` (rol CLIENT no puede cancelar EN_PREP)

### Requirement: Decremento atómico de stock al confirmar (RN-FS03, RN-FS04)
Cuando el sistema procesa la transición `PENDIENTE → CONFIRMADO` (vía webhook), SHALL decrementar `Producto.stock_cantidad` por la `cantidad` de cada `DetallePedido` dentro del mismo `UnitOfWork`. Si el decremento deja `stock_cantidad < 0` para algún producto (race condition extrema), SHALL lanzar error y hacer rollback de toda la transición.

#### Scenario: Stock decrementado correctamente
- **GIVEN** un producto con `stock_cantidad=10` y un DetallePedido con `cantidad=3`
- **WHEN** el webhook confirma el pedido
- **THEN** `Producto.stock_cantidad=7` y el pedido está en CONFIRMADO

#### Scenario: Stock resultante negativo — rollback
- **GIVEN** un producto con `stock_cantidad=2` y un DetallePedido con `cantidad=3` (race condition)
- **WHEN** el sistema intenta confirmar
- **THEN** hace rollback; el pedido permanece en PENDIENTE; `pago.estado_pago` queda en APROBADO pero sin efecto de transición (requiere intervención manual)

### Requirement: Restaurar stock al cancelar desde CONFIRMADO (RN-FS05)
Cuando se transiciona de CONFIRMADO a CANCELADO, el sistema SHALL restaurar `Producto.stock_cantidad` sumando la `cantidad` de cada `DetallePedido` dentro del mismo `UnitOfWork`.

#### Scenario: Stock restaurado al cancelar desde CONFIRMADO
- **GIVEN** un producto con `stock_cantidad=7` (fue decrementado al confirmar)
- **WHEN** un admin cancela el pedido desde CONFIRMADO
- **THEN** `Producto.stock_cantidad=10` (se suman las cantidades del pedido)

#### Scenario: Cancelar desde PENDIENTE no afecta stock
- **WHEN** se cancela un pedido en PENDIENTE
- **THEN** `Producto.stock_cantidad` permanece sin cambios (nunca fue decrementado)

### Requirement: Historial append-only en cada transición (RN-FS07)
Toda transición de estado (incluyendo la del webhook) SHALL crear exactamente un nuevo registro en `historial_estado_pedido` con `estado_desde=<estado_anterior>`, `estado_hasta=<nuevo_estado>`, `cambiado_por_id=<actor_id>` y `motivo` (requerido solo al cancelar, NULL en otros casos). No se permite UPDATE ni DELETE sobre esta tabla.

#### Scenario: Registro por transición
- **WHEN** un pedido hace 3 transiciones: PENDIENTE→CONFIRMADO, CONFIRMADO→EN_PREP, EN_PREP→EN_CAMINO
- **THEN** existen 4 filas en `historial_estado_pedido` (1 de creación en Sprint 5 + 3 de transiciones)

#### Scenario: Historial creado en la misma transacción
- **WHEN** la transición de estado falla (ej: el decremento de stock hace rollback)
- **THEN** el registro de historial también hace rollback y no queda persistido

### Requirement: Motivo obligatorio al cancelar (RN-FS09, RN-FS10)
Cuando el `nuevo_estado=CANCELADO`, el campo `motivo` SHALL ser obligatorio (no nulo ni vacío). El sistema SHALL rechazar con HTTP 422 si `motivo` está ausente o es cadena vacía.

#### Scenario: Cancelación con motivo
- **WHEN** se envía `{ "nuevo_estado": "CANCELADO", "motivo": "El cliente no puede recibirlo" }`
- **THEN** la transición procede y `historial_estado_pedido.motivo="El cliente no puede recibirlo"`

#### Scenario: Cancelación sin motivo
- **WHEN** se envía `{ "nuevo_estado": "CANCELADO" }` o `{ "nuevo_estado": "CANCELADO", "motivo": null }`
- **THEN** responde HTTP 422 con `{ "code": "MOTIVO_REQUERIDO", "field": "motivo", "detail": "El motivo es obligatorio al cancelar un pedido" }`

#### Scenario: Motivo vacío
- **WHEN** se envía `{ "nuevo_estado": "CANCELADO", "motivo": "   " }` (solo espacios)
- **THEN** responde HTTP 422 con `{ "code": "MOTIVO_REQUERIDO" }`

### Requirement: Service no llama session.commit() en FSM
El `PedidoService` y el `PagoService` SHALL gestionar todas las transiciones de la FSM sin invocar `session.commit()` directamente. El commit/rollback SHALL ocurrir exclusivamente en el `UnitOfWork` context manager.

#### Scenario: Confirmación via webhook sin commit manual
- **WHEN** `PagoService.procesar_webhook()` confirma un pedido
- **THEN** no contiene llamadas directas a `session.commit()` — el UoW hace el commit al salir del bloque `with`
