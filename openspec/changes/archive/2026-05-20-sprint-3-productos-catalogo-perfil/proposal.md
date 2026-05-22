## Why

Con categorías e ingredientes disponibles (Sprint 2), el sistema ya puede modelar productos completos. El catálogo público —corazón del e-commerce— y el perfil de usuario son los dos flujos de valor visible para el cliente que habilitan los sprints siguientes (carrito, checkout, pagos).

## What Changes

- **Nuevo módulo `productos`** en el backend: CRUD completo con soft delete, gestión de relaciones con categorías e ingredientes, control de stock y disponibilidad.
- **Nuevos endpoints de stock/disponibilidad** con permisos diferenciados por rol (ADMIN vs STOCK).
- **Nueva feature `catalogo`** en el frontend: grid público paginado con filtros por categoría, búsqueda con debounce, exclusión de alérgenos y skeleton loaders.
- **Extensión de la feature `auth`** en el frontend: formularios de edición de perfil y cambio de contraseña del cliente.
- **Nuevos endpoints de perfil** en el backend (módulo `usuarios`): ver y actualizar datos propios.

## Capabilities

### New Capabilities

- `productos-backend`: CRUD de productos con relaciones a categorías e ingredientes, paginación con filtros, control de stock/disponibilidad, soft delete y snapshot de datos para pedidos futuros.
- `catalogo-frontend`: Feature pública de catálogo — grid de productos con filtros (categoría, búsqueda, alérgenos), paginación y skeleton loaders.
- `perfil-frontend`: Formularios de perfil del cliente logueado — ver/editar nombre y apellido, cambiar contraseña con validación.

### Modified Capabilities

- `auth-backend`: Agrega endpoints `GET /usuarios/me` (perfil propio) y `PUT /usuarios/me` (actualizar datos) y `PATCH /usuarios/me/password` (cambiar contraseña). Extensión de comportamiento sin breaking changes.

## Impact

- **Backend**: nuevo módulo `backend/app/modules/productos/` (model, schemas, repository, service, router). Extensión de `backend/app/modules/usuarios/` con endpoints de perfil. Registro en `main.py`.
- **Frontend**: nueva feature `frontend/src/features/catalogo/`. Nuevos componentes en `frontend/src/features/auth/` (PerfilForm, CambiarPasswordForm). Nuevos API endpoints en `frontend/src/api/endpoints/productos.ts` y `usuarios.ts`. Nuevas rutas en React Router.
- **Dependencias**: reutiliza tipos de categorías e ingredientes ya definidos en Sprint 2. Los schemas de productos incluyen `precio_snapshot` y `nombre_snapshot` como campos base para el patrón Snapshot que usará Sprint 5.
- **Sin breaking changes** en módulos anteriores.
