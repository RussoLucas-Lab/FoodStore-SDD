## Why

El catálogo de Food Store necesita una taxonomía de categorías jerárquica y un registro de ingredientes con flag de alérgenos antes de poder crear productos. Sin estas entidades base (EPIC 03 y EPIC 04), el módulo de productos del Sprint 3 no tiene datos de referencia válidos.

## What Changes

- Nuevo endpoint árbol de categorías con CTE recursiva (`GET /api/v1/categorias`)
- CRUD completo de categorías con soft delete y validación de productos activos (RN-CA03)
- CRUD completo de ingredientes con flag `es_alergeno` y soft delete
- Panel admin frontend: `CategoriaCRUD` con árbol jerárquico navegable
- Panel admin frontend: `IngredienteCRUD` con badge de alérgenos

## Capabilities

### New Capabilities

- `categorias-backend`: Módulo FastAPI `categorias` — modelo, repositorio, servicio y router con árbol recursivo y CRUD admin
- `ingredientes-backend`: Módulo FastAPI `ingredientes` — modelo, repositorio, servicio y router con CRUD y flag `es_alergeno`
- `admin-categorias-ingredientes-frontend`: Feature admin parcial — componentes `CategoriaCRUD` e `IngredienteCRUD` con TanStack Query

### Modified Capabilities

## Impact

- **Backend**: Nuevos módulos `backend/app/modules/categorias/` e `backend/app/modules/ingredientes/` (model, repository, schemas, service, router). Registro de routers en `main.py`.
- **Frontend**: Nuevos componentes en `frontend/src/features/admin/components/`. Nuevos hooks en `features/admin/hooks/`. Nuevos endpoints en `api/endpoints/`.
- **Base de datos**: Tablas `categoria` e `ingrediente` ya definidas en Sprint 0. No requiere nuevas migraciones Alembic.
- **Dependencias**: Sin dependencias nuevas. Requiere Sprint 1 (auth + `require_role`) completo.
