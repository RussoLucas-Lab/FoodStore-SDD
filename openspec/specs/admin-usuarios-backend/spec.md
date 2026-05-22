## ADDED Requirements

### Requirement: Listar usuarios (ADMIN)
El sistema SHALL exponer `GET /api/v1/admin/usuarios` paginado (`page`, `size`) con filtros opcionales `q` (búsqueda en nombre, apellido, email) y `activo` (bool). Restringido al rol ADMIN.

#### Scenario: Lista paginada sin filtros
- **WHEN** ADMIN llama `GET /api/v1/admin/usuarios?page=1&size=20`
- **THEN** responde HTTP 200 con `{ "items": [...], "total": N, "page": 1, "size": 20, "pages": P }` con todos los usuarios (activos e inactivos)

#### Scenario: Filtro por estado activo
- **WHEN** ADMIN llama con `?activo=true`
- **THEN** devuelve solo usuarios con `activo=true`

#### Scenario: Búsqueda textual
- **WHEN** ADMIN llama con `?q=lucas`
- **THEN** devuelve usuarios cuyo nombre, apellido o email contiene "lucas" (case-insensitive)

#### Scenario: Sin autenticación o rol insuficiente
- **WHEN** se llama sin token o con un rol distinto de ADMIN
- **THEN** responde HTTP 403

### Requirement: Actualizar datos de usuario (ADMIN)
El sistema SHALL exponer `PUT /api/v1/admin/usuarios/{id}` para que ADMIN edite `nombre`, `apellido` y `email` de cualquier usuario. No permite cambiar contraseña desde este endpoint.

#### Scenario: Actualización exitosa
- **WHEN** ADMIN envía `PUT /api/v1/admin/usuarios/{id}` con `nombre`, `apellido`, `email`
- **THEN** responde HTTP 200 con el usuario actualizado

#### Scenario: Email duplicado
- **WHEN** el email enviado ya está en uso por otro usuario
- **THEN** responde HTTP 409 con `{ "detail": "Email ya registrado", "code": "EMAIL_DUPLICATE" }`

#### Scenario: Usuario no encontrado
- **WHEN** el `id` no existe
- **THEN** responde HTTP 404

### Requirement: Asignar roles a usuario (ADMIN) — RN-RB03, RN-RB04
El sistema SHALL exponer `PATCH /api/v1/admin/usuarios/{id}/roles` para reemplazar el conjunto de roles de un usuario. Aplica reglas RN-RB03 (no puede haber cero ADMINs activos) y RN-RB04 (no automodificarse).

#### Scenario: Asignación exitosa
- **WHEN** ADMIN envía `PATCH /api/v1/admin/usuarios/{id}/roles` con `{ "roles": ["STOCK", "PEDIDOS"] }`
- **THEN** responde HTTP 200 con el usuario y sus nuevos roles

#### Scenario: RN-RB03 — último ADMIN
- **WHEN** se intenta quitar el rol ADMIN del único administrador activo
- **THEN** responde HTTP 422 con `{ "detail": "No puede haber cero administradores activos", "code": "LAST_ADMIN" }`

#### Scenario: RN-RB04 — automodificación
- **WHEN** ADMIN intenta cambiar sus propios roles
- **THEN** responde HTTP 403 con `{ "detail": "No puede modificar sus propios roles", "code": "SELF_ROLE_CHANGE" }`

#### Scenario: Rol inválido
- **WHEN** se envía un nombre de rol que no existe en la BD
- **THEN** responde HTTP 400 con `{ "detail": "Rol no válido", "code": "ROL_INVALID" }`

### Requirement: Activar/desactivar usuario (ADMIN)
El sistema SHALL exponer `PATCH /api/v1/admin/usuarios/{id}/activar` para toggle del campo `activo`. Protege que el último ADMIN activo no sea desactivado.

#### Scenario: Desactivar usuario
- **WHEN** ADMIN envía `PATCH /api/v1/admin/usuarios/{id}/activar` con `{ "activo": false }`
- **THEN** responde HTTP 200 con el usuario actualizado con `activo: false`

#### Scenario: Reactivar usuario
- **WHEN** ADMIN envía con `{ "activo": true }`
- **THEN** responde HTTP 200 con `activo: true`

#### Scenario: Último ADMIN activo no puede desactivarse
- **WHEN** se intenta desactivar al único ADMIN activo
- **THEN** responde HTTP 422 con `{ "detail": "No puede desactivar al único administrador activo", "code": "LAST_ADMIN" }`

#### Scenario: Sin autenticación o rol insuficiente
- **WHEN** se llama sin token o con rol distinto de ADMIN
- **THEN** responde HTTP 403
