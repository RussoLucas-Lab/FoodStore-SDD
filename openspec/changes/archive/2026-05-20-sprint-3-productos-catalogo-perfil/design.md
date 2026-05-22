## Context

Tras el Sprint 2, el sistema cuenta con categorías e ingredientes completamente operativos. El módulo `productos` es la entidad central del e-commerce: referenciada en el catálogo público, en el carrito (Sprint 4) y en los detalles de pedido con patrón Snapshot (Sprint 5). El catálogo es la primera pantalla de valor real para el cliente final.

El módulo `usuarios` ya existe con registro y login. Este sprint extiende ese módulo con endpoints de gestión de perfil propio, sin crear un módulo nuevo.

## Goals / Non-Goals

**Goals:**
- CRUD completo de productos con relaciones M2M a categorías e ingredientes
- Endpoints de stock y disponibilidad con permisos diferenciados (ADMIN/STOCK)
- Soft delete en productos (nunca DELETE físico)
- Catálogo público paginado con filtros por categoría, búsqueda textual y exclusión de alérgenos
- Gestión de perfil propio: ver/editar nombre-apellido y cambiar contraseña

**Non-Goals:**
- Carrito de compras (Sprint 4)
- Pedidos y snapshots de precio (Sprint 5)
- Gestión de imágenes de producto (fuera de scope del TPI)
- Reseñas o ratings de productos

## Decisions

### D1 — Relaciones M2M en Producto via tablas junction

`ProductoCategoria` y `ProductoIngrediente` son tablas junction explícitas (no tablas implícitas de SQLModel). Esto permite controlar el ciclo de vida de las relaciones independientemente del producto.

**Alternativa descartada**: usar el helper `Relationship` de SQLModel con `link_model`. Se descarta porque las tablas junction ya están definidas en el modelo de datos del proyecto (ver `DATA_MODEL.md`) y SQLModel requiere clases explícitas para junction tables con campos adicionales.

### D2 — Campo `disponible` es explícito, no derivado de stock

`Producto.disponible: bool` es un campo propio del modelo, no derivado de `stock > 0`. Esto permite deshabilitar un producto manualmente aunque tenga stock (por ejemplo, por retiro temporal). El PATCH de stock no cambia automáticamente `disponible`.

**Alternativa descartada**: `disponible = stock > 0`. Descartada porque el admin necesita ocultar productos por razones operativas independientes del stock.

### D3 — Filtros del catálogo como query params opcionales

`GET /api/v1/productos` acepta `?categoria_id=`, `?q=` (búsqueda textual en nombre/descripción), `?excluir_alergenos=` (lista de IDs separados por coma), `?disponible=true`. Todos son opcionales y combinables. La paginación usa el estándar del proyecto: `?page=1&size=20`.

### D4 — Perfil en módulo `usuarios`, no módulo nuevo

Los endpoints `GET /api/v1/usuarios/me`, `PUT /api/v1/usuarios/me` y `PATCH /api/v1/usuarios/me/password` se agregan al router existente de `usuarios`. No se crea un módulo separado para perfil. El service de usuarios ya tiene acceso al hash de contraseña necesario para la validación de cambio de password.

### D5 — Frontend: catálogo usa TanStack Query, sin Zustand

El estado del catálogo (productos, filtros aplicados) es estado del servidor — se gestiona con `useQuery` de TanStack Query. Los filtros se mantienen en estado local del componente (useState) o en URL query params. No hay store Zustand para el catálogo.

## Risks / Trade-offs

- **[Riesgo] CTE recursiva de categorías en filtro de catálogo** → Para filtrar por categoría incluyendo subcategorías (e.g., "Lácteos" incluye "Quesos"), el query debe expandir el árbol. Mitigación: el repository de productos recibe directamente `categoria_id` y hace JOIN simple; la expansión del árbol es responsabilidad del cliente frontend que puede pasar un `categoria_id` específico.
- **[Riesgo] Cambio de contraseña sin verificación de sesión activa en otras dispositivos** → Mitigación: fuera de scope para Sprint 3; el logout global con revocación de refresh tokens se implementa en Sprint 6.
- **[Trade-off] `excluir_alergenos` como query param CSV** → Menos RESTful que un body, pero compatible con GET y permite bookmarks de URL. Aceptable para el scope del TPI.
