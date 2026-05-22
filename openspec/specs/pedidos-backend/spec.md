## ADDED Requirements

### Requirement: Crear pedido atómico desde el carrito (RN-PE01)
El sistema SHALL exponer `POST /api/v1/pedidos` que crea un pedido completo desde el carrito del cliente autenticado. La creación SHALL ser atómica: si falla cualquier validación o paso, ninguna fila (Pedido, DetallePedido, HistorialEstadoPedido) SHALL quedar persistida en la base de datos. El `usuario_id` SHALL tomarse exclusivamente del JWT — el body NO SHALL incluir `usuario_id`.

#### Scenario: Creación exitosa con un item
- **WHEN** un cliente autenticado envía `POST /api/v1/pedidos` con body `{ "direccion_id": 5, "forma_pago_codigo": "MERCADOPAGO", "items": [{ "producto_id": 12, "cantidad": 2 }] }` y todos los datos son válidos
- **THEN** responde HTTP 201 con `PedidoRead` (`id`, `estado_codigo='PENDIENTE'`, `total`, `created_at`); en la base existen exactamente: 1 fila en `pedido`, 1 fila en `detalle_pedido` y 1 fila en `historial_estado_pedido`

#### Scenario: Creación exitosa con múltiples items y personalización
- **WHEN** un cliente envía un body con 3 items, uno de ellos con `personalizacion: [4, 7]`
- **THEN** responde HTTP 201; existen 3 filas en `detalle_pedido` y la línea con personalización tiene `personalizacion=[4,7]` (orden preservado o ordenado ascendente, según implementación)

#### Scenario: Rollback ante error en medio de la creación
- **WHEN** se procesan 3 items y el 3° falla con `STOCK_INSUFICIENTE`
- **THEN** responde HTTP 409; en la base NO existe ninguna fila nueva en `pedido`, `detalle_pedido` ni `historial_estado_pedido`

#### Scenario: Sin autenticación
- **WHEN** se llama sin token
- **THEN** responde HTTP 401 con `{ "code": "NOT_AUTHENTICATED" }`

#### Scenario: usuario_id en body es ignorado
- **WHEN** el cliente envía `usuario_id: 999` en el body
- **THEN** el pedido se crea con el `usuario_id` del JWT y el campo del body se ignora silenciosamente (Pydantic schema no expone `usuario_id`)

### Requirement: Validar carrito no vacío
El sistema SHALL rechazar la creación si `items` viene vacío o ausente.

#### Scenario: Items vacío
- **WHEN** el cliente envía `items: []`
- **THEN** responde HTTP 400 con `{ "code": "CART_EMPTY", "detail": "El carrito está vacío" }`

#### Scenario: Items omitido
- **WHEN** el body no incluye el campo `items`
- **THEN** responde HTTP 422 con `{ "code": "VALIDATION_ERROR", "field": "items" }`

### Requirement: Snapshot de precio y nombre por línea (RN-PE02)
Cada `DetallePedido` creado SHALL guardar `precio_snapshot` (copia exacta de `Producto.precio_base` al momento del commit) y `nombre_snapshot` (copia exacta de `Producto.nombre`). Estos valores SHALL ser inmutables: cambios futuros en el `Producto` (renombre, cambio de precio, soft delete) NO SHALL afectar el detalle del pedido.

#### Scenario: Snapshot tomado al crear
- **WHEN** se crea un pedido con `producto_id=12` cuyo `precio_base=150.00` y `nombre="Pizza Muzzarella"`
- **THEN** la línea de detalle tiene `precio_snapshot=150.00` y `nombre_snapshot="Pizza Muzzarella"`

#### Scenario: Inmutabilidad ante cambio posterior
- **GIVEN** un pedido creado con un detalle `precio_snapshot=150.00`
- **WHEN** un admin posteriormente actualiza el producto a `precio_base=200.00` y `nombre="Pizza Mozzarella Premium"`
- **THEN** consultar el `detalle_pedido` sigue devolviendo `precio_snapshot=150.00` y `nombre_snapshot="Pizza Muzzarella"`

