## ADDED Requirements

### Requirement: Crear preferencia de pago MercadoPago (RN-MP01)
El sistema SHALL exponer `POST /api/v1/pagos/crear` autenticado (rol CLIENT) que crea una preferencia de pago en MercadoPago para el pedido indicado. El cuerpo SHALL incluir `pedido_id`. El sistema SHALL generar un `idempotency_key` UUID v4 y enviarlo al SDK de MP (`preference.idempotency_key`). El endpoint SHALL devolver `{ "preference_id": "<mp_preference_id>", "init_point": "<url>" }`. El pedido SHALL estar en estado PENDIENTE y pertenecer al usuario autenticado; de lo contrario HTTP 404 o HTTP 409.

#### Scenario: Creación exitosa
- **WHEN** un cliente autenticado envía `POST /api/v1/pagos/crear` con `{ "pedido_id": 42 }` y el pedido 42 le pertenece y está en PENDIENTE
- **THEN** responde HTTP 201 con `{ "preference_id": "...", "init_point": "https://..." }`; en la tabla `pago` se crea una fila con `pedido_id=42`, `estado_pago="PENDIENTE"`, `idempotency_key=<uuid>` e `mp_preference_id` poblado

#### Scenario: Pedido no pertenece al usuario
- **WHEN** el pedido indicado pertenece a otro usuario
- **THEN** responde HTTP 404 con `{ "code": "PEDIDO_NOT_FOUND" }`

#### Scenario: Pedido no en PENDIENTE
- **WHEN** el pedido está en estado CONFIRMADO o posterior
- **THEN** responde HTTP 409 con `{ "code": "PEDIDO_ESTADO_INVALIDO", "detail": "Solo se puede iniciar pago en estado PENDIENTE" }`

#### Scenario: Reintento idempotente
- **GIVEN** ya existe una fila `pago` para el pedido 42 con `idempotency_key` X
- **WHEN** el cliente llama nuevamente a `POST /api/v1/pagos/crear` con `pedido_id=42`
- **THEN** responde HTTP 200 devolviendo la misma `preference_id` existente sin crear una nueva fila en `pago`

### Requirement: Webhook IPN de MercadoPago (RN-MP02)
El sistema SHALL exponer `POST /api/v1/pagos/webhook` como endpoint público (sin autenticación JWT) que recibe notificaciones IPN de MercadoPago. El sistema SHALL validar la firma HMAC-SHA256 del header `x-signature` usando el `WEBHOOK_SECRET` configurado en `.env`. Si la firma no coincide, SHALL devolver HTTP 400 y no procesar el evento. Para eventos `topic=payment` con `status=approved`, SHALL obtener detalles del pago via SDK MP, marcar la fila `pago` como `APROBADO`, y delegar a `PedidoService.confirmar_pedido()` la transición de estado PENDIENTE → CONFIRMADO con decremento de stock.

#### Scenario: Pago aprobado — flujo completo
- **WHEN** MercadoPago envía un IPN con `topic=payment`, `data.id=<mp_payment_id>`, firma válida, y el pago tiene `status=approved`
- **THEN** el sistema actualiza `pago.estado_pago="APROBADO"`, `pago.mp_payment_id=<mp_payment_id>`; el pedido asociado transiciona a `CONFIRMADO`; el stock de cada producto del pedido se decrementa por la cantidad correspondiente; se crea un registro en `historial_estado_pedido`; el endpoint responde HTTP 200

#### Scenario: Firma inválida
- **WHEN** el header `x-signature` no coincide con el HMAC calculado
- **THEN** responde HTTP 400 con `{ "code": "INVALID_SIGNATURE" }` y no modifica ningún dato

#### Scenario: IPN duplicado (idempotencia)
- **GIVEN** ya existe una fila `pago` con `mp_payment_id=<id>` y `estado_pago="APROBADO"`
- **WHEN** MercadoPago reenvía el mismo IPN
- **THEN** responde HTTP 200 sin reprocesar (no vuelve a decrementar stock ni crear historial)

#### Scenario: Pago rechazado o pendiente
- **WHEN** el IPN tiene `status=rejected` o `status=pending`
- **THEN** el sistema actualiza `pago.estado_pago="RECHAZADO"` o no cambia; el pedido NO transiciona de PENDIENTE; responde HTTP 200

#### Scenario: topic distinto a payment
- **WHEN** el IPN tiene `topic=merchant_order` u otro valor
- **THEN** responde HTTP 200 sin procesar ninguna acción

### Requirement: Consultar estado de pago por pedido
El sistema SHALL exponer `GET /api/v1/pagos/{pedido_id}` autenticado (rol CLIENT, ADMIN o PEDIDOS) que devuelve el estado actual del pago asociado al pedido. Si no existe fila en `pago` para ese pedido, SHALL devolver HTTP 404.

#### Scenario: Pago existente
- **WHEN** un cliente autenticado llama `GET /api/v1/pagos/42` y existe una fila `pago` para el pedido 42
- **THEN** responde HTTP 200 con `{ "pedido_id": 42, "estado_pago": "APROBADO", "mp_payment_id": "...", "created_at": "..." }`

#### Scenario: Sin pago iniciado
- **WHEN** el pedido existe pero no se ha iniciado ningún pago
- **THEN** responde HTTP 404 con `{ "code": "PAGO_NOT_FOUND" }`

#### Scenario: Pedido de otro usuario (CLIENT)
- **WHEN** un CLIENT intenta consultar el pago de un pedido que no le pertenece
- **THEN** responde HTTP 404 con `{ "code": "PEDIDO_NOT_FOUND" }` (no filtrar existencia entre usuarios)

#### Scenario: ADMIN puede consultar cualquier pago
- **WHEN** un usuario con rol ADMIN llama `GET /api/v1/pagos/{pedido_id}` de cualquier usuario
- **THEN** responde HTTP 200 si existe la fila de pago

### Requirement: Confirmar pedido solo vía webhook (RN-FS02)
La transición `PENDIENTE → CONFIRMADO` SHALL ser ejecutada exclusivamente por el `PagoService` al procesar un IPN de MercadoPago aprobado. El endpoint `PATCH /pedidos/{id}/estado` SHALL rechazar con HTTP 422 cualquier intento de transición manual a `CONFIRMADO`.

#### Scenario: Intento manual de confirmación
- **WHEN** un admin envía `PATCH /api/v1/pedidos/42/estado` con `{ "nuevo_estado": "CONFIRMADO" }`
- **THEN** responde HTTP 422 con `{ "code": "TRANSICION_NO_PERMITIDA", "detail": "CONFIRMADO solo puede ser alcanzado vía webhook de pago" }`

#### Scenario: Confirmación automática vía webhook
- **WHEN** el webhook procesa un pago aprobado para el pedido 42
- **THEN** el pedido 42 transiciona a CONFIRMADO correctamente (sin pasar por el endpoint PATCH)
