## 1. Backend — Scaffold y configuración base

- [x] 1.1 Crear estructura de carpetas: `backend/app/core/`, `backend/app/modules/`, `backend/app/db/`, `backend/alembic/`, `backend/tests/`
- [x] 1.2 Crear `backend/requirements.txt` con todas las dependencias del stack (`fastapi`, `sqlmodel`, `alembic`, `passlib[bcrypt]`, `python-jose[cryptography]`, `slowapi`, `psycopg2-binary`, `python-dotenv`, `pydantic-settings`, `mercadopago`, `uvicorn`)
- [x] 1.3 Crear `backend/.env.example` con todas las variables documentadas (`DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `CORS_ORIGINS`, `MP_ACCESS_TOKEN`, `MP_PUBLIC_KEY`, `MP_NOTIFICATION_URL`)
- [x] 1.4 Crear `backend/app/core/config.py` con clase `Settings` usando `pydantic-settings` que cargue todas las variables del `.env`

## 2. Backend — Capa core

- [x] 2.1 Crear `backend/app/db/database.py` con `engine = create_engine(settings.DATABASE_URL)` y `SessionLocal = sessionmaker(...)` usando SQLModel
- [x] 2.2 Crear `backend/app/core/repository.py` con `BaseRepository[T]`: métodos `get_by_id`, `list_all`, `count`, `create`, `update`, `soft_delete`, `hard_delete`
- [x] 2.3 Crear `backend/app/core/uow.py` con `UnitOfWork`: `__enter__` abre sesión e instancia todos los repositorios; `__exit__` hace commit o rollback automático y cierra sesión; método `flush()`
- [x] 2.4 Crear `backend/app/core/security.py` con: `hash_password`, `verify_password` (bcrypt cost ≥ 12), `create_access_token` (JWT HS256, exp 30min), `create_refresh_token` (UUID v4), dependencias `get_current_user` y `require_role([...])`

## 3. Backend — Modelos SQLModel (Dominio Identidad y Acceso)

- [x] 3.1 Crear `backend/app/modules/usuarios/model.py` con `Usuario` (`id`, `nombre`, `apellido`, `email` UQ, `password_hash`, `activo`, `deleted_at`, `created_at`)
- [x] 3.2 Crear `backend/app/modules/roles/model.py` con `Rol` (PK semántica `codigo`) y `UsuarioRol` (pivot N:M con `asignado_por_id`)
- [x] 3.3 Crear `backend/app/modules/auth/model.py` con `RefreshToken` (`token_hash` SHA-256, `expires_at`, `revoked_at`)

## 4. Backend — Modelos SQLModel (Dominio Catálogo)

- [x] 4.1 Crear `backend/app/modules/categorias/model.py` con `Categoria` (FK autoreferencial `parent_id`, soft delete)
- [x] 4.2 Crear `backend/app/modules/ingredientes/model.py` con `Ingrediente` (`es_alergeno`, soft delete)
- [x] 4.3 Crear `backend/app/modules/productos/model.py` con `Producto` (`precio_base DECIMAL(10,2) CHECK>=0`, `stock_cantidad INTEGER CHECK>=0`, `disponible`, soft delete), `ProductoCategoria` (pivot), `ProductoIngrediente` (pivot con `es_removible`)
- [x] 4.4 Crear `backend/app/modules/direcciones/model.py` con `DireccionEntrega` (`usuario_id` FK, `es_principal`, soft delete)
- [x] 4.5 Crear `backend/app/modules/pagos/model.py` con `FormaPago` (PK semántica `codigo`, `habilitado`)

## 5. Backend — Modelos SQLModel (Dominio Ventas)

- [x] 5.1 Crear `backend/app/modules/pedidos/model.py` con `EstadoPedido` (PK semántica, `es_terminal`), `Pedido` (`direccion_snapshot JSONB`, `total DECIMAL`, snapshots), `DetallePedido` (`precio_snapshot`, `nombre_snapshot`, `personalizacion INTEGER[]`), `HistorialEstadoPedido` (append-only, `estado_desde` nullable)
- [x] 5.2 Crear `backend/app/modules/pagos/model.py` (ampliar) con `Pago` (`mp_payment_id` UQ, `idempotency_key` UQ, `external_reference` UQ)

## 6. Backend — Alembic y Seed

- [x] 6.1 Inicializar Alembic: `alembic init alembic` dentro de `backend/`; configurar `alembic.ini` para leer `DATABASE_URL` desde `Settings`; configurar `env.py` para importar todos los modelos SQLModel
- [x] 6.2 Generar migración inicial: `alembic revision --autogenerate -m "initial schema"`; revisar el script y agregar manualmente constraints CHECK y el tipo `INTEGER[]` si autogenerate los omite
- [x] 6.3 Verificar que `alembic upgrade head` crea las 16 tablas sin errores
- [x] 6.4 Crear `backend/app/db/seed.py` con función `seed()` que inserta (idempotente): roles `ADMIN`/`STOCK`/`PEDIDOS`/`CLIENT`; estados de pedido con `orden` y `es_terminal`; formas de pago; usuario `admin@foodstore.com` / `Admin1234!` con rol ADMIN
- [x] 6.5 Verificar que `python -m app.db.seed` ejecuta sin errores y es idempotente (segunda ejecución no duplica)

## 7. Backend — main.py y manejo de errores

- [x] 7.1 Crear `backend/app/main.py` con instancia FastAPI, `CORSMiddleware` usando `settings.CORS_ORIGINS` y `Limiter` de slowapi
- [x] 7.2 Registrar `@app.exception_handler(HTTPException)` que formatea la respuesta como RFC 7807: `{ "detail": "...", "code": "...", "field": "..." }`
- [x] 7.3 Registrar `@app.exception_handler(RequestValidationError)` que incluye el campo `field` con el nombre del campo inválido
- [x] 7.4 Registrar routers placeholder vacíos para los 8 módulos con prefijo `/api/v1` (los routers se implementan en sprints siguientes)
- [x] 7.5 Verificar que `uvicorn app.main:app --reload` arranca sin errores y `/docs` está disponible

## 8. Frontend — Scaffold

- [x] 8.1 Crear proyecto con `npm create vite@latest frontend -- --template react-ts`; verificar que `tsconfig.json` tiene `"strict": true`
- [x] 8.2 Instalar dependencias: `tailwindcss`, `postcss`, `autoprefixer`, `react-router-dom`, `axios`, `zustand`, `@tanstack/react-query`, `@tanstack/react-form`, `recharts`, `@mercadopago/sdk-react`
- [x] 8.3 Inicializar Tailwind: `npx tailwindcss init -p`; configurar `content` para que incluya `./src/**/*.{ts,tsx}`
- [x] 8.4 Extender `tailwind.config.js` con los tokens del `DESIGN_SYSTEM.md`: colores (`blue: #0071E3`, `blue-dark: #0055C6`, `surface: #F5F5F7`, `border: #D2D2D7`, `text-primary`, `text-secondary`, `text-tertiary`, `success`, `error`), fontFamily SF Pro, borderRadius (`sm: 10px`, `md: 18px`, `lg: 28px`, `full: 9999px`), maxWidth (`product: 980px`, `grid: 1200px`)
- [x] 8.5 Crear `frontend/.env.example` con `VITE_API_URL` y `VITE_MP_PUBLIC_KEY`

## 9. Frontend — Estructura de carpetas

- [x] 9.1 Crear estructura: `src/features/auth/`, `src/features/catalogo/`, `src/features/carrito/`, `src/features/checkout/`, `src/features/pedidos/`, `src/features/admin/` — cada una con `components/`, `hooks/`, `index.ts`
- [x] 9.2 Crear carpetas: `src/pages/`, `src/components/`, `src/store/`, `src/api/endpoints/`, `src/hooks/`, `src/types/`, `src/utils/`

## 10. Frontend — Stores Zustand

- [x] 10.1 Crear `src/store/authStore.ts` con `persist` middleware solo para `accessToken`; exponer `setAuth(token, usuario)`, `logout()`, `isAuthenticated`, `hasRole(role)`
- [x] 10.2 Crear `src/store/cartStore.ts` con `persist` completo; exponer `items`, `addItem`, `removeItem`, `updateCantidad`, `clearCart`, `total`; implementar lógica de incremento si el producto ya existe (RN-CR03)
- [x] 10.3 Crear `src/store/paymentStore.ts` sin persist; estado `status: 'idle' | 'processing' | 'approved' | 'rejected' | 'error'`; exponer `setStatus`
- [x] 10.4 Crear `src/store/uiStore.ts` sin persist; exponer `cartOpen`, `sidebarOpen`, `confirmModal`, `toggleCart`, `toggleSidebar`, `openConfirm`, `closeConfirm`

## 11. Frontend — Cliente Axios

- [x] 11.1 Crear `src/api/client.ts` con instancia `axios.create({ baseURL: import.meta.env.VITE_API_URL })`
- [x] 11.2 Agregar `interceptors.request` que lee `authStore.getState().accessToken` y agrega `Authorization: Bearer <token>` si existe
- [x] 11.3 Agregar `interceptors.response` que captura errores 401: intenta `POST /api/v1/auth/refresh` con el refresh token, actualiza el store con el nuevo access token, reintenta el request original una vez; si el refresh falla, llama `authStore.logout()` y redirige a `/login`; excluir la URL `/auth/refresh` del retry para evitar loop

## 12. Frontend — Componentes UI base

- [x] 12.1 Crear `src/components/Button.tsx` con variantes `primary` (pill `#0071E3`, sin borde) y `secondary` (texto `#0071E3`, sin borde ni fondo); props: `variant`, `disabled`, `loading`, `onClick`, `type`
- [x] 12.2 Crear `src/components/Input.tsx` con borde `#D2D2D7`, focus `#0071E3`, border-radius `10px`; props: `label`, `error`, `placeholder`, tipo HTML
- [x] 12.3 Crear `src/components/Card.tsx` con fondo `#F5F5F7`, sin borde, border-radius `18px`, padding `40px`
- [x] 12.4 Crear `src/components/Modal.tsx` con overlay oscuro, contenido centrado, shadow `0 40px 80px rgba(0,0,0,0.2)`, soporte para `onClose`
- [x] 12.5 Crear `src/components/Toast.tsx` con variantes `success` (`#34C759`) y `error` (`#FF3B30`); auto-dismiss configurable
- [x] 12.6 Crear `src/components/Spinner.tsx` con animación de carga en color `#0071E3`
- [x] 12.7 Crear `src/components/Skeleton.tsx` con animación de pulso y dimensiones configurables vía props

## 13. Frontend — Routing base

- [x] 13.1 Configurar React Router en `src/main.tsx` con `<BrowserRouter>`
- [x] 13.2 Crear `src/pages/` con componentes placeholder para: `HomePage`, `LoginPage`, `RegisterPage`, `PedidosPage`, `CheckoutPage`, `AdminPage`, `NotFoundPage`
- [x] 13.3 Definir rutas en `src/App.tsx`: `/` → `HomePage`, `/login` → `LoginPage`, `/register` → `RegisterPage`, `/pedidos` → `PedidosPage`, `/checkout` → `CheckoutPage`, `/admin` → `AdminPage`, `*` → `NotFoundPage`
- [x] 13.4 Verificar que `npm run dev` levanta sin errores de TypeScript y que la navegación entre rutas funciona en el browser
