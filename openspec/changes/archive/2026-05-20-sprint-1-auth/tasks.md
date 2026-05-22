## 1. Backend — Modelos y migración

- [x] 1.1 Completar `backend/app/modules/auth/model.py` con `RefreshToken(SQLModel, table=True)` (campos: `jti: UUID PK`, `usuario_id: FK`, `expires_at: datetime`, `revoked_at: datetime | None`, `created_at: datetime`)
- [x] 1.2 Verificar/asegurar `UNIQUE` constraint en `usuarios.email` en `backend/app/modules/usuarios/model.py`
- [x] 1.3 Generar migración Alembic: `alembic revision --autogenerate -m "add refresh_tokens table"`
- [x] 1.4 Revisar la migración generada (PK UUID, índice en `usuario_id`, índice en `expires_at`) y aplicar `alembic upgrade head`

## 2. Backend — Core de seguridad

- [x] 2.1 Implementar en `backend/app/core/security.py`: `hash_password(plain) -> str` con `passlib[bcrypt]` cost 12
- [x] 2.2 Implementar `verify_password(plain, hashed) -> bool`
- [x] 2.3 Implementar `create_access_token(sub, rol) -> str` (HS256, exp 30 min, claims `sub`, `rol`, `type: "access"`)
- [x] 2.4 Implementar `create_refresh_token(sub) -> tuple[str, str]` (devuelve token y `jti`; exp 7 días; claim `type: "refresh"`)
- [x] 2.5 Implementar `decode_token(token, expected_type) -> dict` con manejo de `JWTError`, `ExpiredSignatureError`
- [x] 2.6 Implementar dependencia `get_current_user(token: str = Depends(oauth2_scheme), uow: UnitOfWork = Depends(get_uow)) -> Usuario`
- [x] 2.7 Implementar dependencia factory `require_role(roles: list[str])` que use `get_current_user` y valide el rol

## 3. Backend — Repositorios

- [x] 3.1 Crear `backend/app/modules/usuarios/repository.py` con `UsuarioRepository(BaseRepository[Usuario])` y método `get_by_email(email) -> Usuario | None`
- [x] 3.2 Crear `backend/app/modules/auth/repository.py` con `RefreshTokenRepository` y métodos: `create(jti, usuario_id, expires_at)`, `get_by_jti(jti)`, `revoke(jti)`, `revoke_all_by_user(usuario_id)`

## 4. Backend — Schemas Pydantic

- [x] 4.1 Crear `backend/app/modules/auth/schemas.py` con `RegisterRequest` (email EmailStr, password min_length=8, nombre, apellido)
- [x] 4.2 Agregar `LoginRequest` (email, password)
- [x] 4.3 Agregar `TokenResponse` (access_token, refresh_token, token_type="bearer", expires_in=1800)
- [x] 4.4 Agregar `RefreshRequest` (refresh_token)
- [x] 4.5 Agregar `LogoutRequest` (refresh_token)
- [x] 4.6 Agregar `UserPublic` (id, email, nombre, apellido, rol, fecha_alta) — usado por `/me` y como response de `/register`
- [x] 4.7 Agregar `ErrorResponse` (detail, code, field?) para documentar errores en OpenAPI

## 5. Backend — Service

- [x] 5.1 Crear `backend/app/modules/auth/service.py` con función `register(uow, body) -> UserPublic` (verifica email duplicado, hashea password, fuerza rol CLIENT, retorna usuario)
- [x] 5.2 Implementar `login(uow, email, password) -> TokenResponse` (busca usuario, verifica password, emite par de tokens, persiste `jti` del refresh)
- [x] 5.3 Implementar `refresh(uow, refresh_token) -> TokenResponse` (decode, lookup `jti`, si `revoked_at` IS NULL rota; si está revoked revoca all del usuario y lanza 401)
- [x] 5.4 Implementar `logout(uow, refresh_token) -> None` (revoca el `jti`)
- [x] 5.5 Implementar `get_me(uow, usuario_id) -> UserPublic`
- [x] 5.6 Asegurar que NINGÚN service haga `session.commit()` directo (todo via UoW)

## 6. Backend — Router

- [x] 6.1 Crear `backend/app/modules/auth/router.py` con `APIRouter(prefix="/auth", tags=["auth"])`
- [x] 6.2 Endpoint `POST /register` → 201, body `RegisterRequest`, response `UserPublic`
- [x] 6.3 Endpoint `POST /login` → 200, body `LoginRequest`, response `TokenResponse`, con `@limiter.limit("5/15minutes")`
- [x] 6.4 Endpoint `POST /refresh` → 200, body `RefreshRequest`, response `TokenResponse`
- [x] 6.5 Endpoint `POST /logout` → 204, body `LogoutRequest`, protegido con `Depends(get_current_user)`
- [x] 6.6 Endpoint `GET /me` → 200, response `UserPublic`, protegido con `Depends(get_current_user)`

