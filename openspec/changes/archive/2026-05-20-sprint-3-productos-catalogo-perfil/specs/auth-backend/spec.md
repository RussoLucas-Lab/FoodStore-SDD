## ADDED Requirements

### Requirement: Obtener perfil propio (CLIENT)
El sistema SHALL exponer `GET /api/v1/usuarios/me` que devuelve los datos del usuario autenticado (sin `password_hash`).

#### Scenario: Usuario autenticado
- **WHEN** un usuario autenticado llama `GET /api/v1/usuarios/me` con access token válido
- **THEN** responde HTTP 200 con `{ id, email, nombre, apellido, roles: [...] }` sin exponer `password_hash`

#### Scenario: Sin autenticación
- **WHEN** se llama sin access token o con token expirado
- **THEN** responde HTTP 401 con `{ "code": "UNAUTHORIZED" }`

### Requirement: Actualizar perfil propio (CLIENT)
El sistema SHALL exponer `PUT /api/v1/usuarios/me` que permite al usuario autenticado actualizar su `nombre` y `apellido`.

#### Scenario: Actualización exitosa
- **WHEN** un usuario autenticado envía `PUT /api/v1/usuarios/me` con `{ "nombre": "Juan", "apellido": "Pérez" }`
- **THEN** responde HTTP 200 con los datos actualizados

#### Scenario: Campos vacíos
- **WHEN** el body incluye `nombre` o `apellido` como string vacío
- **THEN** responde HTTP 422 con `{ "code": "VALIDATION_ERROR" }`

### Requirement: Cambiar contraseña propia (CLIENT)
El sistema SHALL exponer `PATCH /api/v1/usuarios/me/password` que permite al usuario autenticado cambiar su contraseña verificando primero la contraseña actual.

#### Scenario: Cambio exitoso
- **WHEN** un usuario autenticado envía `{ "password_actual": "...", "password_nuevo": "...", "password_nuevo_confirmar": "..." }` con `password_actual` correcto y `password_nuevo` ≥ 8 caracteres e igual a `password_nuevo_confirmar`
- **THEN** responde HTTP 200, actualiza el `password_hash` con bcrypt cost ≥ 12

#### Scenario: Contraseña actual incorrecta
- **WHEN** `password_actual` no coincide con el hash almacenado
- **THEN** responde HTTP 400 con `{ "detail": "Contraseña actual incorrecta", "code": "INVALID_PASSWORD" }`

#### Scenario: Confirmación no coincide
- **WHEN** `password_nuevo` y `password_nuevo_confirmar` son distintos
- **THEN** responde HTTP 422 con `{ "code": "VALIDATION_ERROR", "field": "password_nuevo_confirmar" }`

#### Scenario: Nueva contraseña débil
- **WHEN** `password_nuevo` tiene menos de 8 caracteres
- **THEN** responde HTTP 422 con `{ "code": "VALIDATION_ERROR", "field": "password_nuevo" }`