### Requirement: Snapshot de dirección completa (RN-PE03)
El `Pedido.direccion_snapshot` SHALL contener una copia JSON de la dirección elegida al momento del pedido, con campos: `id`, `calle`, `numero`, `piso`, `depto`, `ciudad`, `provincia`, `codigo_postal`, `referencia`, `es_principal`. Cambios o eliminación posterior de la `Direccion` original NO SHALL afectar el snapshot.

#### Scenario: Snapshot incluye todos los campos
- **WHEN** se crea un pedido con `direccion_id=5`
- **THEN** `pedido.direccion_snapshot` es un dict JSON con todos los campos enumerados y los valores actuales de la dirección 5

#### Scenario: Inmutabilidad ante eliminación
- **GIVEN** un pedido con `direccion_snapshot` que apunta a `direccion_id=5`
- **WHEN** el cliente elimina (soft delete) la dirección 5
- **THEN** el `direccion_snapshot` del pedido sigue conteniendo los mismos datos originales

### Requirement: Validar disponibilidad y stock con lock (RN-PE04, RN-PE05)
Para cada `producto_id` del carrito, el sistema SHALL obtener un lock pesimista (`SELECT ... FOR UPDATE`) sobre la fila de `Producto` dentro de la misma transacción, ordenando los IDs ascendentemente para evitar deadlocks. Tras obtener el lock, SHALL validar: (a) el producto existe, (b) `deleted_at IS NULL`, (c) `disponible=true`, (d) `stock_cantidad >= cantidad`.

#### Scenario: Stock suficiente
- **WHEN** el cliente pide 2 unidades de un producto con `stock_cantidad=5`
- **THEN** la validación pasa y el pedido se crea

#### Scenario: Producto no existe
- **WHEN** el cliente envía un `producto_id` que no existe
- **THEN** responde HTTP 400 con `{ "code": "PRODUCTO_NOT_FOUND", "field": "producto_id" }`

#### Scenario: Producto soft-eliminado
- **WHEN** el `producto_id` tiene `deleted_at` no nulo
- **THEN** responde HTTP 400 con `{ "code": "PRODUCTO_NOT_FOUND" }`

#### Scenario: Producto no disponible
- **WHEN** el `producto_id` existe con `disponible=false`
- **THEN** responde HTTP 409 con `{ "code": "PRODUCTO_NO_DISPONIBLE", "field": "producto_id" }`

#### Scenario: Stock insuficiente
- **WHEN** el cliente pide 10 unidades de un producto con `stock_cantidad=3`
- **THEN** responde HTTP 409 con `{ "code": "STOCK_INSUFICIENTE", "field": "producto_id", "detail": "Stock insuficiente para producto 12" }`

#### Scenario: Lock se libera al finalizar la transacción
- **WHEN** la transacción termina (commit o rollback)
- **THEN** el lock sobre las filas de `Producto` se libera (comportamiento estándar de PostgreSQL `FOR UPDATE`)

### Requirement: Validar dirección pertenece al usuario
El sistema SHALL verificar que la `direccion_id` enviada exista, tenga `deleted_at IS NULL` y `usuario_id` coincida con el del token. Si no se cumple, SHALL devolver HTTP 404.

#### Scenario: Dirección válida del usuario
- **WHEN** el cliente envía `direccion_id=5` y la dirección 5 pertenece a su usuario y está activa
- **THEN** la validación pasa y el snapshot se toma

#### Scenario: Dirección de otro usuario
- **WHEN** el cliente envía una `direccion_id` que pertenece a otro usuario
- **THEN** responde HTTP 404 con `{ "code": "DIRECCION_NOT_FOUND" }` (no se filtra existencia entre usuarios)

#### Scenario: Dirección eliminada
- **WHEN** la `direccion_id` tiene `deleted_at` no nulo
- **THEN** responde HTTP 404 con `{ "code": "DIRECCION_NOT_FOUND" }`

