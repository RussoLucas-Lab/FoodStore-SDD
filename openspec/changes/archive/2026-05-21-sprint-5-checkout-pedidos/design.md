## Context

Estado actual (post-Sprint 4):
- Modelos `Pedido`, `DetallePedido`, `EstadoPedido`, `HistorialEstadoPedido`, `FormaPago` y `Pago` existen como tablas SQLModel pero solo el `Pedido` tiene un repositorio mínimo (`PedidoRepository` heredando de `BaseRepository`). No hay schemas, service, ni router.
- `cartStore` (Zustand persistido) maneja items con `lineId` derivado de `productoId + ingredientes_excluidos`. Cada item guarda `productoId`, `nombre`, `precio`, `cantidad`, `ingredientesExcluidosIds`, `ingredientesExcluidosNombres`.
- `AddressSelector` ya devuelve el `id` de la dirección seleccionada vía callback `onSelect`.
- `CheckoutPage` es un placeholder.
- El backend usa SQLite en dev (no PostgreSQL); por lo tanto `SELECT FOR UPDATE` se aplica mediante `with_for_update()` de SQLAlchemy — funciona como no-op en SQLite pero queda correcto en PostgreSQL.
- El catálogo (`Producto`) ya tiene `stock_cantidad`, `precio_base` y `disponible`.

Restricciones obligatorias (de `CLAUDE.md` y `docs/BUSINESS_RULES.md`):
- **Patrón**: Router → Service → UoW → Repository → Model. **El Service nunca llama `session.commit()`**.
- **RN-PE01**: creación atómica todo-o-nada.
- **RN-PE02 / RN-PE03**: snapshots inmutables de precio, nombre y dirección.
- **RN-PE04 / RN-PE05**: validación de stock con `SELECT FOR UPDATE` dentro de la transacción.
- **RN-PE06**: pedido nace en `PENDIENTE` con un `HistorialEstadoPedido(estado_desde=NULL)`.
- **RN-PE08**: `total = Σ(cantidad × precio_snapshot) + costo_envio`. En Sprint 5 `costo_envio = 0`.
- **RN-FS03**: el decremento de stock ocurre al confirmar el pago — no en Sprint 5.
- **Seguridad**: `usuario_id` viene del JWT, nunca del body.

Stakeholders implícitos: cliente final (US-067 a US-071) y Sprint 6 que dependerá de poder crear pedidos para conectar MercadoPago.

## Goals / Non-Goals

**Goals:**
- Habilitar la creación atómica de pedidos vía `POST /api/v1/pedidos`.
- Persistir snapshots inmutables de precio por línea, nombre por línea y dirección completa.
- Registrar el primer evento de `HistorialEstadoPedido` en la misma transacción.
- Bloquear las filas de `Producto` involucradas con `with_for_update()` para evitar oversell en concurrencia (efecto real en PostgreSQL).
- Validar que: (a) el carrito no esté vacío, (b) cada producto exista y esté activo (`deleted_at IS NULL`), (c) `disponible=true`, (d) `stock_cantidad >= cantidad_pedida`, (e) la dirección pertenezca al usuario autenticado, (f) la `forma_pago_codigo` exista y esté `habilitado=true`.
- Devolver un `PedidoRead` con `id`, `estado_codigo`, `total`, `created_at` que el frontend usa para la pantalla de confirmación.
- Exponer un endpoint público autenticado `GET /api/v1/formas-pago` para poblar el selector.
- Completar la pantalla `/checkout` con resumen, selector de dirección, selector de forma de pago, validación pre-checkout (re-fetch de precios y disponibilidad) y confirmación visual con número de pedido.
- Limpiar el carrito (`clearCart()`) al confirmar exitosamente.

**Non-Goals:**
- Integración con MercadoPago (Sprint 6).
- Crear el registro `Pago` (Sprint 6 lo manejará al iniciar el flujo MP).
- Decrementar `stock_cantidad` (Sprint 6, al confirmar pago).
- FSM completa de pedidos: `PATCH /pedidos/{id}/estado`, `DELETE /pedidos/{id}` quedan fuera de este sprint.
- Listado de pedidos del cliente (`GET /pedidos`) y detalle (`GET /pedidos/{id}`) — los maneja Sprint 7.
- Webhook IPN ni polling de pago — Sprint 6.
- `costo_envio`: queda en 0 en Sprint 5 (el campo no existe aún en `Pedido`, se persiste solo el `total`).
- Recuperar y mostrar el historial del pedido en el frontend.

## Decisions

### 1. Persistir `forma_pago_codigo` como campo del `Pedido`

