## 1. Backend — Módulo `productos`

- [x] 1.1 Crear `backend/app/modules/productos/model.py` — clase `Producto` SQLModel con `id`, `nombre`, `descripcion`, `precio` (Decimal), `stock` (int), `disponible` (bool), `deleted_at`; tablas junction `ProductoCategoria` y `ProductoIngrediente`
- [x] 1.2 Crear `backend/app/modules/productos/schemas.py` — `ProductoCreate` (con `categoria_ids: list[int]`, `ingrediente_ids: list[int]`), `ProductoUpdate`, `ProductoRead` (con `categorias: list[CategoriaRead]`, `ingredientes: list[IngredienteRead]`), `StockUpdate`, `DisponibilidadUpdate`
- [x] 1.3 Crear `backend/app/modules/productos/repository.py` — hereda `BaseRepository[Producto]`; métodos: `get_with_relations(id)`, `list_filtered(page, size, categoria_id, q, excluir_alergenos, disponible)`, `set_relaciones(session, producto_id, categoria_ids, ingrediente_ids)`, `get_ingredientes(id)`
- [x] 1.4 Crear `backend/app/modules/productos/service.py` — métodos: `list_all(uow, params)`, `get_by_id(uow, id)`, `create(uow, body)`, `update(uow, id, body)`, `patch_disponibilidad(uow, id, body)`, `patch_stock(uow, id, body)`, `delete(uow, id)`, `get_ingredientes(uow, id)`; validar existencia de categoria_ids e ingrediente_ids
- [x] 1.5 Crear `backend/app/modules/productos/router.py` — endpoints: `GET /productos`, `GET /productos/{id}`, `POST /productos`, `PUT /productos/{id}`, `PATCH /productos/{id}/disponibilidad`, `PATCH /productos/{id}/stock`, `DELETE /productos/{id}`, `GET /productos/{id}/ingredientes`
- [x] 1.6 Registrar router de productos en `backend/app/main.py` con prefix `/api/v1`

## 2. Backend — Extensión módulo `usuarios` (perfil propio)

- [x] 2.1 Agregar schemas en `backend/app/modules/usuarios/schemas.py`: `UsuarioMeRead` (sin `password_hash`), `UsuarioMeUpdate` (solo `nombre` y `apellido`), `PasswordChangeRequest` (`password_actual`, `password_nuevo`, `password_nuevo_confirmar`)
- [x] 2.2 Agregar métodos en `backend/app/modules/usuarios/service.py`: `get_me(uow, user_id)`, `update_me(uow, user_id, body)`, `change_password(uow, user_id, body)` con verificación de `password_actual` via bcrypt y validación de confirmación
- [x] 2.3 Agregar endpoints en `backend/app/modules/usuarios/router.py`: `GET /usuarios/me`, `PUT /usuarios/me`, `PATCH /usuarios/me/password`; todos requieren `get_current_user` como dependencia

## 3. Frontend — Tipos y API endpoints

- [x] 3.1 Crear `frontend/src/types/productos.ts` — tipos `ProductoRead`, `ProductoCreate`, `ProductoUpdate`, `StockUpdate`, `DisponibilidadUpdate`, `ProductoListResponse`
- [x] 3.2 Crear `frontend/src/api/endpoints/productos.ts` — funciones: `getProductos(params)`, `getProductoById(id)`, `getProductoIngredientes(id)`, `createProducto(data)`, `updateProducto(id, data)`, `patchDisponibilidad(id, data)`, `patchStock(id, data)`, `deleteProducto(id)`
- [x] 3.3 Extender `frontend/src/api/endpoints/usuarios.ts` — agregar `getMe()`, `updateMe(data: UsuarioMeUpdate)`, `changePassword(data: PasswordChangeRequest)`
- [x] 3.4 Crear o extender `frontend/src/types/usuarios.ts` — `UsuarioMeRead`, `UsuarioMeUpdate`, `PasswordChangeRequest`

