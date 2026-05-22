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

### Requirement: Service no llama session.commit()
El `PedidoService` SHALL completar toda su lógica sin invocar `session.commit()`, `session.rollback()` ni `session.close()` directamente. El commit/rollback SHALL ocurrir en el `UnitOfWork` context manager.

#### Scenario: Inspección del service
- **WHEN** se inspecciona el código del `PedidoService.crear`
- **THEN** no contiene ninguna llamada a `session.commit()`, `session.rollback()` ni `session.close()`

#### Scenario: Rollback ocurre vía UoW
- **WHEN** el service lanza `HTTPException` en medio de la creación
- **THEN** el `UnitOfWork.__exit__` invoca `rollback()` y nada queda persistido
