# direcciones-backend Specification

## Purpose
Address management backend — CRUD endpoints for authenticated users' delivery addresses, with soft delete, principal invariant enforcement, and atomic principal-swap on promotion.

## ADDED Requirements

### Requirement: Listar direcciones propias del cliente autenticado
El sistema SHALL exponer `GET /api/v1/direcciones` que devuelve la lista de direcciones activas (con `deleted_at IS NULL`) del usuario autenticado. Requiere autenticación. La respuesta SHALL ordenar las direcciones con la principal primero y luego por `id` ascendente.

#### Scenario: Cliente con direcciones
- **WHEN** un cliente autenticado llama `GET /api/v1/direcciones`
- **THEN** responde HTTP 200 con `[DireccionRead]` conteniendo solo sus direcciones activas, con la `es_principal=true` en primera posición

#### Scenario: Cliente sin direcciones
- **WHEN** un cliente autenticado sin direcciones registradas llama el endpoint
- **THEN** responde HTTP 200 con `[]`

#### Scenario: Sin autenticación
- **WHEN** se llama sin token
- **THEN** responde HTTP 401 con `{ "code": "NOT_AUTHENTICATED" }`

#### Scenario: Aislamiento entre usuarios
- **WHEN** el cliente A llama el endpoint estando autenticado
- **THEN** la respuesta NO incluye direcciones del cliente B aunque existan en la base

### Requirement: Crear dirección — primera = principal automática (RN-DI01)
El sistema SHALL exponer `POST /api/v1/direcciones` que crea una dirección para el usuario autenticado. Si el usuario no tenía ninguna dirección activa previa, la nueva dirección SHALL marcarse automáticamente con `es_principal=true` ignorando el valor del body.

#### Scenario: Primera dirección del usuario
- **WHEN** un cliente sin direcciones envía `POST /api/v1/direcciones` con body válido (con o sin `es_principal` en el body)
- **THEN** responde HTTP 201 con la dirección creada y `es_principal=true`

#### Scenario: N-ésima dirección, body sin promoción
- **WHEN** un cliente con direcciones existentes envía `POST` con `es_principal=false` (o sin el campo)
- **THEN** responde HTTP 201 con la dirección creada y `es_principal=false`; la dirección principal previa permanece sin cambios

#### Scenario: Validación de campos requeridos
- **WHEN** el body omite `calle`, `numero`, `ciudad`, `provincia` o `codigo_postal`
- **THEN** responde HTTP 422 con `{ "code": "VALIDATION_ERROR", "field": "<campo_faltante>" }`

#### Scenario: Sin autenticación
- **WHEN** se llama sin token
- **THEN** responde HTTP 401

### Requirement: Actualizar dirección
El sistema SHALL exponer `PUT /api/v1/direcciones/{id}` que actualiza los campos editables de una dirección del usuario autenticado. El flag `es_principal` NO se cambia por este endpoint (se usa el PATCH dedicado).

#### Scenario: Actualización exitosa
- **WHEN** el dueño envía `PUT /api/v1/direcciones/{id}` con campos válidos
- **THEN** responde HTTP 200 con la dirección actualizada; `es_principal` queda igual que antes aunque venga en el body

#### Scenario: Dirección de otro usuario
- **WHEN** un cliente intenta actualizar una dirección cuyo `usuario_id` no coincide con el suyo
- **THEN** responde HTTP 404 con `{ "code": "DIRECCION_NOT_FOUND" }` (no se filtra existencia entre usuarios)

#### Scenario: Dirección inexistente o eliminada
- **WHEN** el id no existe o tiene `deleted_at` no nulo
- **THEN** responde HTTP 404 con `{ "code": "DIRECCION_NOT_FOUND" }`

### Requirement: Cambiar dirección principal (RN-DI02)
El sistema SHALL exponer `PATCH /api/v1/direcciones/{id}/principal` que marca la dirección indicada como principal del usuario autenticado y desmarca automáticamente la dirección que era principal previamente, en la misma transacción.

#### Scenario: Cambio exitoso
- **WHEN** el dueño llama `PATCH /api/v1/direcciones/{id}/principal` sobre una dirección activa propia que NO es principal
- **THEN** responde HTTP 200; la dirección indicada queda con `es_principal=true` y la dirección que era principal queda con `es_principal=false`

#### Scenario: Idempotencia
- **WHEN** el dueño llama el endpoint sobre una dirección que ya es principal
- **THEN** responde HTTP 200 sin cambios; sigue habiendo exactamente una principal

#### Scenario: Dirección de otro usuario
- **WHEN** un cliente intenta promocionar una dirección que no le pertenece
- **THEN** responde HTTP 404 con `{ "code": "DIRECCION_NOT_FOUND" }`

#### Scenario: Dirección eliminada
- **WHEN** la dirección tiene `deleted_at` no nulo
- **THEN** responde HTTP 404 con `{ "code": "DIRECCION_NOT_FOUND" }`

### Requirement: Eliminar dirección (soft delete)
El sistema SHALL exponer `DELETE /api/v1/direcciones/{id}` que realiza soft delete (set `deleted_at`) sobre una dirección del usuario autenticado. Una dirección principal solo puede eliminarse si es la única dirección activa del usuario.

#### Scenario: Eliminación de dirección no principal
- **WHEN** el dueño elimina una dirección con `es_principal=false`
- **THEN** responde HTTP 204; la dirección queda con `deleted_at` no nulo y no aparece más en listados

#### Scenario: Eliminación de la única dirección
- **WHEN** el dueño elimina su única dirección activa (que es principal)
- **THEN** responde HTTP 204; el usuario queda sin direcciones activas

#### Scenario: Intento de eliminar principal con otras direcciones activas
- **WHEN** el dueño intenta eliminar su dirección principal teniendo al menos otra dirección activa
- **THEN** responde HTTP 400 con `{ "code": "PRINCIPAL_CANNOT_DELETE", "detail": "Promocioná otra dirección como principal antes de eliminar esta" }`

#### Scenario: Dirección de otro usuario
- **WHEN** un cliente intenta eliminar una dirección que no le pertenece
- **THEN** responde HTTP 404 con `{ "code": "DIRECCION_NOT_FOUND" }`

#### Scenario: Dirección ya eliminada
- **WHEN** el id corresponde a una dirección con `deleted_at` no nulo
- **THEN** responde HTTP 404 con `{ "code": "DIRECCION_NOT_FOUND" }`

### Requirement: Invariante "máximo una dirección principal por usuario"
El sistema SHALL garantizar, a nivel de service, que para todo usuario existe a lo sumo una dirección activa con `es_principal=true` en todo momento.

#### Scenario: Tras crear primera dirección
- **WHEN** un cliente sin direcciones crea la primera
- **THEN** existe exactamente una dirección con `es_principal=true` para ese usuario

#### Scenario: Tras cambiar principal
- **WHEN** un cliente con N direcciones (1 principal) hace PATCH principal sobre otra
- **THEN** sigue existiendo exactamente una dirección con `es_principal=true` para ese usuario
