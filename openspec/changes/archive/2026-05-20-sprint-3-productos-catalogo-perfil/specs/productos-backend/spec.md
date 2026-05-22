## ADDED Requirements

### Requirement: Listar productos con filtros y paginación
El sistema SHALL exponer `GET /api/v1/productos` que devuelve productos activos con paginación estándar y filtros opcionales combinables: `categoria_id` (int), `q` (búsqueda textual en nombre y descripción), `excluir_alergenos` (CSV de IDs de ingredientes alérgenos), `disponible` (bool). Acceso público (sin autenticación).

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

### Requirement: Obtener detalle de producto
El sistema SHALL exponer `GET /api/v1/productos/{id}` que devuelve el producto con su lista de categorías e ingredientes. Acceso público.

#### Scenario: Producto existente
- **WHEN** se llama `GET /api/v1/productos/{id}` con id válido y producto activo
- **THEN** responde HTTP 200 con el producto incluyendo campos `categorias: [CategoriaRead]` e `ingredientes: [IngredienteRead]`

#### Scenario: Producto no encontrado o eliminado
- **WHEN** el id no existe o tiene `deleted_at` no nulo
- **THEN** responde HTTP 404 con `{ "detail": "Producto no encontrado", "code": "PRODUCTO_NOT_FOUND" }`

### Requirement: Crear producto (ADMIN)
El sistema SHALL exponer `POST /api/v1/productos` restringido al rol ADMIN para crear un nuevo producto con sus relaciones a categorías e ingredientes.

#### Scenario: Creación exitosa
- **WHEN** ADMIN envía `POST /api/v1/productos` con `nombre`, `descripcion`, `precio` (decimal > 0), `stock` (int ≥ 0), `disponible` (bool), `categoria_ids: [int]`, `ingrediente_ids: [int]`
- **THEN** responde HTTP 201 con el producto creado incluyendo sus relaciones

#### Scenario: Categoría o ingrediente inexistente
- **WHEN** algún id en `categoria_ids` o `ingrediente_ids` no existe o está eliminado
- **THEN** responde HTTP 400 con `{ "detail": "Categoría o ingrediente no encontrado", "code": "RELATED_NOT_FOUND" }`

#### Scenario: Sin autenticación o rol insuficiente
- **WHEN** usuario sin rol ADMIN intenta crear
- **THEN** responde HTTP 403

### Requirement: Actualizar producto (ADMIN)
El sistema SHALL exponer `PUT /api/v1/productos/{id}` restringido al rol ADMIN para actualizar todos los campos del producto y reemplazar sus relaciones.

#### Scenario: Actualización exitosa
- **WHEN** ADMIN envía `PUT /api/v1/productos/{id}` con campos válidos
- **THEN** responde HTTP 200 con el producto actualizado; las listas `categoria_ids` e `ingrediente_ids` REEMPLAZAN las relaciones existentes

#### Scenario: Producto no encontrado
- **WHEN** id no existe o está eliminado
- **THEN** responde HTTP 404 con `{ "code": "PRODUCTO_NOT_FOUND" }`

### Requirement: Cambiar disponibilidad de producto (ADMIN / STOCK)
El sistema SHALL exponer `PATCH /api/v1/productos/{id}/disponibilidad` restringido a roles ADMIN y STOCK para activar o desactivar un producto sin modificar su stock.

#### Scenario: Toggle exitoso
- **WHEN** ADMIN o STOCK envía `PATCH /api/v1/productos/{id}/disponibilidad` con `{ "disponible": false }`
- **THEN** responde HTTP 200 con el producto actualizado y `disponible=false`

#### Scenario: Rol insuficiente
- **WHEN** un CLIENT intenta llamar al endpoint
- **THEN** responde HTTP 403

### Requirement: Actualizar stock de producto (ADMIN / STOCK)
El sistema SHALL exponer `PATCH /api/v1/productos/{id}/stock` restringido a roles ADMIN y STOCK para modificar la cantidad en stock.

#### Scenario: Actualización exitosa
- **WHEN** ADMIN o STOCK envía `PATCH /api/v1/productos/{id}/stock` con `{ "stock": 50 }`
- **THEN** responde HTTP 200 con el producto actualizado y `stock=50`

#### Scenario: Stock negativo
- **WHEN** el body incluye `stock` con valor negativo
- **THEN** responde HTTP 422 con `{ "code": "VALIDATION_ERROR", "field": "stock" }`

### Requirement: Eliminar producto con soft delete (ADMIN)
El sistema SHALL exponer `DELETE /api/v1/productos/{id}` restringido al rol ADMIN que realiza soft delete estableciendo `deleted_at`.

#### Scenario: Eliminación exitosa
- **WHEN** ADMIN llama `DELETE /api/v1/productos/{id}` con id válido
- **THEN** responde HTTP 204 y el producto queda con `deleted_at` no nulo; no aparece en listados públicos

#### Scenario: Producto no encontrado
- **WHEN** id no existe o ya está eliminado
- **THEN** responde HTTP 404 con `{ "code": "PRODUCTO_NOT_FOUND" }`

### Requirement: Listar ingredientes de un producto
El sistema SHALL exponer `GET /api/v1/productos/{id}/ingredientes` que devuelve la lista de ingredientes del producto. Acceso público.

#### Scenario: Producto con ingredientes
- **WHEN** se llama `GET /api/v1/productos/{id}/ingredientes`
- **THEN** responde HTTP 200 con `[IngredienteRead]` del producto

#### Scenario: Producto sin ingredientes
- **WHEN** el producto no tiene ingredientes asociados
- **THEN** responde HTTP 200 con lista vacía `[]`
