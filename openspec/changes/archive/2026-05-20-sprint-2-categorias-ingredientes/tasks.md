## 1. Backend — Módulo `categorias`

- [x] 1.1 Crear `backend/app/modules/categorias/model.py` — clase `Categoria` SQLModel con `id`, `nombre`, `parent_id`, `deleted_at`
- [x] 1.2 Crear `backend/app/modules/categorias/schemas.py` — `CategoriaCreate`, `CategoriaUpdate`, `CategoriaRead`, `CategoriaTreeRead` (con `subcategorias: list[CategoriaTreeRead]`)
- [x] 1.3 Crear `backend/app/modules/categorias/repository.py` — hereda `BaseRepository[Categoria]`, métodos: `get_tree()` (CTE recursiva), `get_with_subcategorias(id)`, `has_active_products(id)`, `has_active_children(id)`
- [x] 1.4 Crear `backend/app/modules/categorias/service.py` — métodos: `get_tree()`, `get_by_id(id)`, `create(uow, body)`, `update(uow, id, body)`, `delete(uow, id)` con validaciones RN-CA03 y subcategorías activas
- [x] 1.5 Crear `backend/app/modules/categorias/router.py` — endpoints: `GET /categorias`, `GET /categorias/{id}`, `POST /categorias`, `PUT /categorias/{id}`, `DELETE /categorias/{id}`
- [x] 1.6 Registrar router de categorías en `backend/app/main.py`

## 2. Backend — Módulo `ingredientes`

- [x] 2.1 Crear `backend/app/modules/ingredientes/model.py` — clase `Ingrediente` SQLModel con `id`, `nombre`, `es_alergeno`, `deleted_at`
- [x] 2.2 Crear `backend/app/modules/ingredientes/schemas.py` — `IngredienteCreate`, `IngredienteUpdate`, `IngredienteRead`
- [x] 2.3 Crear `backend/app/modules/ingredientes/repository.py` — hereda `BaseRepository[Ingrediente]`, método `get_by_nombre(nombre)` para validar duplicados
- [x] 2.4 Crear `backend/app/modules/ingredientes/service.py` — métodos: `list_all(uow, page, size, es_alergeno)`, `get_by_id(uow, id)`, `create(uow, body)`, `update(uow, id, body)`, `delete(uow, id)`; valida nombre duplicado en create
- [x] 2.5 Crear `backend/app/modules/ingredientes/router.py` — endpoints: `GET /ingredientes`, `GET /ingredientes/{id}`, `POST /ingredientes`, `PUT /ingredientes/{id}`, `DELETE /ingredientes/{id}`
- [x] 2.6 Registrar router de ingredientes en `backend/app/main.py`

## 3. Frontend — API endpoints

- [x] 3.1 Crear `frontend/src/api/endpoints/categorias.ts` — funciones: `getCategorias()`, `getCategoriaById(id)`, `createCategoria(data)`, `updateCategoria(id, data)`, `deleteCategoria(id)`
- [x] 3.2 Crear `frontend/src/api/endpoints/ingredientes.ts` — funciones: `getIngredientes(params)`, `getIngredienteById(id)`, `createIngrediente(data)`, `updateIngrediente(id, data)`, `deleteIngrediente(id)`
- [x] 3.3 Crear `frontend/src/types/categorias.ts` — tipos `CategoriaRead`, `CategoriaTreeRead`, `CategoriaCreate`, `CategoriaUpdate`
- [x] 3.4 Crear `frontend/src/types/ingredientes.ts` — tipos `IngredienteRead`, `IngredienteCreate`, `IngredienteUpdate`

## 4. Frontend — Hooks TanStack Query

- [x] 4.1 Crear `frontend/src/features/admin/hooks/useCategorias.ts` — `useCategoriaTree()`, `useCreateCategoria()`, `useUpdateCategoria()`, `useDeleteCategoria()`; invalidar query key tras mutaciones
- [x] 4.2 Crear `frontend/src/features/admin/hooks/useIngredientes.ts` — `useIngredientes(params)`, `useCreateIngrediente()`, `useUpdateIngrediente()`, `useDeleteIngrediente()`; invalidar query key tras mutaciones

## 5. Frontend — Componente CategoriaCRUD

- [x] 5.1 Crear `frontend/src/features/admin/components/CategoriaCRUD.tsx` — estructura base con árbol, botón "Nueva categoría" y skeleton loader
- [x] 5.2 Implementar árbol jerárquico recursivo: nodos expandibles con indentación por nivel, botones editar/agregar subcategoría/eliminar por nodo
- [x] 5.3 Implementar `CategoriaFormModal` — modal con TanStack Form, campo nombre y selector opcional de padre; modo crear y editar
- [x] 5.4 Implementar eliminación con modal de confirmación y manejo de error RN-CA03 con toast

## 6. Frontend — Componente IngredienteCRUD

- [x] 6.1 Crear `frontend/src/features/admin/components/IngredienteCRUD.tsx` — tabla/lista paginada con columnas nombre, badge alérgeno, acciones
- [x] 6.2 Implementar badge visual "Alérgeno" (color distinto) para `es_alergeno=true`
- [x] 6.3 Implementar filtro "Solo alérgenos" que llama al endpoint con `?es_alergeno=true`
- [x] 6.4 Implementar `IngredienteFormModal` — modal con TanStack Form, campos nombre y checkbox `es_alergeno`; modo crear y editar
- [x] 6.5 Implementar eliminación con modal de confirmación

## 7. Frontend — Integración en panel admin

- [x] 7.1 Agregar rutas `/admin/categorias` y `/admin/ingredientes` en React Router
- [x] 7.2 Agregar links a las rutas nuevas en el `AdminLayout` sidebar (sección "Catálogo")
- [x] 7.3 Crear páginas `AdminCategoriasPage` y `AdminIngredientesPage` que rendericen los respectivos CRUDs
- [x] 7.4 Exportar componentes y hooks desde `frontend/src/features/admin/index.ts`

## 8. Tests backend

- [x] 8.1 Crear `backend/tests/test_categorias.py` — tests: listar árbol, crear, crear con padre inválido, actualizar, eliminar, RN-CA03, subcategorías activas
- [x] 8.2 Crear `backend/tests/test_ingredientes.py` — tests: listar con filtro, crear, nombre duplicado, actualizar, eliminar, 404 en id inexistente
