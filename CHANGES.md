# CHANGES.md — Food Store · Tracker de Progreso

> **Cómo usar este archivo**
> - Marca `[x]` cuando un ítem esté implementado y funcionando.
> - Mové el sprint a **En Progreso** cuando lo iniciás, a **Completado** cuando pase todos sus criterios de salida.
> - Registrá las decisiones y deuda técnica a medida que aparecen.

---

## Estado General

| Sprint | Nombre | Estado |
|--------|--------|--------|
| Sprint 0 | Infraestructura y Setup | ⬜ Pendiente |
| Sprint 1 | Auth y Autorización + Layout Base | ⬜ Pendiente |
| Sprint 2 | Categorías + Ingredientes | ⬜ Pendiente |
| Sprint 3 | Productos, Catálogo y Perfil | ⬜ Pendiente |
| Sprint 4 | Direcciones + Carrito | ⬜ Pendiente |
| Sprint 5 | Checkout y Creación de Pedidos | ⬜ Pendiente |
| Sprint 6 | Pagos MercadoPago + FSM de Pedidos | ⬜ Pendiente |
| Sprint 7 | Visualización de Pedidos + UX | ⬜ Pendiente |
| Sprint 8 | Admin: Usuarios, Catálogo y Métricas | ⬜ Pendiente |

---

## En Progreso

_Ningún sprint en progreso actualmente._

---

## Sprints Detallados

---

### Sprint 0 — Infraestructura y Setup
**Épica:** EPIC 00 · **Estado:** ⬜ Pendiente

**Criterio de salida:** `alembic upgrade head` + `seed.py` sin errores. `npm run dev` levanta sin errores.

#### Backend
- [ ] Scaffolding del proyecto FastAPI con estructura de módulos
- [ ] Configuración de `core/config.py` con Pydantic Settings
- [ ] `core/uow.py` — Unit of Work con context manager
- [ ] `core/repository.py` — `BaseRepository[T]` genérico
- [ ] `core/security.py` — JWT, hashing bcrypt, dependencias `get_current_user`, `require_role`
- [ ] Configuración de base de datos (`app/db/database.py`)
- [ ] Modelos SQLModel: `Usuario`, `Rol`, `UsuarioRol`, `RefreshToken`, `DireccionEntrega`, `Categoria`, `Ingrediente`, `Producto`, `ProductoCategoria`, `ProductoIngrediente`, `FormaPago`, `EstadoPedido`, `Pedido`, `DetallePedido`, `HistorialEstadoPedido`, `Pago`
- [ ] Alembic: migración inicial con todos los modelos
- [ ] `app/db/seed.py` — Roles, EstadoPedidos, FormasPago, usuario admin
- [ ] Manejo global de errores RFC 7807
- [ ] `app/main.py` con CORS, rate limiter (slowapi) y registro de routers
- [ ] `.env.example` completo

#### Frontend
- [ ] Scaffolding Vite + React + TypeScript + Tailwind
- [ ] `tsconfig.json` con `strict: true`
- [ ] Configuración de Tailwind con tokens del design system (`DESIGN_SYSTEM.md`)
- [ ] `api/client.ts` — Axios con interceptors JWT (access + refresh automático)
- [ ] `store/authStore.ts` con persist (solo `accessToken`)
- [ ] `store/cartStore.ts` con persist completo
- [ ] `store/paymentStore.ts` sin persist
- [ ] `store/uiStore.ts` sin persist
- [ ] Estructura de carpetas `features/`, `pages/`, `components/`, `hooks/`, `types/`
- [ ] Componentes UI base: `Button`, `Input`, `Card`, `Modal`, `Toast`, `Spinner`, `Skeleton`
- [ ] React Router DOM con rutas base

---

### Sprint 1 — Auth y Autorización + Layout Base
**Épicas:** EPIC 01, EPIC 02 · **Estado:** ⬜ Pendiente

**Criterio de salida:** Login, registro, refresh y logout funcionales end-to-end. Rutas protegidas por rol.

#### Backend — Módulo `auth`
- [ ] `POST /auth/register` — Registro con bcrypt, asignación automática rol CLIENT
- [ ] `POST /auth/login` — JWT access + refresh token, rate limiting 5/15min
- [ ] `POST /auth/refresh` — Rotación de refresh token
- [ ] `POST /auth/logout` — Revocación de refresh token
- [ ] `GET /auth/me` — Usuario actual desde JWT
- [ ] Dependencia `require_role([...])` para autorización RBAC

#### Frontend — Feature `auth`
- [ ] `LoginForm` — TanStack Form + validación
- [ ] `RegisterForm` — TanStack Form + validación
- [ ] `ProtectedRoute` — HOC que verifica `isAuthenticated` y roles
- [ ] Interceptor 401 → refresh automático → retry request
- [ ] Redirect post-login según rol (`/admin`, `/`, `/pedidos`)
- [ ] Navbar con estado de autenticación

#### Frontend — Layout Base
- [ ] `AppLayout` con nav sticky blur, footer
- [ ] `AdminLayout` con sidebar por rol
- [ ] Protección de rutas frontend por rol
- [ ] Manejo global de errores (toast en 400/403/500)