#### Scenario: Dirección inexistente
- **WHEN** la `direccion_id` no existe en la tabla
- **THEN** responde HTTP 404 con `{ "code": "DIRECCION_NOT_FOUND" }`

### Requirement: Validar forma de pago habilitada
El sistema SHALL verificar que la `forma_pago_codigo` exista en la tabla `forma_pago` y tenga `habilitado=true`. Si no se cumple, SHALL devolver HTTP 400.

#### Scenario: Forma de pago válida
- **WHEN** el cliente envía `forma_pago_codigo="MERCADOPAGO"` y la fila existe con `habilitado=true`
- **THEN** la validación pasa

#### Scenario: Forma de pago inexistente
- **WHEN** el cliente envía un código que no existe
- **THEN** responde HTTP 400 con `{ "code": "FORMA_PAGO_NOT_FOUND", "field": "forma_pago_codigo" }`

#### Scenario: Forma de pago deshabilitada
- **WHEN** el código existe pero `habilitado=false`
- **THEN** responde HTTP 400 con `{ "code": "FORMA_PAGO_NOT_FOUND" }`

### Requirement: Validar personalización pertenece al producto
Para cada `item` con `personalizacion: [int]` no vacío, el sistema SHALL verificar que cada `ingrediente_id` esté asociado al `producto_id` en la tabla `producto_ingrediente`.

#### Scenario: Personalización válida
- **WHEN** el item tiene `producto_id=12` y `personalizacion=[4, 7]`, y el producto 12 está asociado a los ingredientes 4 y 7
- **THEN** la validación pasa

#### Scenario: Ingrediente no pertenece al producto
- **WHEN** un item tiene `personalizacion=[99]` y el producto NO está asociado al ingrediente 99
- **THEN** responde HTTP 400 con `{ "code": "INGREDIENTE_NO_DEL_PRODUCTO", "field": "personalizacion", "detail": "Ingrediente 99 no pertenece al producto 12" }`

#### Scenario: Personalización vacía o ausente
- **WHEN** el item no tiene personalización o `personalizacion: []`
- **THEN** la validación pasa y la línea se crea con `personalizacion=null` o `[]` según implementación

### Requirement: Pedido nace en PENDIENTE con primer historial (RN-PE06)
Todo pedido recién creado SHALL tener `estado_codigo='PENDIENTE'`. En la misma transacción SHALL crearse exactamente una fila en `historial_estado_pedido` con `estado_desde=NULL`, `estado_hasta='PENDIENTE'`, `cambiado_por_id=usuario_id` y `motivo=NULL`.

#### Scenario: Estado inicial
- **WHEN** se crea un pedido exitosamente
- **THEN** `pedido.estado_codigo='PENDIENTE'`

#### Scenario: Primer registro de historial
- **WHEN** se crea un pedido exitosamente
- **THEN** existe exactamente una fila en `historial_estado_pedido` con `pedido_id` del nuevo pedido, `estado_desde=NULL`, `estado_hasta='PENDIENTE'`, `cambiado_por_id=usuario_id`

#### Scenario: Historial creado dentro de la transacción
- **WHEN** la creación del historial falla (ej: violación de FK)
- **THEN** la transacción hace rollback y no queda ni el `Pedido` ni el `DetallePedido`

### Requirement: Cálculo del total (RN-PE08)
El sistema SHALL calcular `pedido.total = Σ(cantidad × precio_snapshot) + costo_envio`. En Sprint 5 el `costo_envio` SHALL ser 0. El total SHALL calcularse usando `precio_snapshot` (no `precio_base`) para mantener coherencia con las líneas.

#### Scenario: Total con un item
- **WHEN** se crea un pedido con un item `cantidad=2, precio_snapshot=150.00`
- **THEN** `pedido.total = 300.00`

#### Scenario: Total con múltiples items
- **WHEN** se crea un pedido con items `[(2, 150.00), (1, 80.50), (3, 50.00)]`
- **THEN** `pedido.total = 530.50`

