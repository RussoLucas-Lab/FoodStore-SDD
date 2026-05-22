## ADDED Requirements

### Requirement: Dashboard con métricas y gráficos
El sistema SHALL renderizar un componente `Dashboard` dentro de `features/admin/` que muestra KPIs y tres gráficos recharts: `LineChart` de ventas, `BarChart` de productos top y `PieChart` de distribución de pedidos por estado. Solo accesible con rol ADMIN.

#### Scenario: Carga inicial del dashboard
- **WHEN** ADMIN navega a la ruta `/admin`
- **THEN** se renderizan 4 tarjetas de KPI (total pedidos, ventas del mes, productos activos, usuarios activos) y los 3 gráficos con datos del servidor

#### Scenario: Estado de carga
- **WHEN** las métricas están cargando
- **THEN** se muestra un `Skeleton` en cada tarjeta y gráfico

#### Scenario: Sin datos de ventas
- **WHEN** la respuesta de `/admin/metricas/ventas` devuelve series vacías
- **THEN** el `LineChart` muestra estado vacío con mensaje "Sin ventas en el período"

#### Scenario: Selector de período en LineChart
- **WHEN** ADMIN cambia el selector de período (día / semana / mes)
- **THEN** el hook re-fetcha con el nuevo período y el gráfico se actualiza

### Requirement: UsuariosCRUD — Gestión de usuarios con roles
El sistema SHALL renderizar un componente `UsuariosCRUD` dentro de `features/admin/` que lista usuarios con búsqueda, permite editar datos básicos, asignar roles y activar/desactivar. Solo accesible con rol ADMIN.

#### Scenario: Listado y búsqueda
- **WHEN** ADMIN navega a la sección de usuarios
- **THEN** ve tabla paginada con columnas: nombre, email, roles, estado activo; con campo de búsqueda debounced (300ms)

#### Scenario: Edición de roles
- **WHEN** ADMIN hace clic en editar roles de un usuario
- **THEN** se abre un modal con checkboxes de roles disponibles; al guardar se llama `PATCH /admin/usuarios/{id}/roles`

#### Scenario: Activar/desactivar usuario
- **WHEN** ADMIN hace toggle en la columna "Activo" de un usuario
- **THEN** se llama `PATCH /admin/usuarios/{id}/activar` y la UI se actualiza optimistamente

#### Scenario: Error al deshabilitar último admin
- **WHEN** el backend responde HTTP 422 con code `LAST_ADMIN`
- **THEN** el toggle se revierte y se muestra toast de error con el mensaje del backend

#### Scenario: No puede editar propios roles (RN-RB04)
- **WHEN** ADMIN intenta editar sus propios roles
- **THEN** el botón de edición de roles aparece deshabilitado con tooltip "No puedes editar tus propios roles"

### Requirement: StockTable — Gestión de stock y disponibilidad
El sistema SHALL renderizar un componente `StockTable` dentro de `features/admin/` que lista productos con sus campos de stock y disponibilidad, permitiendo editar ambos inline. Accesible con roles ADMIN y STOCK.

#### Scenario: Listado de productos con stock
- **WHEN** ADMIN o STOCK navegan a la sección de stock
- **THEN** ve tabla con columnas: nombre, stock actual, disponible (toggle), acciones; con paginación y búsqueda

#### Scenario: Editar stock inline
- **WHEN** ADMIN/STOCK edita el número de stock y confirma
- **THEN** se llama `PATCH /api/v1/productos/{id}/stock` y el valor se actualiza en la tabla

#### Scenario: Toggle disponibilidad
- **WHEN** ADMIN/STOCK hace toggle en la columna "Disponible"
- **THEN** se llama `PATCH /api/v1/productos/{id}/disponibilidad` con optimistic update

#### Scenario: Vista admin incluye productos eliminados
- **WHEN** ADMIN (no STOCK) activa el filtro "Mostrar eliminados"
- **THEN** la tabla incluye productos con `deleted_at` no nulo, marcados visualmente con badge "Eliminado"

### Requirement: ConfiguracionPanel — Configuración del sistema
El sistema SHALL renderizar un componente `ConfiguracionPanel` dentro de `features/admin/` que muestra pares clave-valor de configuración del sistema con capacidad de edición local. Solo accesible con rol ADMIN.

#### Scenario: Visualización de configuración
- **WHEN** ADMIN navega a configuración
- **THEN** ve tabla de pares clave-valor con valores editables inline

#### Scenario: Edición de valor
- **WHEN** ADMIN edita un valor y confirma
- **THEN** el valor se actualiza en el estado local del componente con feedback visual de confirmación

### Requirement: Navegación del panel admin completo
El sistema SHALL actualizar el sidebar del `AdminLayout` para incluir accesos a todas las secciones: Dashboard, Usuarios, Productos, Categorías, Ingredientes, Pedidos (gestión), Stock, Configuración. Las secciones se filtran según el rol del usuario autenticado.

#### Scenario: Sidebar ADMIN
- **WHEN** usuario con rol ADMIN está autenticado
- **THEN** el sidebar muestra todas las secciones del panel

#### Scenario: Sidebar STOCK
- **WHEN** usuario con rol STOCK está autenticado
- **THEN** el sidebar muestra solo: Stock, Productos (sin eliminar)

#### Scenario: Sidebar PEDIDOS
- **WHEN** usuario con rol PEDIDOS está autenticado
- **THEN** el sidebar muestra solo: Gestión de Pedidos