---

### Sprint 2 — Categorías + Ingredientes
**Épicas:** EPIC 03, EPIC 04 · **Estado:** ⬜ Pendiente

**Criterio de salida:** CRUD completo de categorías e ingredientes. El árbol de categorías se renderiza correctamente.

#### Backend — Módulo `categorias`
- [ ] `GET /categorias` — Árbol con CTE recursiva
- [ ] `GET /categorias/{id}` — Detalle con subcategorías
- [ ] `POST /categorias` — Crear (ADMIN)
- [ ] `PUT /categorias/{id}` — Actualizar (ADMIN)
- [ ] `DELETE /categorias/{id}` — Soft delete, valida sin productos activos (RN-CA03)

#### Backend — Módulo `ingredientes`
- [ ] CRUD completo de ingredientes con flag `es_alergeno`
- [ ] Soft delete

#### Frontend — Feature `admin` (parcial)
- [ ] `CategoriaCRUD` — Árbol jerárquico navegable, crear/editar/eliminar
- [ ] `IngredienteCRUD` — Lista con badge de alérgenos, crear/editar/eliminar

---

### Sprint 3 — Productos, Catálogo y Perfil
**Épicas:** EPIC 05, EPIC 06 · **Estado:** ⬜ Pendiente

**Criterio de salida:** Catálogo público funcional con filtros. CRUD de productos en panel admin.

#### Backend — Módulo `productos`
- [ ] `GET /productos` — Paginado, filtros (categoría, búsqueda, disponible, excluir alérgenos)
- [ ] `GET /productos/{id}` — Detalle con ingredientes, categorías
- [ ] `POST /productos` — Crear con categorías e ingredientes (ADMIN)
- [ ] `PUT /productos/{id}` — Actualizar (ADMIN)
- [ ] `PATCH /productos/{id}/disponibilidad` — Toggle (ADMIN/STOCK)
- [ ] `PATCH /productos/{id}/stock` — Actualizar cantidad (ADMIN/STOCK)
- [ ] `DELETE /productos/{id}` — Soft delete (ADMIN)
- [ ] Endpoints de ingredientes por producto

#### Frontend — Feature `catalogo`
- [ ] `CatalogoGrid` — Grid responsive con filtros y búsqueda (debounce 300ms)
- [ ] `ProductoCard` — Imagen, nombre, precio, badge alérgenos
- [ ] `FiltrosBarra` — Por categoría, alérgenos, búsqueda
- [ ] Skeleton loaders durante carga
- [ ] Paginación

#### Frontend — Feature `auth` (perfil)
- [ ] `PerfilForm` — Ver/editar nombre, apellido
- [ ] `CambiarPasswordForm` — Validación y actualización

---

### Sprint 4 — Direcciones + Carrito
**Épicas:** EPIC 07, EPIC 08 · **Estado:** ⬜ Pendiente

**Criterio de salida:** Carrito persiste en localStorage. CRUD de direcciones funcional.

#### Backend — Módulo `direcciones`
- [ ] `GET /direcciones` — Propias del cliente
- [ ] `POST /direcciones` — Crear (primera = principal automáticamente, RN-DI01)
- [ ] `PUT /direcciones/{id}` — Actualizar
- [ ] `PATCH /direcciones/{id}/principal` — Cambiar principal (RN-DI02)
- [ ] `DELETE /direcciones/{id}` — Soft delete

#### Frontend — Feature `carrito`
- [ ] `cartStore` completo: `addItem`, `removeItem`, `updateCantidad`, `clearCart`
- [ ] Personalización de items (excluir ingredientes, RN-CR03, RN-CR04)
- [ ] `CartDrawer` — Sidebar deslizable con items y totales
- [ ] Badge de cantidad en nav

#### Frontend — Feature `checkout` (parcial)
- [ ] `AddressSelector` — CRUD de direcciones inline en checkout
- [ ] Selector de dirección de entrega

---

### Sprint 5 — Checkout y Creación de Pedidos
**Épicas:** EPIC 09, EPIC 10 · **Estado:** ⬜ Pendiente

**Criterio de salida:** Pedido se crea atómicamente con snapshots. Flujo de checkout completo.

#### Backend — Módulo `pedidos` (creación)
- [ ] `POST /pedidos` — Creación atómica (UoW):
  - [ ] Validar disponibilidad de productos (RN-PE04)
  - [ ] `SELECT FOR UPDATE` para stock
  - [ ] Crear `Pedido` con `direccion_snapshot`
  - [ ] Crear `DetallePedido` con `precio_snapshot` y `nombre_snapshot`
  - [ ] Crear primer `HistorialEstadoPedido` con `estado_desde=NULL`
  - [ ] Calcular total (RN-PE08)
  - [ ] Rollback total si falla cualquier paso (RN-PE01)

#### Frontend — Feature `checkout`
- [ ] `CheckoutForm` — Resumen de carrito, selector de dirección, selector de forma de pago
- [ ] Validación pre-checkout: disponibilidad y precios
- [ ] Confirmación visual de pedido creado

---

