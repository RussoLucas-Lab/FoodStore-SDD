## Context

Sprint 8 completa el panel de administración de Food Store. Los sprints anteriores (0–7) ya implementaron auth, catálogo, carrito, checkout, pagos, FSM de pedidos y visualización. Lo que falta es la capa de operaciones admin: gestión de usuarios con RBAC, métricas del negocio y stock/configuración. El frontend ya tiene la estructura `features/admin/` parcialmente poblada con `admin-categorias-ingredientes-frontend`; el backend no tiene módulo `admin/` aún — los endpoints RBAC y de métricas son nuevos.

## Goals / Non-Goals

**Goals:**
- Nuevo módulo `app/modules/admin/` con router/service/repository/schemas
- Endpoints de gestión de usuarios (listar, editar, asignar roles, activar/desactivar)
- Endpoints de métricas agregadas (resumen KPIs, ventas por período, productos top, pedidos por estado)
- Frontend: `Dashboard` (recharts), `UsuariosCRUD`, `StockTable`, `ConfiguracionPanel`
- Visibilidad de productos soft-deleted para ADMIN vía `include_deleted=true`

**Non-Goals:**
- Autenticación multi-factor ni cambio en el flujo JWT
- Panel de configuración con persistencia en base de datos (solo UI placeholder key-value)
- Reportes exportables (PDF/CSV) — no está en SPRINTS.md
- Paginación cursor-based en métricas — paginación estándar es suficiente

## Decisions

### D1: Módulo `admin` independiente, no por-dominio

**Decisión**: crear `app/modules/admin/` con su propio router/service/repository en lugar de agregar endpoints admin en `usuarios/`, `pedidos/`, etc.

**Alternativa considerada**: agregar `/admin/usuarios` a `app/modules/usuarios/router.py`. Se descartó porque mezcla la lógica de gestión propia del usuario (perfil, contraseña) con la gestión administrativa (roles, activación), violando SRP.

**Rationale**: el módulo admin es transversal — necesita queries sobre múltiples tablas (usuarios, pedidos, productos). Un módulo propio mantiene el flujo Router → Service → UoW → Repository limpio.

### D2: Métricas con queries SQL directas vía SQLModel `select()`

**Decisión**: implementar las queries de métricas directamente en `AdminRepository` usando `select()` con `func.sum`, `func.count`, `group_by`. Sin caching ni materialización de vistas.

**Alternativa considerada**: tabla `Metrica` materializada con job de actualización. Se descartó por complejidad innecesaria para un sistema de bajo volumen académico.

**Rationale**: las queries de métricas se ejecutan solo bajo demanda desde el dashboard. El costo es aceptable.

### D3: `include_deleted=true` solo honrado con rol ADMIN

**Decisión**: agregar `include_deleted: bool = False` al query param de `GET /api/v1/productos`. Si el token no tiene rol ADMIN, el param se ignora (siempre `False`).

**Rationale**: evita exponer lógica de autorización en el router — el service recibe el param resuelto según el rol del usuario actual.

### D4: `ConfiguracionPanel` sin persistencia real

**Decisión**: `ConfiguracionPanel` es un componente de UI que muestra/edita valores hardcodeados en el estado local. No hay tabla `Configuracion` en BD ni endpoint nuevo.

**Rationale**: US-060 pide "ver y editar configuración del sistema" pero el DATA_MODEL.md no define tabla de configuración. Se implementa como placeholder visual que cumple el criterio de entrega (CE-12 screenshots).

### D5: recharts ya es dependencia declarada

**Decisión**: usar `recharts` directamente. No instalar ninguna otra librería de gráficos.

**Rationale**: `recharts` ya está en el stack declarado en CLAUDE.md y SPRINTS.md.

## Risks / Trade-offs

- [Riesgo: queries de métricas lentas si hay muchos pedidos] → Mitigación: agregar índices en `Pedido.created_at` y `DetallePedido.pedido_id`. Para volumen académico no es crítico.
- [Riesgo: UsuariosCRUD puede degradar roles incorrectamente (RN-RB03: no bajar rol ADMIN del último admin)] → Mitigación: validación en service antes de PATCH roles: contar cuántos ADMINs activos quedan.
- [Riesgo: `include_deleted` expone productos eliminados al catálogo público si no se protege] → Mitigación: decisión D3 — el service ignora el param si el usuario no es ADMIN.

## Migration Plan

1. Crear `app/modules/admin/` (model no cambia, solo queries nuevas)
2. Registrar router en `app/main.py` con prefijo `/api/v1/admin`
3. Modificar `app/modules/productos/service.py` para aceptar `include_deleted` según rol
4. Frontend: extender `features/admin/` con nuevos componentes
5. Sin migraciones Alembic: no hay tablas nuevas

## Open Questions

- ¿El período de `ventas` puede ser parametrizable (`?periodo=dia|semana|mes`)? → Sí, implementar con query param `periodo: Literal["dia", "semana", "mes"] = "mes"`.
- ¿Cuántos productos devuelve `productos-top`? → Top 10 por defecto, configurable con `?limit=N` (max 50).