**Problema**: el frontend necesita enviar la forma de pago elegida y el sistema debe recordarla; sin embargo el modelo actual de `Pedido` no tiene FK a `FormaPago` (el `Pago` sí, pero `Pago` se crea en Sprint 6).

**Decisión**: agregar columna `forma_pago_codigo: str` (FK a `forma_pago.codigo`) al modelo `Pedido` via migration Alembic en este sprint. Es información del pedido (qué medio se eligió) y la decisión es ortogonal al registro `Pago` (que es la transacción concreta).

**Alternativas consideradas**:
- *(a)* Crear el registro `Pago` ya en Sprint 5 con `estado='pending'`: rechazada porque acopla el flujo de creación con el dominio de pagos antes de tiempo y porque MercadoPago genera `idempotency_key` y `external_reference` recién al iniciar checkout MP.
- *(b)* Guardar la forma de pago solo en frontend y enviarla al crear el `Pago` en Sprint 6: rechazada porque pierde trazabilidad si el cliente abandona antes de pagar.

**Justificación**: la columna agrega cero costo, no rompe nada y deja el modelo coherente con el snapshot pattern (lo que el cliente eligió queda registrado).

### 2. `SELECT FOR UPDATE` ordenado por `producto_id` ascendente

**Problema**: si dos clientes piden el mismo subconjunto de productos en orden inverso, los locks de PostgreSQL pueden generar deadlock.

**Decisión**: el service ordena los `producto_id` del carrito ascendentemente antes de hacer los `with_for_update()` individuales (o uno solo con `IN (...)` con `ORDER BY id`).

**Alternativas**:
- *(a)* Lock pesimista por `IN (producto_ids)` sin ordenar: PostgreSQL puede adquirir en orden no determinístico → deadlock.
- *(b)* Lock optimista (versionado): rechazada por complejidad y porque no soluciona el requisito de "validar dentro de la transacción".

### 3. Snapshot de dirección como `dict` JSON

**Problema**: `Pedido.direccion_snapshot` está tipado como `dict` en `Column(JSON)`. ¿Qué campos snapshotear?

**Decisión**: snapshotear TODOS los campos visibles de la dirección al momento del pedido:
`{ id, calle, numero, piso, depto, ciudad, provincia, codigo_postal, referencia, es_principal }`.
Se guarda también el `id` original como traza, pero el comportamiento del pedido es inmune a cambios o soft-delete posteriores sobre la dirección.

**Alternativas**:
- Snapshot mínimo (solo string formateado): rechazada porque pierde estructura para listados/etiquetas/futuras integraciones logísticas.

### 4. Validación pre-checkout en frontend

**Problema**: el carrito vive en localStorage; los precios y disponibilidad pueden haber cambiado desde que el usuario agregó los items (US-069, US-070).

**Decisión**: antes de invocar `useCrearPedido()`, el `CheckoutForm` ejecuta `GET /api/v1/productos/{id}` por cada `productoId` del carrito (`Promise.all`) y compara:
- Si algún producto vino con `disponible=false`, `deleted_at != null`, o `stock_cantidad < cantidad_pedida` → mostrar banner "Algunos productos ya no están disponibles" y bloquear el botón "Confirmar pedido".
- Si algún `precio_base` difiere del `precio` guardado en el `cartItem` → mostrar banner "Los precios cambiaron" y obligar al usuario a aceptar el nuevo precio (que se sincroniza en el cartStore) antes de continuar.

El backend igualmente revalida y rechaza con HTTP 409 si algo cambió entre el pre-check y el submit (segunda línea de defensa).

**Alternativas**:
- Solo validar en backend: rechazada porque obliga al usuario a fallar para enterarse del cambio (mala UX).

### 5. Endpoint `GET /api/v1/formas-pago`

**Decisión**: vivir dentro del router de pedidos (`backend/app/modules/pedidos/router.py`) como `@router.get("/formas-pago")` para no crear un módulo entero solo para un GET sin filtros. Requiere autenticación (no exponer el catálogo público de formas de pago a no-clientes).

### 6. Errores RFC 7807 específicos

| Código | HTTP | Cuándo |
|---|---|---|
| `CART_EMPTY` | 400 | items vacío |
| `PRODUCTO_NOT_FOUND` | 400 | un producto del carrito no existe o `deleted_at != null` |
| `PRODUCTO_NO_DISPONIBLE` | 409 | `disponible=false` |
| `STOCK_INSUFICIENTE` | 409 | `stock_cantidad < cantidad`. Incluye `field: producto_id` |
| `PRECIO_DESACTUALIZADO` | 409 | cliente envía `precio_esperado` (opcional) y difiere del actual |
| `DIRECCION_NOT_FOUND` | 404 | dirección no existe, ya fue eliminada (`deleted_at != null`) o no pertenece al usuario |
| `FORMA_PAGO_NOT_FOUND` | 400 | código de forma de pago no existe o `habilitado=false` |
| `INGREDIENTE_NO_DEL_PRODUCTO` | 400 | un id de `personalizacion` no pertenece al producto |

