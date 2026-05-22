## Context

Food Store parte de un repositorio vacío. El Sprint 0 construye el esqueleto completo sobre el que todos los demás sprints se apoyan. El backend usa FastAPI + SQLModel + PostgreSQL siguiendo el patrón de capas `Router → Service → UoW → Repository → Model`. El frontend usa Vite + React 18 + TypeScript 5 + Tailwind 3 con Feature-Sliced Design.

No hay código legado ni datos existentes. La única restricción es cumplir el stack fijo definido en `CLAUDE.md` y respetar las convenciones del design system de `docs/DESIGN_SYSTEM.md`.

## Goals / Non-Goals

**Goals:**
- Crear la estructura de directorios completa de ambas capas
- Implementar los cuatro patrones core del backend: UoW, BaseRepository, Security (JWT + bcrypt), Config
- Generar los 16 modelos SQLModel con todos los constraints del `DATA_MODEL.md`
- Migración Alembic inicial funcional y seed data ejecutable
- Cuatro Zustand stores tipados con el persist correcto según `CLAUDE.md`
- Cliente Axios con interceptors JWT (attach + refresh automático en 401)
- Componentes UI atómicos alineados al design system (tokens Tailwind, pill buttons, cards sin borde)
- `alembic upgrade head` y `npm run dev` sin errores al final del sprint

**Non-Goals:**
- Implementar lógica de negocio de ningún módulo (eso es Sprint 1+)
- Conectar el frontend al backend (los stores y el cliente quedan listos pero sin queries reales)
- Configurar CI/CD, Docker o despliegue en producción
- Escribir tests (Sprint 13)

## Decisions

### D1 — SQLModel como ORM + Schema único

**Decisión:** Usar `SQLModel` que une el modelo de BD (SQLAlchemy) con el schema Pydantic en una sola clase.

**Alternativa considerada:** SQLAlchemy puro + Pydantic separados. Más flexible pero requiere duplicar modelos.

**Razón:** El stack está fijado en `CLAUDE.md`. SQLModel reduce boilerplate en un proyecto académico donde la velocidad importa. El tradeoff (menos control de migraciones complejas) es aceptable.

**Regla operativa:** Los modelos con `table=True` son la fuente de verdad para Alembic. Los schemas de request/response son clases SQLModel sin `table=True` o Pydantic puros.

---

### D2 — Unit of Work como context manager Python

**Decisión:** `UnitOfWork` implementa `__enter__` / `__exit__`. El `__exit__` hace `session.commit()` si no hubo excepción, `session.rollback()` si la hubo.

**Razón:** Garantiza atomicidad sin que los Services tengan que gestionar la sesión. Ningún `Service` puede llamar `session.commit()` directamente (CE-10 del checklist de entrega).

**Implementación:**
```python
class UnitOfWork:
    def __enter__(self):
        self.session = SessionLocal()
        # instancia repositorios con self.session
        return self

    def __exit__(self, exc_type, *_):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
```

---

### D3 — JWT en dos tokens: access (30min) + refresh (7 días, rotación)

**Decisión:** Access token corto (30min) en header `Authorization: Bearer`. Refresh token opaco (UUID v4) almacenado hasheado en BD con `SHA-256`.

**Razón:** RN-AU02, RN-AU03, RN-AU04 del `BUSINESS_RULES.md`. Rotación previene replay attacks; si se detecta reuso, se revocan todos los tokens del usuario (RN-AU05).

**En Sprint 0:** Solo implementar las funciones criptográficas en `core/security.py`. Los endpoints `/auth/*` son Sprint 1.

---

### D4 — Zustand stores con persist selectivo

**Decisión:**
- `authStore`: persist solo `accessToken` (string). El objeto `usuario` se reconstruye con `GET /auth/me` al recargar.
- `cartStore`: persist completo (`items`, `total`).
- `paymentStore`, `uiStore`: sin persist (estado efímero).

**Razón:** CE-11 del checklist. Persistir el objeto usuario completo crea inconsistencias si cambian los roles en el backend.

---

### D5 — Tailwind config con tokens del design system

**Decisión:** Extender `tailwind.config.js` con los colores, fuentes, border-radius y maxWidth exactos del `DESIGN_SYSTEM.md`. No usar clases Tailwind que no estén mapeadas a tokens del sistema.

**Razón:** Consistencia visual en todos los sprints. Los tokens se definen una vez aquí y todos los componentes los usan.

---

### D6 — Manejo de errores RFC 7807 como middleware global

**Decisión:** Usar `@app.exception_handler` de FastAPI para capturar `HTTPException` y formatearlas como `{ "detail": "...", "code": "...", "field": "..." }`.

**Alternativa:** Manejar errores en cada router. Descartado: código duplicado.

**Razón:** Convención obligatoria del `CLAUDE.md`. Un solo lugar para el formato de error.

## Risks / Trade-offs

- **[Riesgo] Alembic autogenerate puede omitir constraints complejos** (CHECK, arrays PostgreSQL) → Mitigación: revisar el script generado antes de commitear; agregar constraints manualmente si autogenerate los omite.
- **[Riesgo] `INTEGER[]` (array nativo PostgreSQL) no soportado por SQLite** → No hay riesgo real: el proyecto usa PostgreSQL exclusivamente. No usar SQLite en ningún entorno.
- **[Riesgo] Interceptor de refresh en Axios puede entrar en loop si el endpoint `/auth/refresh` también devuelve 401** → Mitigación: verificar que el interceptor solo retrie una vez y que excluya la URL `/auth/refresh` del retry.
- **[Trade-off] SQLModel mezcla tabla y schema en una clase** → Para respuestas de API siempre usar schemas separados (clases sin `table=True`). Nunca devolver el modelo de tabla directamente como response (convención del `CLAUDE.md`).

## Migration Plan

1. Clonar repositorio base
2. Crear entorno virtual Python y ejecutar `pip install -r requirements.txt`
3. Copiar `.env.example` a `.env` y configurar `DATABASE_URL`
4. Ejecutar `alembic upgrade head` — crea todas las tablas
5. Ejecutar `python -m app.db.seed` — inserta datos semilla
6. En frontend: `npm install && npm run dev`

**Rollback:** Al ser la migración inicial no hay estado previo. Recrear la BD o ejecutar `alembic downgrade base`.

## Open Questions

- ¿La BD de desarrollo corre en PostgreSQL local o en Docker? → No afecta el código; solo la `DATABASE_URL` del `.env`.
- ¿Se incluye `docker-compose.yml` para PostgreSQL en este sprint? → Considerar agregarlo como conveniencia aunque el despliegue completo es Sprint 8.
