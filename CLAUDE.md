# CLAUDE.md — Food Store

## Visión General

Food Store es un e-commerce full-stack de alimentos con React + TypeScript (frontend) y FastAPI + PostgreSQL (backend). Usa metodología **Spec-Driven Development (SDD)** y organización **Feature-First** en ambas capas.

**Documentación de referencia obligatoria antes de implementar cualquier feature:**
- `docs/ARCHITECTURE.md` — Capas, patrones y reglas de dependencia
- `docs/DATA_MODEL.md` — ERD completo, constraints y snapshots
- `docs/API_SPEC.md` — Endpoints, schemas Pydantic y convenciones REST
- `docs/BUSINESS_RULES.md` — Reglas de negocio y FSM de pedidos
- `docs/USER_STORIES.md` — Historias de usuario por épica y criterios de aceptación
- `docs/DESIGN_SYSTEM.md` — Sistema de diseño Apple-inspired

---

## Stack Tecnológico

### Backend
| Tecnología | Versión | Rol |
|---|---|---|
| FastAPI | 0.111+ | Framework REST + OpenAPI |
| SQLModel | 0.0.19+ | ORM + schemas Pydantic |
| PostgreSQL | 15+ | Base de datos |
| Alembic | 1.13+ | Migraciones |
| Passlib (bcrypt) | — | Hashing contraseñas (cost ≥ 12) |
| python-jose / PyJWT | — | Tokens JWT HS256 |
| slowapi | 0.1.9+ | Rate limiting |
| mercadopago | 2.3.0+ | SDK MercadoPago Python |

### Frontend
| Tecnología | Versión | Rol |
|---|---|---|
| React + TypeScript | 18.x + 5.x | UI |
| Vite | 5.x | Build tool |
| Tailwind CSS | 3.x | Estilos |
| TanStack Query | 5.x | Estado del servidor |
| TanStack Form | 0.x | Formularios |
| Zustand | 4.x | Estado del cliente |
| Axios | 1.x | HTTP + interceptors JWT |
| recharts | 2.x | Gráficos del dashboard |
| @mercadopago/sdk-react | — | Tokenización PCI-compliant |

---

## Estructura del Proyecto

```
food-store/
├── backend/
│   ├── app/
│   │   ├── core/               # Config, seguridad, UoW, base repository
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── uow.py
│   │   │   └── repository.py
│   │   ├── modules/            # Feature-first: cada módulo es autocontenido
│   │   │   ├── auth/
│   │   │   │   ├── router.py
│   │   │   │   ├── service.py
│   │   │   │   ├── repository.py
│   │   │   │   ├── schemas.py
│   │   │   │   └── model.py
│   │   │   ├── usuarios/
│   │   │   ├── categorias/
│   │   │   ├── ingredientes/
│   │   │   ├── productos/
│   │   │   ├── direcciones/
│   │   │   ├── pedidos/
│   │   │   ├── pagos/
│   │   │   └── admin/
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   └── seed.py
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── pages/              # Solo define rutas, delega a features
    │   ├── features/           # Feature-Sliced Design
    │   │   ├── auth/
    │   │   │   ├── components/ # LoginForm, RegisterForm, ProtectedRoute
    │   │   │   ├── hooks/
    │   │   │   └── index.ts
    │   │   ├── catalogo/
    │   │   │   ├── components/ # CatalogoGrid, ProductoCard, FiltrosBarra
    │   │   │   ├── hooks/
    │   │   │   └── index.ts
    │   │   ├── carrito/
    │   │   │   ├── components/ # CartDrawer, CartItem, CartSummary
    │   │   │   ├── hooks/
    │   │   │   └── index.ts
    │   │   ├── pedidos/
    │   │   │   ├── components/ # PedidosList, PedidoDetail, HistorialTimeline
    │   │   │   ├── hooks/
    │   │   │   └── index.ts
    │   │   ├── checkout/
    │   │   │   ├── components/ # CheckoutForm, AddressSelector, PaymentStatus
    │   │   │   ├── hooks/
    │   │   │   └── index.ts
    │   │   └── admin/
    │   │       ├── components/ # Dashboard, CRUDs, GestionPedidos, StockTable
    │   │       ├── hooks/
    │   │       └── index.ts
    │   ├── components/         # Componentes compartidos (UI atómico)
    │   ├── store/              # Zustand stores
    │   │   ├── authStore.ts
    │   │   ├── cartStore.ts
    │   │   ├── paymentStore.ts
    │   │   └── uiStore.ts
    │   ├── api/                # Axios + interceptors
    │   │   ├── client.ts
    │   │   └── endpoints/
    │   ├── hooks/              # Custom hooks globales
    │   ├── types/              # Tipos TypeScript globales
    │   └── utils/
    ├── package.json
    └── .env.example
```

