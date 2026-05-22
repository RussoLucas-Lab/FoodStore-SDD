## Why

Food Store no tiene aún ningún mecanismo de identidad ni de control de acceso. Sin esto no se puede construir ninguna otra funcionalidad (carrito persistente, checkout, gestión de pedidos, administración) porque todas dependen de saber quién es el usuario y qué rol tiene. El Sprint 0 ya dejó el scaffold (módulos `auth`, `usuarios`, `roles`, stores Zustand vacíos, `api/client.ts` sin interceptors). El Sprint 1 debe convertir ese scaffold en un flujo de auth real y entregar el layout base que el resto de las épicas reutilizará.

Cubre las épicas **EPIC 01 — Autenticación y Autorización** y **EPIC 02 — Layout y Navegación Base**. Criterio de salida: login, registro, refresh y logout funcionales end-to-end, con rutas frontend y backend protegidas por rol.

## What Changes

**Backend — Módulo `auth`:**
- `POST /api/v1/auth/register` — registro de cliente con bcrypt (cost ≥ 12) y asignación automática del rol `CLIENT`.
- `POST /api/v1/auth/login` — emisión de access token (30 min) y refresh token (7 días), con rate limiting de 5 intentos por IP cada 15 minutos (HTTP 429 al superarlo).
- `POST /api/v1/auth/refresh` — rotación de refresh token. Si llega un token ya consumido se revocan TODOS los refresh tokens del usuario (protección anti-replay).
- `POST /api/v1/auth/logout` — revocación del refresh token vigente.
- `GET /api/v1/auth/me` — devuelve el usuario actual reconstruido desde el JWT.
- Tabla `refresh_tokens` (jti, usuario_id, expires_at, revoked_at) para rotación y revocación.
- Dependencia FastAPI `require_role([...])` que valida JWT y rol para usar en cualquier router.
- Respuestas de error en formato RFC 7807 (`detail`, `code`, `field?`). El login NO diferencia "email inexistente" de "password incorrecto".

**Frontend — Feature `auth`:**
- `LoginForm` y `RegisterForm` con TanStack Form y validación cliente (email, password mínimo 8, confirm).
- `ProtectedRoute` (HOC) que verifica `isAuthenticated` y `requiredRoles` antes de renderizar.
- Interceptor Axios: ante 401 dispara `/auth/refresh` una sola vez y reintenta la request original. Si el refresh falla, limpia `authStore` y redirige a `/login`.
- Redirect post-login según rol: `ADMIN/STOCK/PEDIDOS` → `/admin`, `CLIENT` → `/`.
- `authStore` (Zustand) persistiendo solo `accessToken`; reconstruye `usuario` con `GET /auth/me` en el bootstrap de la app.

**Frontend — Layout base:**
- `AppLayout` con navbar sticky con blur, footer y `<Outlet />`. Muestra estado de autenticación (login / avatar + logout).
- `AdminLayout` con sidebar cuyos ítems dependen del rol (ADMIN ve todo, STOCK solo stock, PEDIDOS solo pedidos).
- Manejo global de errores HTTP: toast automático en 400/403/500 (vía `Toast` ya existente + `uiStore`).
- Wiring de rutas: `/login`, `/register` públicas; `/admin/*` protegida por roles administrativos; `/pedidos`, `/checkout` protegidas por sesión.

## Capabilities

### New Capabilities
- `auth-backend`: Endpoints HTTP de autenticación, emisión/rotación de tokens JWT, hashing de contraseñas, rate limiting, dependencia de autorización RBAC y formato de error estandarizado.
- `auth-frontend`: Flujo de auth en el cliente: stores, formularios, interceptors, rutas protegidas, redirect por rol y reconstrucción de sesión al recargar.
- `layout-base`: Layouts compartidos (app y admin), navegación según estado de auth y rol, manejo global de errores con toasts.

### Modified Capabilities
- `infraestructura-backend`: el scaffold del módulo `auth` (ya creado en Sprint 0) se llena con `router`, `service`, `repository`, `schemas`, modelo `RefreshToken` y wiring en `main.py`. No hay cambios en los requirements actuales (que están vacíos).
- `infraestructura-frontend`: `api/client.ts` gana interceptors, `authStore.ts` deja de ser stub, `App.tsx` incorpora `ProtectedRoute` y los nuevos layouts. Sin cambios en requirements existentes.

(No se listan en `## Modified Capabilities` porque los specs base actuales no tienen requirements; las modificaciones son a archivos del scaffold, no a behavior ya especificado.)

## Impact

**Código afectado:**
- `backend/app/modules/auth/`: agrega `router.py`, `service.py`, `repository.py`, `schemas.py`, completa `model.py` con `RefreshToken`.
- `backend/app/modules/usuarios/`: agrega `repository.py` (consulta por email para login y registro).
- `backend/app/core/security.py`: completa funciones de hash, verificación, encode/decode JWT y dependencia `require_role`.
- `backend/app/main.py`: registra el router de `auth`, monta `slowapi` y middleware de error handler RFC 7807.
- `backend/alembic/versions/`: nueva migración para tabla `refresh_tokens` y constraint `usuarios.email UNIQUE`.
- `frontend/src/features/auth/`: implementa `LoginForm`, `RegisterForm`, `ProtectedRoute`, hooks `useLogin`, `useRegister`, `useLogout`, `useCurrentUser`.
- `frontend/src/api/client.ts`: interceptors de request (Bearer) y response (refresh + retry).
- `frontend/src/store/authStore.ts`: implementación real con `persist`.
- `frontend/src/components/`: nuevos `AppLayout`, `AdminLayout`, `Navbar`, `Sidebar`.
- `frontend/src/App.tsx`: wiring de rutas con layouts y `ProtectedRoute`.

**Dependencias:**
- Backend: `passlib[bcrypt]`, `python-jose[cryptography]` (o `PyJWT`), `slowapi` (ya listadas en `requirements.txt` del Sprint 0).
- Frontend: `@tanstack/react-form`, `@tanstack/react-query`, `zustand`, `axios`, `react-router-dom` (ya instalados).

**APIs públicas nuevas:** los 5 endpoints bajo `/api/v1/auth/*`.

**Datos:** nueva tabla `refresh_tokens`; `usuarios.password_hash` empieza a contener hashes reales; el seed (ya existente) sigue creando `admin@foodstore.com` pero ahora con hash bcrypt.

**Riesgos principales:** mala configuración de CORS impide el flujo de refresh; secret JWT débil; pérdida de rotación si el frontend dispara refresh en paralelo (mitigado con cola de requests en el interceptor).
