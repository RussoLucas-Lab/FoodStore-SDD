## ADDED Requirements

### Requirement: CatalogoGrid — grid paginado de productos
El sistema SHALL renderizar un componente `CatalogoGrid` en la ruta pública `/` (o `/catalogo`) que muestre los productos disponibles en grid responsive con paginación.

#### Scenario: Carga inicial
- **WHEN** el usuario navega al catálogo
- **THEN** se muestran skeleton loaders durante la carga y luego la grilla de `ProductoCard` con paginación al pie

#### Scenario: Sin resultados
- **WHEN** los filtros activos no retornan productos
- **THEN** se muestra un mensaje "No se encontraron productos" sin errores de UI

#### Scenario: Error de red
- **WHEN** la llamada a `GET /api/v1/productos` falla
- **THEN** se muestra un mensaje de error con botón de reintento

### Requirement: ProductoCard — tarjeta de producto
El sistema SHALL renderizar un componente `ProductoCard` por cada producto que muestre nombre, descripción truncada, precio formateado en ARS y badges de alérgenos.

#### Scenario: Producto con alérgenos
- **WHEN** el producto tiene ingredientes con `es_alergeno=true`
- **THEN** la card muestra badges de alerta por cada alérgeno

#### Scenario: Producto no disponible
- **WHEN** el producto tiene `disponible=false`
- **THEN** la card muestra una indicación visual de "No disponible" y el botón de agregar al carrito está deshabilitado

### Requirement: FiltrosBarra — barra de filtros combinables
El sistema SHALL renderizar un componente `FiltrosBarra` que permita filtrar el catálogo por categoría (selector), búsqueda textual (input con debounce 300ms) y excluir alérgenos (multiselect o checkboxes).

#### Scenario: Filtro por categoría
- **WHEN** el usuario selecciona una categoría en el selector
- **THEN** el catálogo se actualiza mostrando solo productos de esa categoría

#### Scenario: Búsqueda textual con debounce
- **WHEN** el usuario escribe en el campo de búsqueda
- **THEN** la llamada al API se dispara 300ms después de la última tecla presionada

#### Scenario: Limpiar filtros
- **WHEN** el usuario hace click en "Limpiar filtros"
- **THEN** todos los filtros se resetean y el catálogo muestra todos los productos disponibles

### Requirement: Paginación del catálogo
El sistema SHALL renderizar controles de paginación que permitan navegar entre páginas de resultados.

#### Scenario: Navegación entre páginas
- **WHEN** el usuario hace click en una página específica o en "Siguiente"
- **THEN** el catálogo se actualiza mostrando los productos de esa página

#### Scenario: Sin paginación necesaria
- **WHEN** el total de resultados cabe en una página (total ≤ size)
- **THEN** los controles de paginación no se renderizan

### Requirement: Skeleton loaders durante carga
El sistema SHALL mostrar skeleton loaders en lugar de tarjetas vacías mientras se carga el catálogo.

#### Scenario: Estado de carga
- **WHEN** `isLoading` es true en el hook de TanStack Query
- **THEN** se renderizan N skeleton cards del mismo tamaño que `ProductoCard`