## 7. Backend — Wiring y error handling

- [x] 7.1 En `backend/app/main.py`: incluir `auth_router` con prefijo `/api/v1`
- [x] 7.2 Inicializar `slowapi.Limiter` y registrar `app.state.limiter = limiter`
- [x] 7.3 Registrar handler global de `RateLimitExceeded` que devuelva RFC 7807 con `code: "RATE_LIMIT_EXCEEDED"` y header `Retry-After`
- [x] 7.4 Registrar handler global de `HTTPException` que envuelva el detail en formato `{ detail, code, field? }` cuando el detail no venga ya estructurado
- [x] 7.5 Registrar handler de `RequestValidationError` que devuelva `400` con `code: "VALIDATION_ERROR"` y `field` mapeado al primer error de Pydantic
- [x] 7.6 Configurar `CORSMiddleware` con origins desde `.env`, `allow_credentials=True`, `allow_headers=["Authorization", "Content-Type"]`

## 8. Backend — Seed y .env

- [x] 8.1 Actualizar `backend/app/db/seed.py` para que el `admin@foodstore.com` se inserte con `password_hash = hash_password("Admin1234!")` (idempotente)
- [x] 8.2 Asegurar que `backend/.env.example` documente `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30`, `JWT_REFRESH_TOKEN_EXPIRE_DAYS=7`, `CORS_ALLOWED_ORIGINS`

## 9. Backend — Tests

- [x] 9.1 Crear `backend/tests/test_auth_register.py`: registro exitoso, email duplicado, password débil, intento de escalar rol
- [x] 9.2 Crear `backend/tests/test_auth_login.py`: login exitoso, credenciales inválidas (mismo error para email-inexistente y password-malo), rate limit
- [x] 9.3 Crear `backend/tests/test_auth_refresh.py`: refresh exitoso (token nuevo + viejo revocado), token expirado, replay (revoca todos)
- [x] 9.4 Crear `backend/tests/test_auth_logout.py`: logout revoca, logout sin auth devuelve 401
- [x] 9.5 Crear `backend/tests/test_auth_me.py`: /me con token válido, con token expirado, sin token
- [x] 9.6 Crear `backend/tests/test_require_role.py`: dependencia permite, deniega 403, rechaza sin token

## 10. Frontend — API client e interceptors

- [x] 10.1 Completar `frontend/src/api/client.ts` con interceptor de request que agregue `Authorization: Bearer ${accessToken}` leyendo de `authStore.getState()`
- [x] 10.2 Implementar interceptor de response que detecte `401` con `code: ACCESS_TOKEN_EXPIRED`, dispare `/auth/refresh`, actualice `authStore` y reintente la request original (usando flag `isRefreshing` y `failedQueue` para evitar requests duplicadas)
- [x] 10.3 En caso de fallo del refresh, limpiar `authStore`, mostrar toast "Sesión expirada" y redirigir a `/login`
- [x] 10.4 Implementar interceptor global de errores que para `400/403/500` dispare toast vía `uiStore` con el `detail` del body RFC 7807 (saltea 401)

## 11. Frontend — Endpoints tipados de auth

- [x] 11.1 Crear `frontend/src/api/endpoints/auth.ts` con funciones: `login(body)`, `register(body)`, `refresh(body)`, `logout(body)`, `getMe()`
- [x] 11.2 Definir tipos en `frontend/src/types/auth.ts`: `LoginRequest`, `RegisterRequest`, `TokenResponse`, `UserPublic`, `Rol = "ADMIN" | "STOCK" | "PEDIDOS" | "CLIENT"`

## 12. Frontend — authStore

- [x] 12.1 Implementar `frontend/src/store/authStore.ts` con `accessToken`, `refreshToken`, `usuario: UserPublic | null`, `isAuthenticated` (derivado), `hasRole(role)`, `setSession(tokens, usuario)`, `clearSession()`
- [x] 12.2 Configurar `zustand/persist` con `partialize` para serializar SOLO `accessToken` (y `refreshToken` si se decide persistirlo en localStorage)
- [x] 12.3 Exportar selectores typed: `useAuthStore.use.usuario`, `useAuthStore.use.isAuthenticated`, etc. — suscripción por slice

## 13. Frontend — Hooks de auth

- [x] 13.1 Crear `frontend/src/features/auth/hooks/useLogin.ts` con `useMutation` que llama endpoint y popula `authStore`
- [x] 13.2 Crear `useRegister.ts` con `useMutation` que registra y dispara login automático
- [x] 13.3 Crear `useLogout.ts` con `useMutation` que llama `/auth/logout` y limpia stores
- [x] 13.4 Crear `useCurrentUser.ts` con `useQuery` `["auth", "me"]` que se dispara solo si hay `accessToken` (`enabled: !!accessToken`)

