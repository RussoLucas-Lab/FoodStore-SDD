## Context

Sprint 2 construye los módulos `categorias` e `ingredientes` — entidades de referencia necesarias para el módulo `productos` (Sprint 3). Los modelos SQLModel (`Categoria`, `Ingrediente`) ya fueron creados en Sprint 0. El scaffold de módulos (router/service/repository/schemas) sigue el patrón Feature-First establecido. El frontend usa Feature-Sliced Design con TanStack Query para estado del servidor.

El módulo `categorias` requiere soporte de jerarquía (categoría padre ↔ subcategorías). La BD es SQLite en dev y PostgreSQL en prod; la CTE recursiva debe funcionar en ambas.

## Goals / Non-Goals

**Goals:**
- CRUD completo de categorías con árbol jerárquico y soft delete
- Validación de borrado: no se puede eliminar categoría con productos activos (RN-CA03)
- CRUD completo de ingredientes con flag `es_alergeno` y soft delete
- Componentes admin `CategoriaCRUD` e `IngredienteCRUD` con TanStack Query
- Autorización RBAC: solo ADMIN puede crear/editar/eliminar

**Non-Goals:**
- Asignación de categorías/ingredientes a productos (Sprint 3)
- Filtrado de catálogo por categoría (Sprint 3)
- Imágenes de categorías

## Decisions

### D-01: CTE recursiva para árbol de categorías

**Decisión**: Implementar `GET /categorias` con una CTE recursiva en SQL para construir el árbol completo en una sola query.

**Por qué**: El árbol puede tener profundidad variable. Una query recursiva evita N+1 y trae la jerarquía completa eficientemente. SQLite soporta CTEs recursivas desde 3.35.

**Alternativa descartada**: Múltiples queries con joins — genera N+1 y complica el ensamble del árbol en Python.

### D-02: Respuesta del árbol como lista plana con `parent_id`

**Decisión**: El endpoint devuelve lista plana `[{id, nombre, parent_id, nivel, subcategorias: [...]}]`. El ensamble del árbol se hace en Python (no en SQL).

**Por qué**: Más simple de serializar con Pydantic. El frontend puede renderizar árbol a partir de la lista plana o del campo `subcategorias` anidado.

### D-03: Soft delete con validación en Service

**Decisión**: `DELETE /categorias/{id}` hace soft delete (`deleted_at`). El Service verifica primero que no existan productos activos asociados; si los hay, lanza `HTTPException(400, "RN-CA03")`.

**Por qué**: Regla de negocio RN-CA03 explícita. La validación va en el Service (no en Repository) porque involucra lógica de negocio cross-módulo.

### D-04: Flag `es_alergeno` en ingredientes

**Decisión**: Campo booleano en el modelo `Ingrediente`. El schema de respuesta lo expone directamente. El frontend muestra un badge visual cuando `es_alergeno=True`.

**Por qué**: Requerimiento de negocio para alertar a usuarios con alergias. Simple de implementar y exponer en la API.

### D-05: TanStack Query con invalidación optimista en frontend

**Decisión**: Las mutaciones (crear/editar/eliminar) invalidan el query key del listado tras éxito. Sin optimistic updates en esta fase (se agrega en Sprint 3 si hay necesidad).

**Por qué**: El CRUD admin no requiere UX de alta frecuencia. La simplicidad de invalidar y refetch es suficiente.

## Risks / Trade-offs

- **[Riesgo] CTE en SQLite dev vs PostgreSQL prod**: La CTE recursiva funciona en ambas, pero la sintaxis y performance difieren. → Mitigación: tests de integración contra SQLite; validar contra PostgreSQL antes de prod.
- **[Riesgo] Árbol muy profundo**: Si hay muchos niveles, la respuesta puede ser grande. → Mitigación: limitar profundidad a 3 niveles por ahora (suficiente para food store). Agregar parámetro `?depth=` si se necesita en el futuro.
- **[Trade-off] Árbol anidado vs lista plana**: Lista plana es más fácil de paginar pero el frontend debe construir el árbol. Anidado es más fácil de renderizar pero más complejo de serializar. → Decisión: devolver ambos (lista plana + campo `subcategorias` anidado).