---

## Reglas de Arquitectura — OBLIGATORIAS

### Backend: Flujo de Dependencias (unidireccional, nunca romper)

```
Router → Service → UoW → Repository → Model
```

- **Router**: HTTP puro. Parsea request, valida schema Pydantic, delega al Service. **Sin lógica de negocio.**
- **Service**: Lógica de negocio stateless. Orquesta via UoW. Lanza `HTTPException`. **Nunca hace `session.commit()`.**
- **UoW**: Gestiona la transacción. Abre sesión, provee repositorios, hace commit/rollback automático.
- **Repository**: Queries a BD. Sin lógica de negocio. Hereda `BaseRepository[T]`. Recibe sesión del UoW.
- **Model**: SQLModel tables. Sin imports de capas superiores. **Nunca importa de Router, Service ni Repository.**

> ⛔ Un Model nunca importa de un Service. Un Repository nunca importa de un Router.

### Frontend: Feature-Sliced Design

```
Pages → Features → Hooks/Stores → API → Types
```

- **Sin cross-imports entre features**: `feature/auth` no puede importar de `feature/pedidos`.
- **Pages** solo definen la ruta y delegan a features.
- **`strict: true` en tsconfig**. **Prohibido usar `any`.**
- **Zustand** = estado del cliente (carrito, sesión, UI). **TanStack Query** = estado del servidor (productos, pedidos). No mezclar.

### Unit of Work — Patrón de uso obligatorio

```python
# ✅ Correcto
with UnitOfWork() as uow:
    result = service.crear_pedido(uow, body, usuario_id)
    return result

# ❌ Incorrecto — el service nunca maneja la sesión
session.commit()  # NUNCA en un Service
```

---

## Convenciones de Código

### Backend (Python)
- `snake_case` para funciones, variables y archivos.
- `PascalCase` para clases.
- Funciones de menos de 50 líneas. SRP estricto.
- Docstrings en todos los servicios y repositorios.
- Schemas separados para Create / Update / Read. **Nunca exponer el modelo SQLModel directamente como response.**
- Errores según RFC 7807: `{ "detail": "mensaje", "code": "ERROR_CODE", "field": "campo_opcional" }`
- Paginación estándar: `GET /recursos?page=1&size=20` → `{ "items": [...], "total": N, "page": 1, "size": 20, "pages": P }`
- Prefijo de rutas: `/api/v1/`

### Frontend (TypeScript)
- `camelCase` para variables y funciones.
- `PascalCase` para componentes y tipos.
- `kebab-case` para archivos de componentes.
- Prohibido `any`. Usar tipos explícitos o `unknown`.
- Custom hooks prefijados con `use`.
- Suscripción a Zustand por slice: `const items = useCartStore(s => s.items)` — nunca `const store = useCartStore()`.

---

## Patrones Implementados

| Patrón | Capa | Descripción |
|---|---|---|
| Repository Pattern | Backend | `BaseRepository[T]` genérico con `get_by_id`, `list_all`, `create`, `update`, `soft_delete` |
| Unit of Work | Backend | Context manager que garantiza atomicidad. El Service nunca hace commit. |
| Service Layer | Backend | Lógica de negocio stateless. Consume UoW. Independiente del framework. |
| Snapshot Pattern | Backend/BD | `precio_snapshot` y `nombre_snapshot` en `DetallePedido`. `direccion_snapshot` en `Pedido`. Inmutables. |
| Soft Delete | Backend/BD | `deleted_at TIMESTAMPTZ`. Nunca DELETE físico en entidades de negocio. |
| Audit Trail Append-Only | Backend/BD | `HistorialEstadoPedido`: solo INSERT, nunca UPDATE ni DELETE. |
| FSM (State Machine) | Backend | Transiciones de pedido validadas en Service contra mapa de transiciones permitidas. |
| Idempotent Payments | Backend | `idempotency_key UUID` enviado a MercadoPago. Evita cobros duplicados. |
| Feature-Sliced Design | Frontend | Features autocontenidas. Sin cross-imports entre features. |
| Custom Hooks | Frontend | Encapsulan lógica TanStack Query por dominio. |
| Optimistic Updates | Frontend | UI se actualiza antes de confirmar respuesta del servidor. Rollback en error. |

---

## Seguridad — Reglas Críticas