### 7. Idempotencia opcional vía `Idempotency-Key`

**Decisión** (light): el endpoint acepta header opcional `Idempotency-Key`. Si está presente y ya hay un pedido del mismo usuario con esa key en los últimos 10 minutos (tabla auxiliar minimal o columna `idempotency_key` en `Pedido` con índice único parcial), se devuelve el pedido existente con HTTP 200 en lugar de crear duplicado.

**Trade-off**: si Sprint 6 va a manejar idempotencia full a nivel `Pago`, podríamos no hacerlo aquí. **Resolución**: implementarlo aquí porque el problema real (doble click en "Confirmar pedido") aparece ANTES de pasar por MercadoPago. La columna se llamará `idempotency_key` con índice único parcial `WHERE idempotency_key IS NOT NULL`.

### 8. Frontend — composición de `CheckoutPage`

```
/checkout
└── CheckoutPage (page)
    └── CheckoutForm (orquestador)
        ├── OrderSummary           — Lee cartStore, muestra renglones + totales
        ├── AddressSelector        — Reutilizado de Sprint 4 (state: selectedDireccionId)
        ├── PaymentMethodSelector  — Lista formas de pago habilitadas (state: selectedFormaPago)
        ├── PreCheckoutValidator   — Re-fetch productos, banners si cambió algo
        └── ConfirmarButton        — Dispara useCrearPedido()

post-success → navigate("/checkout/confirmado", { state: { pedido } })
                └── PedidoConfirmacion (page o vista) — número, total, CTA "Ver mis pedidos"
```

`PedidoConfirmacion` puede vivir como sub-ruta `/checkout/confirmado` o como estado interno; **decisión**: sub-ruta dedicada para permitir refresh sin perder el contexto (lee el `pedido_id` de URL params: `/checkout/confirmado/:pedidoId` + fetch via `GET /pedidos/{id}` cuando exista en Sprint 7; en Sprint 5 mostramos solo lo que vino en `location.state`).

### 9. Limpieza del carrito

**Decisión**: el `clearCart()` se invoca solo en el `onSuccess` de `useCrearPedido` (NO en `onMutate`), para que en caso de error de red el carrito siga intacto y el usuario pueda reintentar.

## Risks / Trade-offs

- **Riesgo**: `with_for_update()` es no-op en SQLite (entorno dev). → **Mitigación**: tests de integración correr en PostgreSQL en CI (Sprint 0 ya lo dejó listo); test unitario verifica que el ORM emite `FOR UPDATE` consultando el SQL compilado.
- **Riesgo**: en producción, mantener el lock durante I/O lento (red lenta, JWT lookup) podría reducir throughput. → **Mitigación**: el service hace todo el trabajo síncrono dentro de la transacción una vez adquirido el lock; no hay llamadas externas dentro del lock.
- **Riesgo**: el frontend muestra el "precio actual" según `precio_base`, pero el backend guarda `precio_snapshot` en el momento exacto del commit; podrían diferir si pasa una promoción justo entre el pre-check y el commit. → **Mitigación**: el backend devuelve el `total` final en la respuesta; el frontend lo muestra como autoridad. Si el cliente quiere fallar fuerte ante divergencia, puede enviar `precio_esperado` por línea y el backend devuelve `PRECIO_DESACTUALIZADO` (409).
- **Riesgo**: el `personalizacion: List[int]` no valida que los IDs pertenezcan al producto. → **Mitigación**: validación en service (`INGREDIENTE_NO_DEL_PRODUCTO`) consultando `ProductoIngrediente`.
- **Riesgo**: el migration añade `forma_pago_codigo` a una tabla que ya puede tener filas dummy en dev. → **Mitigación**: el migration agrega la columna como `NULLABLE` y luego, si no hay filas previas, la promueve a `NOT NULL` con `default='MERCADOPAGO'`. Como dev usa SQLite, hacemos `ALTER TABLE ... ADD COLUMN ... NULL` (compatible con SQLite) y dejamos la columna `Optional` en el modelo SQLModel; el service la asigna siempre.
- **Trade-off**: la idempotencia "light" usa columna en `Pedido` en lugar de tabla aparte; menos código pero menos extensible si más recursos necesitan idempotencia. **Aceptado** — Sprint 6 puede generalizar si hace falta.
- **Trade-off**: `PedidoConfirmacion` lee `location.state` en Sprint 5 y se "rompe" si el usuario refresca antes de Sprint 7. **Aceptado**: se muestra un fallback "El pedido se creó correctamente, ver en /pedidos" y se evita persistir nada extra en localStorage.