## 14. Frontend — Componentes de auth

- [x] 14.1 Crear `frontend/src/features/auth/components/LoginForm.tsx` con TanStack Form, validación email + password ≥ 8, mensaje genérico ante 401, manejo de 429 con tiempo de espera
- [x] 14.2 Crear `RegisterForm.tsx` con validación email, password ≥ 8, confirm password coincidente, nombre, apellido; mapea `field` del 409 al input correspondiente
- [x] 14.3 Crear `ProtectedRoute.tsx` con props `roles?: Rol[]`; redirige a `/login?next=<path>` si no auth y a `/` si rol insuficiente
- [x] 14.4 Exportar todo desde `frontend/src/features/auth/index.ts`

## 15. Frontend — Páginas de auth

- [x] 15.1 Completar `frontend/src/pages/LoginPage.tsx` para usar `LoginForm` y manejar redirect post-login según rol (`ADMIN/STOCK/PEDIDOS` → `/admin`, `CLIENT` → `/` o `next`)
- [x] 15.2 Completar `RegisterPage.tsx` para usar `RegisterForm`; si ya hay sesión redirigir a `/`
- [x] 15.3 Hacer bootstrap en `App.tsx` o `main.tsx`: si hay `accessToken` al montar, disparar `useCurrentUser` para hidratar `authStore.usuario` antes de renderizar rutas

## 16. Frontend — Layout base

- [x] 16.1 Crear `frontend/src/components/layouts/AppLayout.tsx` con navbar sticky + blur (Tailwind `backdrop-blur`), `<Outlet />`, footer simple
- [x] 16.2 Crear `frontend/src/components/layouts/Navbar.tsx` que se suscriba por slice a `authStore.usuario`; muestra links públicos + botón login si no auth, menú con nombre + logout si auth, ítem extra "Mis pedidos" para CLIENT
- [x] 16.3 Crear `frontend/src/components/layouts/AdminLayout.tsx` con sidebar + `<Outlet />`; sidebar lee `authStore.usuario.rol` y filtra ítems
- [x] 16.4 Crear `frontend/src/components/layouts/Sidebar.tsx` con ítems estáticos por rol: ADMIN → Dashboard/Productos/Categorías/Ingredientes/Pedidos/Usuarios; STOCK → Productos/Categorías/Ingredientes; PEDIDOS → Pedidos

## 17. Frontend — Wiring de rutas

- [x] 17.1 En `frontend/src/App.tsx`, configurar `react-router-dom` con: rutas públicas (`/`, `/login`, `/register`) envueltas en `AppLayout`
- [x] 17.2 Rutas de cliente protegidas (`/pedidos`, `/checkout`) en `AppLayout` + `ProtectedRoute` (sin restricción de rol)
- [x] 17.3 Rutas admin (`/admin/*`) envueltas en `ProtectedRoute roles={["ADMIN","STOCK","PEDIDOS"]}` + `AdminLayout`
- [x] 17.4 Ruta `NotFoundPage` para 404
- [x] 17.5 Verificar que el navbar reactivo cambie sin recarga al hacer login/logout (suscripción por slice)

## 18. Frontend — Tests

- [x] 18.1 Test de `LoginForm` con React Testing Library: render, validación, submit exitoso (mock), 401 muestra mensaje genérico, 429 deshabilita botón
- [x] 18.2 Test de `RegisterForm`: validación, confirm password, 409 mapea field
- [x] 18.3 Test de `ProtectedRoute`: redirige sin sesión, permite con rol, redirige con rol insuficiente
- [x] 18.4 Test del interceptor 401: dispara refresh, reintenta request, maneja race condition (mock con `axios-mock-adapter` o MSW)
- [x] 18.5 Test de `authStore`: `setSession`, `clearSession`, `hasRole`, persist solo de `accessToken`

## 19. Validación final

- [ ] 19.1 `pytest backend/tests` pasa sin errores
- [ ] 19.2 `npm test` (frontend) pasa sin errores
- [ ] 19.3 `uvicorn app.main:app --reload` arranca y `/docs` muestra los 5 endpoints de auth
- [ ] 19.4 `npm run dev` arranca; flujo manual: registro → login (CLIENT) → /me → logout funciona end-to-end
- [ ] 19.5 Flujo manual con admin: login admin → redirect a /admin → sidebar muestra todos los ítems → logout
- [ ] 19.6 Replay de refresh manual: usar refresh dos veces seguidas → segundo intento devuelve 401 y revoca todos
- [ ] 19.7 Rate limit manual: 6 logins fallidos seguidos desde misma IP → 6° devuelve 429
- [ ] 19.8 Recargar página con sesión activa: la app se mantiene autenticada (bootstrap de `/me` funciona)
