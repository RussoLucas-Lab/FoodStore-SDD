# ARCHITECTURE.md — Food Store

## 1. Arquitectura del Backend

### Capas y Flujo de Dependencias

El backend aplica arquitectura en capas con flujo **unidireccional**. Ninguna capa puede importar de la capa superior.

```
Router → Service → UoW → Repository → Model
```

| Capa | Archivo | Responsabilidad | Conoce a |
|---|---|---|---|
| Router | `router.py` | HTTP puro: parsear request, validar schema Pydantic, delegar al Service, serializar response. **Sin lógica de negocio.** | Service |
| Service | `service.py` | Lógica de negocio stateless. Orquesta via UoW. Lanza `HTTPException`. **Nunca hace `commit/rollback`.** | UoW |
| Unit of Work | `core/uow.py` | Gestiona la transacción. Abre sesión, provee repositorios, hace commit automático o rollback en error. | Repository, Session |
| Repository | `repository.py` | Acceso a BD sin lógica de negocio. Hereda `BaseRepository[T]`. Recibe sesión del UoW por inyección. | Model, Session |
| Model | `model.py` | SQLModel tables + relaciones. Sin imports de capas superiores. | Ninguna |

### Módulos Backend (Feature-First)

Cada módulo vive en `app/modules/<nombre>/` y contiene sus propios `router.py`, `service.py`, `repository.py`, `schemas.py` y `model.py`.

| Módulo | Ruta | Descripción |
|---|---|---|
| `auth` | `app/modules/auth/` | Login, registro, refresh, logout. JWT + rate limiting. |
| `refreshtokens` | `app/modules/refreshtokens/` | Modelo `RefreshToken` para invalidación segura. |
| `usuarios` | `app/modules/usuarios/` | CRUD usuarios + asignación RBAC. Soft delete. |
| `categorias` | `app/modules/categorias/` | Categorías jerárquicas con CTE recursiva. |
| `ingredientes` | `app/modules/ingredientes/` | CRUD ingredientes con flag `es_alergeno`. |
| `productos` | `app/modules/productos/` | Catálogo con stock, disponibilidad e ingredientes. |
| `direcciones` | `app/modules/direcciones/` | CRUD `DireccionEntrega` por usuario con dirección principal. |
| `pedidos` | `app/modules/pedidos/` | Dominio central: FSM, snapshots, audit trail. |
| `pagos` | `app/modules/pagos/` | Integración MercadoPago: crear pago, webhook IPN. |
| `admin` | `app/modules/admin/` | Dashboard de métricas, gestión de stock y usuarios. |

### Unit of Work — Implementación

```python
# core/uow.py
class UnitOfWork:
    def __enter__(self):
        self.session = SessionLocal()
        self.productos = ProductoRepository(self.session)
        self.pedidos = PedidoRepository(self.session)
        self.pagos = PagoRepository(self.session)
        # ... resto de repositorios
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()

    def flush(self):
        self.session.flush()
```

### BaseRepository[T] — Métodos

| Método | Descripción |
|---|---|
| `get_by_id(entity_id: int) → T \| None` | Por clave primaria. Retorna None si no existe. |
| `list_all(skip, limit) → list[T]` | Listado sin filtros. Repos específicos definen sus propios métodos. |
| `count() → int` | Total de registros. Para paginación. |
| `create(entity: T) → T` | Agrega a sesión + `flush()` + `refresh()`. Retorna entidad con ID. |
| `update(entity: T) → T` | `flush()` + `refresh()`. |
| `soft_delete(entity: T) → None` | Asigna `deleted_at = now()`. Solo entidades con soft-delete. |
| `hard_delete(entity: T) → None` | DELETE físico. Solo cuando el modelo no tiene soft-delete. |

---

## 2. Arquitectura del Frontend

### Feature-Sliced Design

Flujo de imports de arriba hacia abajo:

```
Pages → Features → Hooks/Stores → API → Types
```

**Regla absoluta**: No hay cross-imports entre features. `feature/auth` no puede importar de `feature/pedidos`.