### Sprint 6 — Pagos MercadoPago + FSM de Pedidos
**Épicas:** EPIC 11, EPIC 12 · **Estado:** ⬜ Pendiente

**Criterio de salida:** Pago sandbox end-to-end. Webhook actualiza pedido a CONFIRMADO. FSM valida todas las transiciones.

#### Backend — Módulo `pagos`
- [ ] `POST /pagos/crear` — Crear pago con `idempotency_key` UUID (RN-MP01)
- [ ] `POST /pagos/webhook` — IPN: procesar `topic=payment`, avanzar pedido si `approved`
- [ ] `GET /pagos/{pedido_id}` — Consultar estado de pago

#### Backend — Módulo `pedidos` (FSM)
- [ ] `PATCH /pedidos/{id}/estado` — Validar transición contra mapa FSM
- [ ] Implementar `OrderStateMachine` en service:
  - [ ] `PENDIENTE → CONFIRMADO`: solo automático (RN-FS02)
  - [ ] Decremento atómico de stock al confirmar (RN-FS03, RN-FS04)
  - [ ] Restaurar stock al cancelar desde CONFIRMADO (RN-FS05)
  - [ ] Append-only en `HistorialEstadoPedido` (RN-FS07)
  - [ ] Motivo obligatorio al cancelar (RN-FS10)

#### Frontend — Feature `checkout` (pago)
- [ ] `CardPayment` — Componente MercadoPago SDK React
- [ ] `paymentStore` integrado con flujo de pago
- [ ] Polling de estado de pago cada 30s
- [ ] Pantalla de éxito/error de pago

---

### Sprint 7 — Visualización de Pedidos + UX
**Épicas:** EPIC 13, EPIC 14 · **Estado:** ⬜ Pendiente

**Criterio de salida:** Cliente puede ver su historial completo. Gestor de Pedidos puede avanzar estados.

#### Backend
- [ ] `GET /pedidos` — Paginado (propios para CLIENT, todos para ADMIN/PEDIDOS)
- [ ] `GET /pedidos/{id}` — Detalle completo con items, historial y pago
- [ ] `GET /pedidos/{id}/historial` — Timeline completo
- [ ] `DELETE /pedidos/{id}` — Cancelar pedido propio (solo PENDIENTE)

#### Frontend — Feature `pedidos`
- [ ] `PedidosList` — Lista paginada con estados
- [ ] `PedidoDetail` — Vista completa con items, snapshots, dirección
- [ ] `HistorialTimeline` — Timeline visual del estado del pedido
- [ ] `PaymentStatus` — Estado del pago con actualización en tiempo real

#### Frontend — Feature `admin` (gestión de pedidos)
- [ ] `GestionPedidos` — Lista todos los pedidos, avanzar estado FSM
- [ ] Panel de Gestor de Pedidos

---

### Sprint 8 — Admin: Usuarios, Catálogo y Métricas
**Épicas:** EPIC 15, EPIC 16, EPIC 17, EPIC 18 · **Estado:** ⬜ Pendiente

**Criterio de salida:** Dashboard con gráficos funcionales. Admin puede gestionar todos los módulos.

#### Backend — Módulo `admin`
- [ ] `GET/PUT /admin/usuarios` — Gestión de usuarios con roles
- [ ] `PATCH /admin/usuarios/{id}/roles` — Asignación RBAC (RN-RB03, RN-RB04)
- [ ] `PATCH /admin/usuarios/{id}/activar` — Activar/desactivar
- [ ] `GET /admin/metricas/resumen` — KPIs del dashboard
- [ ] `GET /admin/metricas/ventas` — Ventas por período
- [ ] `GET /admin/metricas/productos-top` — Ranking de productos
- [ ] `GET /admin/metricas/pedidos-por-estado` — Distribución

#### Frontend — Feature `admin` (completo)
- [ ] `Dashboard` — KPIs con recharts: `<LineChart>` ventas, `<BarChart>` productos top, `<PieChart>` estados
- [ ] `UsuariosCRUD` — Lista, editar, roles, activar/desactivar
- [ ] `StockTable` — Gestión de stock y disponibilidad por producto
- [ ] Acceso Admin a catálogo completo (productos con soft-deleted)
- [ ] `ConfiguracionPanel` — Key-value de configuración del sistema

---

## Completado

_Ningún sprint completado aún._

---

## Decisiones Arquitectónicas

_Ninguna registrada aún. Registrar aquí las decisiones de diseño no obvias a medida que se tomen._

<!-- Formato sugerido:
### [Fecha] Título de la decisión
**Contexto:** Por qué surgió esta decisión.
**Decisión:** Qué se decidió hacer.
**Consecuencias:** Impacto esperado y tradeoffs.
-->

---

## Deuda Técnica Detectada

_Ninguna registrada aún. Registrar aquí shortcuts o soluciones temporales que deban revisarse._

<!-- Formato sugerido:
### [Fecha] Título de la deuda
**Ubicación:** Archivo o módulo afectado.
**Descripción:** Qué se hizo y por qué es temporal.
**Impacto:** Qué problemas puede causar si no se resuelve.
**Prioridad:** Alta / Media / Baja
-->