## Migration Plan

1. **Backend — migrations Alembic**
   1.1. Revisar que `Pedido`, `DetallePedido`, `HistorialEstadoPedido`, `EstadoPedido`, `FormaPago` ya estén materializadas (lo están desde Sprint 0). Si no, generar migration para crearlas.
   1.2. Generar migration `add_forma_pago_codigo_and_idempotency_key_to_pedido` que agrega:
       - `forma_pago_codigo VARCHAR(50) NULL` (FK a `forma_pago.codigo`).
       - `idempotency_key VARCHAR(100) NULL` con índice único parcial donde NOT NULL.
   1.3. Verificar seed de `EstadoPedido` (PENDIENTE, CONFIRMADO, EN_PREP, EN_CAMINO, ENTREGADO, CANCELADO) y `FormaPago` (MERCADOPAGO, EFECTIVO, TRANSFERENCIA). Si falta, completar `app/db/seed.py`.

2. **Backend — código**
   2.1. Schemas Pydantic: `ItemPedidoCreate`, `PedidoCreate`, `PedidoRead`, `DetallePedidoRead`, `FormaPagoRead`.
   2.2. Repositorios: extender `PedidoRepository` (`create_pedido_completo(uow, ...)`, `get_by_idempotency_key`) y nuevo `FormaPagoRepository`, `HistorialEstadoPedidoRepository`. Agregar `lock_productos(producto_ids)` en `ProductoRepository`.
   2.3. UoW: registrar `pedidos`, `historial_estado_pedido`, `formas_pago`.
   2.4. Service `PedidoService.crear(uow, usuario_id, body, idempotency_key=None)` implementa toda la lógica.
   2.5. Service `FormaPagoService.list_habilitadas(uow)`.
   2.6. Router con `POST /api/v1/pedidos` y `GET /api/v1/formas-pago` (ambos auth required).
   2.7. Registro en `main.py`.

3. **Frontend**
   3.1. Tipos `frontend/src/types/pedidos.ts` y `frontend/src/types/formasPago.ts`.
   3.2. Endpoints `frontend/src/api/endpoints/pedidos.ts` y `formasPago.ts`.
   3.3. Hooks `useFormasPago`, `useCrearPedido` en `frontend/src/features/checkout/hooks/`.
   3.4. Componentes: `OrderSummary`, `PaymentMethodSelector`, `CheckoutForm`, `PedidoConfirmacion`.
   3.5. Reemplazar `CheckoutPage.tsx` por la nueva composición. Agregar ruta `/checkout/confirmado` en `App.tsx`.
   3.6. Ajustar `CartDrawer` para que "Ir a checkout" use `useNavigate('/checkout')` y cierre el drawer (`useUiStore.setCartOpen(false)`).

4. **Verificación**
   - Tests backend: pytest sobre service (happy path, carrito vacío, stock insuficiente, producto eliminado, dirección ajena, forma de pago inhabilitada, idempotencia, snapshot inmutable).
   - Tests frontend: render del CheckoutForm con dirección/forma seleccionadas habilita botón; mock de mutation devuelve pedido; navegación a `/checkout/confirmado`; cartStore queda vacío.
   - Manual: flujo completo desde catálogo → carrito → checkout → confirmación, con admin verificando en DB que se crearon Pedido + N DetallePedido + 1 HistorialEstadoPedido con `estado_desde=NULL`.

5. **Rollback**
   - Migration es additive (solo agrega columnas con NULL). Rollback safe: `alembic downgrade -1` quita las columnas.
   - Si el rollback ocurre con pedidos ya creados, las columnas se pierden pero los pedidos quedan consistentes (las columnas eran nullable).

## Open Questions

- ¿`costo_envio` debe persistirse como columna en `Pedido` desde ya con default 0, o esperamos a Sprint 6? **Propuesta**: agregarlo en este sprint como `Numeric(10,2) NOT NULL DEFAULT 0` para no tener que cambiar el schema del response en Sprint 7. **Decisión sugerida**: incluirlo en la migration de este sprint.
- ¿La pantalla `PedidoConfirmacion` necesita el resumen completo del pedido (items + snapshots) o alcanza con `{ id, total, estado }`? **Propuesta**: alcanza con lo mínimo en Sprint 5; el detalle completo será reutilizado en Sprint 7 (`GET /pedidos/{id}`).
- ¿`Idempotency-Key` debe ser obligatorio para clientes web (header generado por axios interceptor con `uuid()`)? **Propuesta**: opcional en spec, pero el axios interceptor del frontend lo genera por defecto antes de cada POST a `/pedidos` para protegernos del doble-click.
