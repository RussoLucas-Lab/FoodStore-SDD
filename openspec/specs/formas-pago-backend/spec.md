## ADDED Requirements

### Requirement: Listar formas de pago habilitadas
El sistema SHALL exponer `GET /api/v1/formas-pago` que devuelve la lista de formas de pago habilitadas (`habilitado=true`), ordenadas por `codigo` ascendente. Requiere autenticación. Devuelve `[FormaPagoRead]` con campos `codigo` y `descripcion`.

#### Scenario: Cliente autenticado obtiene lista
- **WHEN** un usuario autenticado llama `GET /api/v1/formas-pago`
- **THEN** responde HTTP 200 con `[{"codigo":"EFECTIVO","descripcion":"..."}, {"codigo":"MERCADOPAGO","descripcion":"..."}, {"codigo":"TRANSFERENCIA","descripcion":"..."}]` (orden alfabético por código)

#### Scenario: Solo formas habilitadas
- **GIVEN** una forma de pago con `codigo="LEGACY"` y `habilitado=false`
- **WHEN** un usuario autenticado llama el endpoint
- **THEN** la respuesta NO incluye "LEGACY"

#### Scenario: Sin autenticación
- **WHEN** se llama sin token
- **THEN** responde HTTP 401 con `{ "code": "NOT_AUTHENTICATED" }`

#### Scenario: Lista vacía
- **WHEN** no existen formas de pago con `habilitado=true`
- **THEN** responde HTTP 200 con `[]`
