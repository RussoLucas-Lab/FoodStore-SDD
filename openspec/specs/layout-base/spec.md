# layout-base Specification

## Purpose
TBD - created by archiving change sprint-1-auth. Update Purpose after archive.
## Requirements
### Requirement: AppLayout público

El frontend SHALL proveer un `AppLayout` que envuelve las rutas públicas y de cliente. Incluye una navbar sticky con efecto blur (Apple-inspired), un área de contenido (`<Outlet />`) y un footer simple. La navbar SHALL reflejar el estado de autenticación.

#### Scenario: Visitante anónimo

- **WHEN** un visitante sin sesión navega a `/`
- **THEN** el navbar muestra los links públicos ("Catálogo") y un botón "Iniciar sesión" que lleva a `/login`

#### Scenario: Cliente autenticado

- **WHEN** un usuario con rol `CLIENT` está autenticado
- **THEN** el navbar muestra "Mis pedidos", un ícono de carrito y un menú con su nombre + opción "Cerrar sesión"

#### Scenario: Comportamiento sticky con blur

- **WHEN** el usuario hace scroll en cualquier página envuelta en `AppLayout`
- **THEN** el navbar permanece fijo en el top con `backdrop-filter: blur` aplicado

### Requirement: AdminLayout con sidebar por rol

El frontend SHALL proveer un `AdminLayout` para las rutas bajo `/admin`. Incluye un sidebar cuyos ítems se filtran según el rol del usuario actual.

#### Scenario: ADMIN ve todos los ítems

- **WHEN** un usuario con rol `ADMIN` entra a `/admin`
- **THEN** el sidebar muestra los ítems: Dashboard, Productos, Categorías, Ingredientes, Pedidos, Usuarios

#### Scenario: STOCK ve solo stock

- **WHEN** un usuario con rol `STOCK` entra a `/admin`
- **THEN** el sidebar muestra solo: Productos, Categorías, Ingredientes (no muestra Pedidos ni Usuarios)

#### Scenario: PEDIDOS ve solo pedidos

- **WHEN** un usuario con rol `PEDIDOS` entra a `/admin`
- **THEN** el sidebar muestra solo: Pedidos

### Requirement: Manejo global de errores HTTP

El cliente Axios SHALL tener un interceptor que, ante respuestas `400`, `403` o `500`, dispare un toast usando el `uiStore` con el `detail` y `code` del body RFC 7807.

#### Scenario: Error 400 Validation

- **WHEN** la API responde `400 VALIDATION_ERROR`
- **THEN** se muestra un toast tipo "warning" con el `detail` del error

#### Scenario: Error 403 Forbidden

- **WHEN** la API responde `403 INSUFFICIENT_ROLE` u otro 403
- **THEN** se muestra un toast tipo "error" con el `detail` del error

#### Scenario: Error 500 Server

- **WHEN** la API responde `500`
- **THEN** se muestra un toast tipo "error" con el texto "Error inesperado, intente nuevamente"

#### Scenario: 401 NO dispara toast genérico

- **WHEN** la API responde `401`
- **THEN** el interceptor de errores NO emite toast (queda en manos del interceptor de auth, que maneja refresh y redirect)

### Requirement: Wiring de rutas con protección

`App.tsx` SHALL declarar las rutas envueltas en los layouts y `ProtectedRoute` correspondiente.

#### Scenario: Rutas públicas

- **WHEN** un visitante sin sesión navega a `/`, `/login` o `/register`
- **THEN** las páginas renderizan dentro de `AppLayout` sin redirecciones

#### Scenario: Rutas de cliente protegidas

- **WHEN** un visitante sin sesión intenta entrar a `/pedidos` o `/checkout`
- **THEN** es redirigido a `/login?next=<ruta-original>`

#### Scenario: Rutas administrativas

- **WHEN** un visitante con rol `CLIENT` intenta entrar a `/admin/*`
- **THEN** es redirigido a `/`; los usuarios con `ADMIN`, `STOCK` o `PEDIDOS` SI pueden entrar y reciben `AdminLayout`

### Requirement: Navbar reactiva al estado de auth

El navbar SHALL suscribirse a `authStore` mediante selectores por slice (`useAuthStore(s => s.usuario)`) y re-renderizar automáticamente cuando cambie el estado de auth.

#### Scenario: Cambio a autenticado

- **WHEN** el usuario completa el login en `/login`
- **THEN** el navbar pasa de mostrar "Iniciar sesión" a mostrar el nombre del usuario sin requerir recarga manual

#### Scenario: Cambio a no autenticado

- **WHEN** el usuario hace logout
- **THEN** el navbar vuelve a mostrar "Iniciar sesión" inmediatamente