### Features

| Feature | Componentes principales |
|---|---|
| `auth` | `LoginForm`, `RegisterForm`, `ProtectedRoute` (HOC) |
| `catalogo` | `CatalogoGrid`, `ProductoCard`, `FiltrosBarra`, `ProductoModal` |
| `carrito` | `CartDrawer`, `CartItem`, `CartSummary`, `PersonalizacionModal` |
| `checkout` | `CheckoutForm`, `AddressSelector`, `CardPayment` (MP), `PaymentStatus` |
| `pedidos` | `PedidosList`, `PedidoDetail`, `HistorialTimeline`, `PaymentStatusPolling` |
| `admin` | `Dashboard`, `CategoriaCRUD`, `ProductoCRUD`, `StockTable`, `GestionPedidos`, `UsuariosCRUD` |

### Separación de Estado

```
Zustand     → Estado del CLIENTE  (carrito, sesión, UI, proceso de pago)
TanStack Query → Estado del SERVIDOR (productos, pedidos, dashboard)
```

Mezclar ambos en el mismo store es un **error arquitectónico**.

### Interceptor Axios — Manejo de JWT

```typescript
// api/client.ts
axiosInstance.interceptors.request.use(config => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

axiosInstance.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // Intentar refresh automático
      // Si falla → logout y redirect a /login
    }
    return Promise.reject(error);
  }
);
```

### TanStack Query — Convenciones

```typescript
// Query keys descriptivos
const QUERY_KEYS = {
  productos: ['productos'] as const,
  productoDetail: (id: number) => ['productos', id] as const,
  pedidos: ['pedidos'] as const,
  pedidoDetail: (id: number) => ['pedidos', id] as const,
};

// Custom hooks encapsulan la lógica
export function useProductos(filters: ProductoFilters) {
  return useQuery({
    queryKey: [...QUERY_KEYS.productos, filters],
    queryFn: () => productosApi.getAll(filters),
  });
}

// Invalidar después de mutaciones
const { mutate: crearProducto } = useMutation({
  mutationFn: productosApi.create,
  onSuccess: () => queryClient.invalidateQueries({ queryKey: QUERY_KEYS.productos }),
});
```

---

## 3. Integración MercadoPago

### Flujo Completo

```
1. Frontend renderiza <CardPayment> con SDK de MercadoPago
2. Cliente ingresa tarjeta → SDK tokeniza → card_token (nunca pasa por Food Store)
3. Frontend llama POST /api/v1/pagos/crear con card_token + pedido_id
4. Backend genera idempotency_key (UUID) → llama MercadoPago API
5. MercadoPago devuelve mp_payment_id + status
6. Backend INSERT en tabla Pago via UoW
7. MercadoPago envía POST /pagos/webhook IPN (topic=payment)
8. Si approved → UoW avanza Pedido a CONFIRMADO + decrementa stock
9. Frontend detecta con polling (30s) y actualiza UI
```

### Estados de Pago

| Estado MP | Acción en Food Store |
|---|---|
| `approved` | Webhook avanza pedido a CONFIRMADO automáticamente |
| `pending` | Pedido permanece en PENDIENTE |
| `rejected` | Mostrar `status_detail` al cliente. Pedido en PENDIENTE. |
| `in_process` | Pedido en PENDIENTE. Webhook notificará la resolución. |
| `cancelled` | Cliente puede reintentar o cancelar pedido. |

---

## 4. Configuración de Entornos

### Variables de Entorno — Backend (`.env`)

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/foodstore_db
SECRET_KEY=your-super-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=["http://localhost:5173"]
MP_ACCESS_TOKEN=TEST-xxxx
MP_PUBLIC_KEY=TEST-xxxx
MP_NOTIFICATION_URL=https://dominio.com/api/v1/pagos/webhook
```

### Variables de Entorno — Frontend (`.env`)

```env
VITE_API_URL=http://localhost:8000
VITE_MP_PUBLIC_KEY=TEST-xxxx
```

---

## 5. CORS

```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