## 4. Frontend — Hooks TanStack Query (catálogo y perfil)

- [x] 4.1 Crear `frontend/src/features/catalogo/hooks/useProductos.ts` — `useProductos(params)` con `useQuery`; params como dependencia del query key para refetch automático al cambiar filtros
- [x] 4.2 Crear `frontend/src/features/catalogo/hooks/useProducto.ts` — `useProducto(id)` con `useQuery`
- [x] 4.3 Crear `frontend/src/features/auth/hooks/usePerfil.ts` — `useMe()` (useQuery), `useUpdateMe()` (useMutation con invalidación de `['me']`), `useChangePassword()` (useMutation)

## 5. Frontend — Feature `catalogo`

- [x] 5.1 Crear `frontend/src/features/catalogo/components/ProductoCard.tsx` — muestra nombre, descripción truncada a 2 líneas, precio formateado en ARS, badges de alérgenos con color distinto, overlay "No disponible" si `disponible=false`
- [x] 5.2 Crear `frontend/src/features/catalogo/components/FiltrosBarra.tsx` — selector de categoría (usa `useCategoriaTree` de la feature admin o un hook compartido), input de búsqueda con debounce 300ms usando `useState` + `useEffect`, botón "Limpiar filtros"
- [x] 5.3 Crear `frontend/src/features/catalogo/components/CatalogoGrid.tsx` — grid responsive (3 cols desktop, 2 tablet, 1 mobile), skeleton loaders mientras `isLoading`, mensaje de vacío, toast en error
- [x] 5.4 Crear `frontend/src/features/catalogo/components/Paginacion.tsx` — botones Anterior/Siguiente y páginas numéricas, ocultar componente si `total <= size`
- [x] 5.5 Crear `frontend/src/pages/CatalogoPage.tsx` — ruta pública `/catalogo`, maneja estado de filtros con `useState`, pasa params a `CatalogoGrid` y `FiltrosBarra`
- [x] 5.6 Exportar componentes y hooks desde `frontend/src/features/catalogo/index.ts`
- [x] 5.7 Agregar ruta `/catalogo` (o `/`) en React Router DOM como ruta pública

## 6. Frontend — Feature `auth` (perfil)

- [x] 6.1 Crear `frontend/src/features/auth/components/PerfilForm.tsx` — TanStack Form con campos `nombre` y `apellido` pre-poblados desde `useMe()`, submit llama `useUpdateMe()`, toast de éxito, deshabilitar botón durante mutación
- [x] 6.2 Crear `frontend/src/features/auth/components/CambiarPasswordForm.tsx` — TanStack Form con campos `password_actual`, `password_nuevo`, `password_nuevo_confirmar`; validación inline de confirmación y longitud ≥ 8; submit llama `useChangePassword()`, toast de éxito/error, limpiar campos al éxito
- [x] 6.3 Crear `frontend/src/pages/PerfilPage.tsx` — ruta protegida `/perfil`, renderiza `PerfilForm` y `CambiarPasswordForm` en secciones separadas
- [x] 6.4 Agregar ruta `/perfil` en React Router DOM protegida con `ProtectedRoute` (roles: CLIENT, ADMIN, STOCK, PEDIDOS)
- [x] 6.5 Agregar link a "Mi Perfil" en el `Navbar` cuando el usuario está autenticado

## 7. Tests backend

- [x] 7.1 Crear `backend/tests/test_productos.py` — tests: listar sin filtros, filtro por categoría, búsqueda textual, exclusión alérgenos, filtro disponible, crear producto, actualizar, patch disponibilidad, patch stock, stock negativo, eliminar, 404 en id inexistente, crear con categoría inexistente
- [x] 7.2 Crear `backend/tests/test_perfil.py` — tests: GET /usuarios/me autenticado, GET sin auth (401), PUT /me actualización exitosa, PUT campos vacíos (422), PATCH /me/password exitoso, contraseña actual incorrecta (400), confirmación no coincide (422), nueva contraseña débil (422)
