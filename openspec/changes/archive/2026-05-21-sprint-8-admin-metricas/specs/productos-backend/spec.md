## MODIFIED Requirements

### Requirement: Listar productos con filtros y paginación
El sistema SHALL exponer `GET /api/v1/productos` que devuelve productos activos con paginación estándar y filtros opcionales combinables: `categoria_id` (int), `q` (búsqueda textual en nombre y descripción), `excluir_alergenos` (CSV de IDs de ingredientes alérgenos), `disponible` (bool), e `include_deleted` (bool, default `false` — solo honrado cuando el usuario autenticado tiene rol ADMIN). Acceso público para el resto de los parámetros.

#### Scenario: Lista paginada sin filtros
- **WHEN** se llama `GET /api/v1/productos?page=1&size=20`
- **THEN** responde HTTP 200 con `{ "items": [...], "total": N, "page": 1, "size": 20, "pages": P }` con productos que tienen `deleted_at IS NULL`

#### Scenario: Filtro por categoría
- **WHEN** se llama con `?categoria_id=3`
- **THEN** devuelve solo productos que tienen esa categoría asociada

#### Scenario: Búsqueda textual
- **WHEN** se llama con `?q=pizza`
- **THEN** devuelve productos cuyo nombre o descripción contiene "pizza" (case-insensitive)

#### Scenario: Exclusión de alérgenos
- **WHEN** se llama con `?excluir_alergenos=1,2`
- **THEN** devuelve solo productos que NO tienen los ingredientes con id 1 o 2

#### Scenario: Filtro por disponibilidad
- **WHEN** se llama con `?disponible=true`
- **THEN** devuelve solo productos con `disponible=true`

#### Scenario: ADMIN lista productos eliminados
- **WHEN** ADMIN llama con `?include_deleted=true`
- **THEN** responde HTTP 200 incluyendo productos con `deleted_at` no nulo junto a los activos

#### Scenario: No-ADMIN intenta include_deleted
- **WHEN** un usuario sin rol ADMIN (o sin token) envía `?include_deleted=true`
- **THEN** el parámetro es ignorado; la respuesta incluye solo productos activos (`deleted_at IS NULL`)
