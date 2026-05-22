# auth-backend Specification

## Purpose
TBD - created by archiving change sprint-1-auth. Update Purpose after archive.
## Requirements
### Requirement: Registro de usuarios cliente

El sistema SHALL exponer `POST /api/v1/auth/register` que crea un usuario con rol `CLIENT` asignado automáticamente, hasheando la contraseña con bcrypt (cost ≥ 12). El rol NO SHALL aceptarse desde el body del request.

#### Scenario: Registro exitoso

- **WHEN** un cliente envía `POST /api/v1/auth/register` con `email`, `password` (≥ 8 caracteres), `nombre` y `apellido` válidos
- **THEN** el sistema responde `201 Created` con el usuario creado (sin `password_hash`), persiste el usuario con rol `CLIENT` y un `password_hash` bcrypt verificable

#### Scenario: Email ya registrado

- **WHEN** un cliente intenta registrarse con un email que ya existe en la base de datos
- **THEN** el sistema responde `409 Conflict` con body RFC 7807 `{ "detail": "El email ya está registrado", "code": "EMAIL_ALREADY_EXISTS", "field": "email" }`

#### Scenario: Intento de escalar rol desde el body

- **WHEN** el body del registro incluye `rol: "ADMIN"` (o cualquier otro rol)
- **THEN** el sistema ignora ese campo y crea el usuario con rol `CLIENT`

#### Scenario: Contraseña débil

- **WHEN** el body envía una `password` de menos de 8 caracteres
- **THEN** el sistema responde `422 Unprocessable Entity` con `code: "VALIDATION_ERROR"` y `field: "password"`

### Requirement: Login con emisión de tokens

El sistema SHALL exponer `POST /api/v1/auth/login` que recibe `email` y `password`, valida credenciales y emite un access token JWT HS256 de 30 minutos y un refresh token opaco/JWT de 7 días persistido en la tabla `refresh_tokens`. La respuesta de error NO SHALL distinguir entre "email no existe" y "contraseña incorrecta".

#### Scenario: Login exitoso

- **WHEN** un usuario envía credenciales válidas
- **THEN** el sistema responde `200 OK` con `{ access_token, refresh_token, token_type: "bearer", expires_in: 1800 }` y registra el `jti` del refresh token en `refresh_tokens` con `expires_at = now + 7d`

#### Scenario: Credenciales inválidas (email inexistente)

- **WHEN** se envía un email que no existe
- **THEN** el sistema responde `401 Unauthorized` con `{ "detail": "Credenciales inválidas", "code": "INVALID_CREDENTIALS" }` (sin revelar que el email no existe)

#### Scenario: Credenciales inválidas (password incorrecto)

- **WHEN** el email existe pero la `password` no verifica contra el hash
- **THEN** el sistema responde con el MISMO `401` y el MISMO `code: "INVALID_CREDENTIALS"` que en el caso anterior

#### Scenario: Rate limit superado

- **WHEN** una misma IP envía un 6° intento de login dentro de una ventana de 15 minutos
- **THEN** el sistema responde `429 Too Many Requests` con `code: "RATE_LIMIT_EXCEEDED"` y header `Retry-After`

### Requirement: Refresh con rotación

El sistema SHALL exponer `POST /api/v1/auth/refresh` que acepta un refresh token vigente, lo marca como revocado y emite un par nuevo de tokens. Si el refresh token recibido ya está revocado, el sistema SHALL revocar TODOS los refresh tokens del usuario (defensa anti-replay).

#### Scenario: Refresh exitoso

- **WHEN** el cliente envía un refresh token válido y no revocado
- **THEN** el sistema responde `200 OK` con un nuevo `access_token` y un nuevo `refresh_token`, marca el token anterior con `revoked_at = now` y persiste el nuevo `jti`

#### Scenario: Refresh token expirado

- **WHEN** el cliente envía un refresh token cuya `expires_at` es anterior a `now`
- **THEN** el sistema responde `401 Unauthorized` con `code: "REFRESH_TOKEN_EXPIRED"`

#### Scenario: Replay de refresh token revocado

- **WHEN** el cliente envía un refresh token cuyo `revoked_at IS NOT NULL`
- **THEN** el sistema responde `401 Unauthorized` con `code: "REFRESH_TOKEN_REUSED"` y marca con `revoked_at = now` TODOS los refresh tokens del usuario asociado al token (forzando re-login global)

### Requirement: Logout

El sistema SHALL exponer `POST /api/v1/auth/logout` (autenticado) que revoca el refresh token enviado en el body o asociado al usuario actual.

#### Scenario: Logout exitoso

- **WHEN** un usuario autenticado envía `POST /api/v1/auth/logout` con su refresh token
- **THEN** el sistema responde `204 No Content` y el refresh token queda con `revoked_at = now` (futuros usos devuelven `401 REFRESH_TOKEN_REUSED`)

#### Scenario: Logout sin token válido

- **WHEN** se envía logout sin access token o con uno inválido
- **THEN** el sistema responde `401 Unauthorized` con `code: "UNAUTHORIZED"`

### Requirement: Usuario actual

El sistema SHALL exponer `GET /api/v1/auth/me` que requiere access token y devuelve los datos públicos del usuario actual incluyendo su rol.

#### Scenario: /me con token válido

- **WHEN** el cliente envía `GET /api/v1/auth/me` con `Authorization: Bearer <access_token>` válido
- **THEN** el sistema responde `200 OK` con `{ id, email, nombre, apellido, rol, fecha_alta }` (sin `password_hash`)

#### Scenario: /me con token expirado

- **WHEN** el access token está expirado
- **THEN** el sistema responde `401 Unauthorized` con `code: "ACCESS_TOKEN_EXPIRED"`

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

### Requirement: Autorización por rol (RBAC)

El sistema SHALL proveer una dependencia FastAPI `require_role(roles: list[str])` que decode el JWT, valida la firma y expiración, y rechaza si el `rol` del usuario no está en la lista. La dependencia SHALL usarse en cualquier endpoint protegido.

#### Scenario: Acceso permitido por rol

- **WHEN** un usuario con rol `ADMIN` invoca un endpoint protegido con `require_role(["ADMIN"])`
- **THEN** el endpoint ejecuta normalmente y retorna su respuesta de éxito

#### Scenario: Acceso denegado por rol insuficiente

- **WHEN** un usuario con rol `CLIENT` invoca un endpoint protegido con `require_role(["ADMIN"])`
- **THEN** el sistema responde `403 Forbidden` con `code: "INSUFFICIENT_ROLE"`

#### Scenario: Token ausente

- **WHEN** se invoca un endpoint protegido sin header `Authorization`
- **THEN** el sistema responde `401 Unauthorized` con `code: "MISSING_TOKEN"`

### Requirement: Formato de error RFC 7807

Toda respuesta de error 4xx/5xx del módulo auth SHALL seguir el formato `{ "detail": "<mensaje human-readable>", "code": "<UPPER_SNAKE>", "field": "<opcional>" }`.

#### Scenario: Error de validación con field

- **WHEN** se rechaza un campo del request por validación
- **THEN** el body de error incluye `field` con el nombre exacto del campo (`email`, `password`, etc.)

#### Scenario: Error sin field específico

- **WHEN** el error no corresponde a un campo (p.ej. rate limit, token expirado)
- **THEN** el body de error omite `field` y conserva `detail` + `code`