#### Scenario: Total con costo_envio cero
- **WHEN** se crea cualquier pedido en Sprint 5
- **THEN** `costo_envio` no se suma o se suma como 0; el `total` final es solo la suma de líneas

### Requirement: Stock NO se decrementa al crear (RN-FS03 difiere a Sprint 6)
El endpoint `POST /api/v1/pedidos` SHALL validar stock y bloquear las filas, pero NO SHALL modificar `Producto.stock_cantidad`. El decremento ocurre solo al confirmar el pago (Sprint 6, transición `PENDIENTE → CONFIRMADO`).

#### Scenario: Stock antes y después de crear pedido
- **GIVEN** un producto con `stock_cantidad=10`
- **WHEN** se crea un pedido con `cantidad=3` de ese producto exitosamente
- **THEN** consultar `Producto.stock_cantidad` sigue devolviendo 10

### Requirement: Idempotencia opcional vía header
Si el cliente envía el header `Idempotency-Key: <uuid>`, el sistema SHALL verificar si ya existe un pedido del mismo usuario con esa key. Si existe, SHALL devolver el pedido existente con HTTP 200 (no crea duplicado). Si no existe, SHALL crear el pedido guardando la key en `Pedido.idempotency_key`.

#### Scenario: Primer request con Idempotency-Key
- **WHEN** el cliente envía `POST /api/v1/pedidos` con header `Idempotency-Key: abc-123` y body válido
- **THEN** responde HTTP 201 con el pedido creado; en la base hay 1 pedido con `idempotency_key="abc-123"`

#### Scenario: Reintento con la misma Idempotency-Key
- **GIVEN** un pedido existente del usuario con `idempotency_key="abc-123"`
- **WHEN** el cliente envía otro `POST /api/v1/pedidos` con header `Idempotency-Key: abc-123`
- **THEN** responde HTTP 200 con el mismo `PedidoRead` del pedido existente; NO se crea un nuevo pedido

#### Scenario: Sin header Idempotency-Key
- **WHEN** el cliente envía el POST sin el header
- **THEN** se procede a crear el pedido normalmente; `idempotency_key` queda NULL

#### Scenario: Misma Idempotency-Key, otro usuario
- **GIVEN** el usuario A tiene un pedido con `idempotency_key="abc-123"`
- **WHEN** el usuario B envía un POST con la misma key
- **THEN** se crea un nuevo pedido para B (la unicidad es por usuario + key)

### Requirement: Persistir forma_pago_codigo en el Pedido
El sistema SHALL persistir la `forma_pago_codigo` elegida como columna del `Pedido` (no como tabla de Pagos, que se crea en Sprint 6). La columna SHALL tener FK a `forma_pago.codigo`.

#### Scenario: Pedido guarda la forma de pago
- **WHEN** el cliente crea un pedido con `forma_pago_codigo="EFECTIVO"`
- **THEN** la fila de `pedido` tiene `forma_pago_codigo="EFECTIVO"`

#### Scenario: FK válida
- **WHEN** se intenta persistir un `forma_pago_codigo` que no existe (caso interno, no debería pasar por la validación previa)
- **THEN** la BD rechaza el INSERT por violación de FK y la transacción hace rollback

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

### Requirement: Service no llama session.commit()
El `PedidoService` SHALL completar toda su lógica sin invocar `session.commit()`, `session.rollback()` ni `session.close()` directamente. El commit/rollback SHALL ocurrir en el `UnitOfWork` context manager.

#### Scenario: Inspección del service
- **WHEN** se inspecciona el código del `PedidoService.crear`
- **THEN** no contiene ninguna llamada a `session.commit()`, `session.rollback()` ni `session.close()`

#### Scenario: Rollback ocurre vía UoW
- **WHEN** el service lanza `HTTPException` en medio de la creación
- **THEN** el `UnitOfWork.__exit__` invoca `rollback()` y nada queda persistido

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
