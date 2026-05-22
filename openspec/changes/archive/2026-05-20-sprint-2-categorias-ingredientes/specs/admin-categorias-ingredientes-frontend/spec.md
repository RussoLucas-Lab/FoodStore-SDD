## ADDED Requirements

### Requirement: CategoriaCRUD — árbol navegable
El sistema SHALL renderizar un componente `CategoriaCRUD` en el panel admin que muestre el árbol de categorías y permita crear, editar y eliminar.

#### Scenario: Árbol cargado
- **WHEN** admin navega a la sección de categorías
- **THEN** se muestra el árbol jerárquico con categorías raíz expandibles

#### Scenario: Crear categoría raíz
- **WHEN** admin hace click en "Nueva categoría" sin seleccionar padre
- **THEN** se abre modal/form con campo nombre; al guardar, la categoría aparece en el árbol

#### Scenario: Crear subcategoría
- **WHEN** admin selecciona una categoría y hace click en "Agregar subcategoría"
- **THEN** se abre form con `parent_id` prellenado; al guardar aparece anidada bajo el padre

#### Scenario: Editar categoría
- **WHEN** admin hace click en editar de una categoría
- **THEN** se abre form con datos actuales; al guardar, el árbol se actualiza

#### Scenario: Eliminar categoría sin productos
- **WHEN** admin elimina categoría sin productos activos ni subcategorías
- **THEN** se muestra confirmación; al confirmar, la categoría desaparece del árbol

#### Scenario: Eliminar categoría con productos (RN-CA03)
- **WHEN** admin intenta eliminar categoría con productos activos
- **THEN** se muestra toast de error con mensaje de la API

#### Scenario: Estado de carga
- **WHEN** se está cargando el árbol
- **THEN** se muestra skeleton loader

### Requirement: IngredienteCRUD — lista con badge de alérgenos
El sistema SHALL renderizar un componente `IngredienteCRUD` en el panel admin que muestre la lista paginada de ingredientes con badge de alérgeno y permita CRUD completo.

#### Scenario: Lista cargada
- **WHEN** admin navega a la sección de ingredientes
- **THEN** se muestra tabla/lista paginada; ingredientes con `es_alergeno=true` tienen badge "Alérgeno" visible

#### Scenario: Filtrar alérgenos
- **WHEN** admin activa filtro "Solo alérgenos"
- **THEN** la lista muestra únicamente ingredientes con `es_alergeno=true`

#### Scenario: Crear ingrediente
- **WHEN** admin completa el form y guarda
- **THEN** el ingrediente aparece en la lista; si `es_alergeno=true` muestra el badge

#### Scenario: Editar ingrediente
- **WHEN** admin edita un ingrediente
- **THEN** los cambios se reflejan en la lista inmediatamente tras guardar

#### Scenario: Eliminar ingrediente
- **WHEN** admin confirma eliminación
- **THEN** el ingrediente desaparece de la lista

#### Scenario: Invalidación de cache tras mutación
- **WHEN** se completa cualquier mutación (crear/editar/eliminar)
- **THEN** TanStack Query invalida el query key de la lista y refetch automáticamente
