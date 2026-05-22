## ADDED Requirements

### Requirement: Listar árbol de categorías
El sistema SHALL exponer `GET /api/v1/categorias` que devuelve todas las categorías activas (no eliminadas) en estructura árbol, con subcategorías anidadas en el campo `subcategorias`.

#### Scenario: Árbol con categorías activas
- **WHEN** se llama `GET /api/v1/categorias`
- **THEN** responde HTTP 200 con lista de categorías raíz, cada una con su lista `subcategorias` anidada

#### Scenario: Sin categorías
- **WHEN** no existen categorías activas
- **THEN** responde HTTP 200 con lista vacía `[]`

### Requirement: Obtener detalle de categoría
El sistema SHALL exponer `GET /api/v1/categorias/{id}` que devuelve la categoría con sus subcategorías directas.

#### Scenario: Categoría existente
- **WHEN** se llama `GET /api/v1/categorias/{id}` con id válido
- **THEN** responde HTTP 200 con la categoría y su lista de subcategorías directas

#### Scenario: Categoría no encontrada
- **WHEN** se llama `GET /api/v1/categorias/{id}` con id inexistente
- **THEN** responde HTTP 404 con `{ "detail": "Categoría no encontrada", "code": "CATEGORIA_NOT_FOUND" }`

### Requirement: Crear categoría (ADMIN)
El sistema SHALL exponer `POST /api/v1/categorias` restringido al rol ADMIN para crear una nueva categoría.

#### Scenario: Creación exitosa sin padre
- **WHEN** ADMIN envía `POST /api/v1/categorias` con `{ "nombre": "Lácteos" }`
- **THEN** responde HTTP 201 con la categoría creada, `parent_id: null`

#### Scenario: Creación exitosa con padre
- **WHEN** ADMIN envía `POST /api/v1/categorias` con `{ "nombre": "Quesos", "parent_id": 1 }`
- **THEN** responde HTTP 201 con la categoría creada y `parent_id: 1`

#### Scenario: Padre inexistente
- **WHEN** ADMIN envía `parent_id` que no existe
- **THEN** responde HTTP 400 con `{ "detail": "Categoría padre no encontrada", "code": "PARENT_NOT_FOUND" }`

#### Scenario: Sin autenticación o rol insuficiente
- **WHEN** usuario sin rol ADMIN intenta crear
- **THEN** responde HTTP 403

### Requirement: Actualizar categoría (ADMIN)
El sistema SHALL exponer `PUT /api/v1/categorias/{id}` restringido al rol ADMIN para actualizar nombre o padre de una categoría.

#### Scenario: Actualización exitosa
- **WHEN** ADMIN envía `PUT /api/v1/categorias/{id}` con campos válidos
- **THEN** responde HTTP 200 con la categoría actualizada

#### Scenario: Categoría no encontrada
- **WHEN** id no existe
- **THEN** responde HTTP 404 con `{ "code": "CATEGORIA_NOT_FOUND" }`

### Requirement: Eliminar categoría con soft delete (ADMIN)
El sistema SHALL exponer `DELETE /api/v1/categorias/{id}` restringido al rol ADMIN que realiza soft delete.

#### Scenario: Eliminación exitosa
- **WHEN** ADMIN elimina categoría sin productos activos y sin subcategorías activas
- **THEN** responde HTTP 204 y la categoría queda con `deleted_at` no nulo

#### Scenario: Categoría con productos activos (RN-CA03)
- **WHEN** la categoría tiene productos activos asociados
- **THEN** responde HTTP 400 con `{ "detail": "No se puede eliminar una categoría con productos activos", "code": "RN_CA03" }`

#### Scenario: Categoría con subcategorías activas
- **WHEN** la categoría tiene subcategorías no eliminadas
- **THEN** responde HTTP 400 con `{ "detail": "No se puede eliminar una categoría con subcategorías activas", "code": "CATEGORIA_HAS_CHILDREN" }`