- ⛔ **Nunca almacenar contraseñas en texto plano.** Siempre bcrypt con cost ≥ 12.
- ⛔ **Nunca commitear el archivo `.env`** al repositorio. Solo `.env.example`.
- ⛔ **Datos de tarjetas nunca pasan por el servidor de Food Store** (PCI DSS SAQ-A). Solo tokenización via MercadoPago.js.
- ⛔ **La respuesta de login NO diferencia** "email no existe" de "contraseña incorrecta".
- ⛔ **El rol CLIENT no viene del request de registro**. Se asigna automáticamente en el backend.
- ✅ Rate limiting en login: 5 intentos por IP en 15 minutos → HTTP 429.
- ✅ Access token: 30 min. Refresh token: 7 días, rotación en cada uso, revocación en logout.
- ✅ Replay attack en refresh token: revocar TODOS los tokens del usuario.

---

## Máquina de Estados — Pedido

```
PENDIENTE → CONFIRMADO (automático, solo por pago aprobado vía webhook)
CONFIRMADO → EN_PREP    (Gestor de Pedidos / Admin)
EN_PREP    → EN_CAMINO  (Gestor de Pedidos / Admin)
EN_CAMINO  → ENTREGADO  (Gestor de Pedidos / Admin)

Cancelación:
  PENDIENTE   → CANCELADO  (Cliente / Gestor / Admin)
  CONFIRMADO  → CANCELADO  (Gestor / Admin)
  EN_PREP     → CANCELADO  (solo Admin)

ENTREGADO y CANCELADO son estados terminales. Sin transiciones salientes.
```

**Reglas críticas de la FSM:**
- `RN-FS02`: `PENDIENTE → CONFIRMADO` es **exclusivamente automática** (webhook IPN). Ningún humano puede ejecutarla manualmente.
- `RN-FS03`: Al confirmar, decrementar stock atómicamente.
- `RN-FS05`: Al cancelar desde CONFIRMADO, restaurar stock atómicamente.
- `RN-FS07`: Todo cambio de estado genera un INSERT en `HistorialEstadoPedido` (append-only).
- `RN-FS09`: Motivo obligatorio al cancelar.

---

## Zustand Stores

| Store | Archivo | Persiste | Qué gestiona |
|---|---|---|---|
| `authStore` | `store/authStore.ts` | Solo `accessToken` | Token, usuario, `isAuthenticated`, `hasRole()` |
| `cartStore` | `store/cartStore.ts` | `items` completos | Carrito, cantidades, personalizaciones |
| `paymentStore` | `store/paymentStore.ts` | No | Estado del pago MP: `idle/processing/approved/rejected/error` |
| `uiStore` | `store/uiStore.ts` | No | `cartOpen`, `sidebarOpen`, `confirmModal` |

> Al recargar, `authStore` solo recupera el `accessToken`. El objeto `usuario` se reconstruye con `GET /api/v1/auth/me`.

---

## Seed Data Obligatorio

Ejecutar luego de `alembic upgrade head`:

```bash
python -m app.db.seed
```

| Entidad | Datos |
|---|---|
| Rol | `ADMIN`, `STOCK`, `PEDIDOS`, `CLIENT` |
| EstadoPedido | `PENDIENTE`, `CONFIRMADO`, `EN_PREP`, `EN_CAMINO`, `ENTREGADO`, `CANCELADO` |
| FormaPago | `MERCADOPAGO`, `EFECTIVO`, `TRANSFERENCIA` |
| Usuario admin | `admin@foodstore.com` / `Admin1234!` con rol ADMIN |

---

## Permisos de Ejecución

Claude Code tiene autorización completa para:
- Ejecutar tests sin pedir confirmación (`pytest`, `npm test`, `npm run dev`)
- Instalar dependencias (`pip install`, `npm install`)
- Ejecutar migraciones (`alembic upgrade head`, `alembic revision`)
- Ejecutar scripts de seed (`python -m app.db.seed`)
- Correr el servidor de desarrollo


## Checklist de Entrega

- [ ] CE-01: Repositorio Git con historial progresivo de commits
- [ ] CE-02: `README.md` con instrucciones completas de setup
- [ ] CE-03: `.env.example` con todas las variables documentadas
- [ ] CE-04: `alembic upgrade head` sin errores
- [ ] CE-05: `python -m app.db.seed` funcional
- [ ] CE-06: `npm install && npm run dev` sin errores
- [ ] CE-07: `uvicorn app.main:app` sin errores
- [ ] CE-08: Swagger en `/docs` con todos los endpoints
- [ ] CE-09: Pago sandbox MercadoPago funcional end-to-end
- [ ] CE-10: Ningún `service.session.commit()` directo (todo via UoW)
- [ ] CE-11: 4 Zustand stores tipados con persist correcto
- [ ] CE-12: Screenshots de ≥ 10 pantallas
- [ ] CE-13: Video de demo (5–10 min) en README
- [ ] CE-14: Repositorio público verificado
