## Context

El Sprint 0 dejó el scaffold del módulo `auth` (carpeta vacía con `__init__.py` y `model.py`), del `core/security.py` con stubs, y del `frontend/src/features/auth` con index vacío. `api/client.ts` existe sin interceptors y los stores Zustand son tipos vacíos. La base de datos tiene la tabla `usuarios` y `roles` pero `usuarios.password_hash` aún no se popula porque no hay flujo de auth.

Esta es la primera capability "real" del producto, así que las decisiones tomadas aquí van a fijar patrones para todo lo que viene (errores RFC 7807, RBAC vía dependencia FastAPI, formularios con TanStack Form, interceptors Axios). Por eso vale la pena un design.md aunque la feature en sí no sea enorme.

Stakeholders: estudiantes (devs), profesor (revisor), futuros pasajeros de los sprints siguientes que van a heredar estas convenciones.

## Goals / Non-Goals

**Goals:**
- Flujo end-to-end login/registro/refresh/logout funcionando con JWT HS256 + rotación.
- Patrón RBAC reusable como dependencia FastAPI.
- Layouts base que las épicas siguientes (catálogo, carrito, checkout, admin) puedan reusar sin tocar.
- Interceptor 401 con refresh transparente y manejo de race condition.
- Convención RFC 7807 establecida y aplicada a todos los errores del módulo auth.

**Non-Goals:**
- Recuperación de contraseña / "olvidé mi password" (no está en EPIC 01).
- OAuth / login social.
- Verificación de email.
- 2FA.
- Auditoría de sesiones / dispositivos.
- Internacionalización de mensajes de error (los mensajes van en español hardcoded por ahora).
- Implementación de los CRUDs admin, gestión de pedidos, etc. (Sprints posteriores).

## Decisions

### D-1: JWT HS256 con secret en `.env` (no RS256)

**Decisión:** Access tokens y refresh tokens firmados con HS256 usando `JWT_SECRET_KEY` del `.env`.

**Por qué:**
- HS256 es suficiente para un monolito (no hay servicios externos validando el token).
- RS256 requiere keypair y gestión de rotación de claves, complejidad innecesaria para un proyecto de TP.
- `python-jose[cryptography]` ya está en `requirements.txt`.

**Alternativa considerada:** RS256. Descartada por overkill.

### D-2: Refresh token persistido en BD (no JWT autocontenido)

**Decisión:** El refresh token es un JWT con `jti` único, y ese `jti` se persiste en `refresh_tokens(jti, usuario_id, expires_at, revoked_at)`. La validación combina firma + lookup en BD + chequeo de `revoked_at IS NULL`.

**Por qué:**
- Necesitamos revocación inmediata (logout, anti-replay) — un JWT puro no es revocable.
- Permite trackear si un token ya fue usado (campo `revoked_at`) y detectar replay.
- Rotación: al usar un refresh, marcamos el actual como revoked e insertamos el nuevo `jti`.

**Alternativa considerada:** refresh token opaco (UUID). Descartada porque mantener formato JWT permite mismo decode/verify path para ambos tipos de token.

### D-3: Anti-replay = revocar TODOS los tokens del usuario

**Decisión:** Si llega un refresh token con `revoked_at IS NOT NULL`, marcamos `revoked_at = now` en TODOS los refresh tokens de ese `usuario_id`.

**Por qué:**
- Comportamiento estándar (OAuth 2.0 Refresh Token Rotation, RFC 6819 §5.2.2.3).
- Si el token revocado se está usando, alguien lo robó del legítimo dueño O alguien tiene el actual; en cualquiera de los dos casos el escenario es comprometedor y forzar re-login es la respuesta más segura.

**Alternativa considerada:** revocar solo el reusado. Descartada: deja al atacante con tokens vigentes.

### D-4: Login no distingue email-inexistente de password-incorrecto

**Decisión:** Ambos casos responden el MISMO `401 INVALID_CREDENTIALS` con el mismo `detail`.

**Por qué:**
- User enumeration prevention (OWASP ASVS V3.2.3).
- Es regla explícita del `CLAUDE.md` ("la respuesta de login NO diferencia...").

**Trade-off:** UX levemente peor (no podemos decir "este email no existe, registrate"). Mitigado: `/register` sí dice "email ya registrado" para no romper el flujo de registro.

### D-5: Rate limiting con `slowapi` por IP

**Decisión:** `@limiter.limit("5/15minutes")` en el endpoint de login, key por IP (`get_remote_address`).

**Por qué:**
- `slowapi` ya está listado en `requirements.txt`.
- Por IP es suficiente para el alcance del TP. Por email + IP combinado sería más robusto pero suma complejidad.

**Alternativa considerada:** rate limit por email. Descartada porque permite a un atacante "bloquear" la cuenta de otro usuario haciendo 5 intentos fallidos con su email.

