## ADDED Requirements

### Requirement: Listar ingredientes
El sistema SHALL exponer `GET /api/v1/ingredientes` que devuelve todos los ingredientes activos con paginación estándar.

#### Scenario: Lista con ingredientes
- **WHEN** se llama `GET /api/v1/ingredientes?page=1&size=20`
- **THEN** responde HTTP 200 con `{ "items": [...], "total": N, "page": 1, "size": 20, "pages": P }`

#### Scenario: Filtro por alérgeno
- **WHEN** se llama `GET /api/v1/ingredientes?es_alergeno=true`
- **THEN** responde HTTP 200 con solo ingredientes donde `es_alergeno=true`

### Requirement: Obtener detalle de ingrediente
El sistema SHALL exponer `GET /api/v1/ingredientes/{id}` que devuelve el ingrediente por id.

#### Scenario: Ingrediente existente
- **WHEN** se llama con id válido
- **THEN** responde HTTP 200 con el ingrediente

#### Scenario: Ingrediente no encontrado
- **WHEN** id no existe
- **THEN** responde HTTP 404 con `{ "code": "INGREDIENTE_NOT_FOUND" }`

### Requirement: Crear ingrediente (ADMIN)
El sistema SHALL exponer `POST /api/v1/ingredientes` restringido al rol ADMIN.

#### Scenario: Creación exitosa sin alérgeno
- **WHEN** ADMIN crea ingrediente con `{ "nombre": "Harina", "es_alergeno": false }`
- **THEN** responde HTTP 201 con el ingrediente creado

#### Scenario: Creación exitosa como alérgeno
- **WHEN** ADMIN crea ingrediente con `{ "nombre": "Gluten", "es_alergeno": true }`
- **THEN** responde HTTP 201 con `es_alergeno: true`

#### Scenario: Nombre duplicado
- **WHEN** ya existe un ingrediente activo con el mismo nombre
- **THEN** responde HTTP 409 con `{ "code": "INGREDIENTE_DUPLICATE" }`

#### Scenario: Sin autorización
- **WHEN** usuario sin rol ADMIN intenta crear
- **THEN** responde HTTP 403

### Requirement: Actualizar ingrediente (ADMIN)
El sistema SHALL exponer `PUT /api/v1/ingredientes/{id}` restringido al rol ADMIN.

#### Scenario: Actualización exitosa
- **WHEN** ADMIN envía campos válidos
- **THEN** responde HTTP 200 con el ingrediente actualizado

#### Scenario: Ingrediente no encontrado
- **WHEN** id no existe
- **THEN** responde HTTP 404 con `{ "code": "INGREDIENTE_NOT_FOUND" }`

### Requirement: Eliminar ingrediente con soft delete (ADMIN)
El sistema SHALL exponer `DELETE /api/v1/ingredientes/{id}` restringido al rol ADMIN que realiza soft delete.

#### Scenario: Eliminación exitosa
- **WHEN** ADMIN elimina ingrediente
- **THEN** responde HTTP 204 y queda con `deleted_at` no nulo

#### Scenario: Ingrediente no encontrado
- **WHEN** id no existe
- **THEN** responde HTTP 404 con `{ "code": "INGREDIENTE_NOT_FOUND" }`