### D-6: RBAC via dependencia FastAPI factory

**Decisión:** Exponer `require_role(roles: list[str])` que retorna una dependencia FastAPI usable como:

```python
@router.get("/admin/dashboard", dependencies=[Depends(require_role(["ADMIN"]))])
def dashboard(): ...
```

**Por qué:**
- Composable, declarativo, idiomático en FastAPI.
- No requiere middleware global ni configuración compleja.

### D-7: `authStore` persiste solo `accessToken`; usuario se reconstruye via `/me`

**Decisión:** `zustand/persist` configurado con `partialize` que solo serializa `accessToken`. Al bootstrap (App mount), si hay `accessToken`, se dispara `GET /auth/me` y se popula `usuario` en el store.

**Por qué:**
- Regla explícita del `CLAUDE.md`.
- Evita stale data: si el usuario cambió de rol mientras el tab estaba cerrado, recupera el estado fresco al volver.

### D-8: Interceptor con cola de requests para evitar refresh loop

**Decisión:** El interceptor 401 mantiene una variable `isRefreshing: boolean` y una `failedQueue: Array<{ resolve, reject }>`. Cuando llega un 401 mientras `isRefreshing` ya es true, la request se mete en la cola. Al resolverse el refresh, todas las requests en cola se reintentan con el nuevo token.

**Por qué:**
- Sin esto, una carga simultánea de N requests (todas con token expirado) dispararía N llamados a `/auth/refresh`, y por la regla anti-replay (D-3) terminarían revocándose entre sí.

### D-9: TanStack Form para `LoginForm` y `RegisterForm`

**Decisión:** Usar `@tanstack/react-form` con `validators.onChange` y `validators.onSubmit`.

**Por qué:**
- Ya está en el `package.json` (es la regla del `CLAUDE.md`).
- API headless, integra bien con Tailwind y con los componentes `Input`/`Button` ya existentes.

### D-10: Layouts vivien en `components/layouts/` no en `features/`

**Decisión:** `AppLayout`, `AdminLayout`, `Navbar`, `Sidebar` van en `frontend/src/components/layouts/`. No en una feature, porque son transversales y NO pertenecen a auth (aunque consuman `authStore`).

**Por qué:**
- Si los pusiéramos en `features/auth` violaríamos Feature-Sliced Design (otras features importarían de auth solo para acceder al layout).
- Si los pusiéramos en `features/layout` crearíamos una "feature" que no representa un dominio de negocio.

## Risks / Trade-offs

- **[Riesgo] CORS mal configurado bloquea cookies/headers en refresh** → Mitigación: documentar en `.env.example` los origins permitidos; configurar `CORSMiddleware` con `allow_credentials=True` y `allow_headers=["Authorization"]`.
- **[Riesgo] `JWT_SECRET_KEY` débil en producción** → Mitigación: el `.env.example` indica generar con `openssl rand -hex 32`; el seed advierte si detecta la clave de ejemplo.
- **[Riesgo] Replay legítimo entre tabs simultáneos del mismo usuario** → Mitigación: la cola del interceptor (D-8) sincroniza requests dentro de un mismo tab; entre tabs es aceptable que uno fuerce re-login porque el escenario es muy raro y la regla de seguridad es estricta.
- **[Trade-off] No hay tests E2E todavía** → Sprint 1 cubre con tests de integración (pytest + httpx) y tests de componentes con React Testing Library. E2E queda para Sprint 5+.
- **[Trade-off] No usamos cookies httpOnly para tokens** → Más simple en localStorage; se asume contexto académico. Migrar a cookies httpOnly + CSRF token sería mejora futura.

## Migration Plan

1. Crear migración Alembic: tabla `refresh_tokens` y `UNIQUE(email)` en `usuarios` (si no existe).
2. Aplicar `alembic upgrade head` (la BD del Sprint 0 sigue compatible).
3. Re-correr `python -m app.db.seed` — ahora el admin se crea con `password_hash` bcrypt real (idempotente: skip si ya existe).
4. Rollout: como es la primera capability funcional, no hay tráfico real que migrar. Si fuera necesario reiniciar el dev environment: `alembic downgrade -1` revierte la migración.

## Open Questions

- ¿Debemos limitar el número de refresh tokens activos por usuario (p.ej. máximo 5)? Por ahora NO se implementa, queda como mejora para Sprint 2 si se ve necesario.
- ¿`/auth/logout` debe revocar SOLO el refresh enviado o TODOS los del usuario? Decisión actual: solo el enviado (logout "de este dispositivo"). Si se quiere "logout global" se agregará `/auth/logout-all` después.
- ¿La página `/register` debe estar accesible si el usuario YA está autenticado? Decisión actual: redirige a `/` si hay sesión.
