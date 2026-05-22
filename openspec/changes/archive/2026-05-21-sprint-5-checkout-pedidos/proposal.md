## Why

Con el carrito persistido y el `AddressSelector` listos (Sprint 4), el cliente todavía no puede materializar la compra: el carrito vive solo en el front, no existe el endpoint que lo convierta en un `Pedido` real con snapshots inmutables ni la página de checkout que orqueste el flujo. Sprint 5 cierra ese hueco habilitando el endpoint atómico `POST /api/v1/pedidos` (con `SELECT FOR UPDATE` de stock, snapshots de precio/dirección y primer registro de historial) y la pantalla `/checkout` que une dirección + forma de pago + resumen + confirmación visual. Sin esto, Sprint 6 (MercadoPago) no tiene `pedido_id` sobre el que registrar el pago.

## What Changes

- **Nuevo módulo `pedidos`** en el backend con creación atómica:
  - `POST /api/v1/pedidos` — Crea `Pedido` + N `DetallePedido` + 1° `HistorialEstadoPedido` en una sola transacción (UoW).
  - Validación de disponibilidad de productos y stock con `SELECT FOR UPDATE` (RN-PE04).
  - Snapshot de precio y nombre por línea (`precio_snapshot`, `nombre_snapshot`) — RN-PE02.
  - Snapshot completo de dirección (`direccion_snapshot`) tomado al momento del pedido — RN-PE03.
  - Cálculo del total = Σ(`cantidad × precio_snapshot`) — RN-PE08 (Sprint 5 sin `costo_envio`; queda en 0 hasta Sprint 6).
  - Pedido nace en estado `PENDIENTE` con `HistorialEstadoPedido(estado_desde=NULL, estado_hasta='PENDIENTE')` — RN-PE06.
  - Rollback total ante cualquier fallo (RN-PE01, RN-PE05).
- **Nueva feature `checkout`** completada en el frontend:
  - Reemplazo del placeholder `CheckoutPage` por un `CheckoutForm` con tres secciones: resumen del carrito, selector de dirección (reusa `AddressSelector`), selector de forma de pago.
  - Hooks TanStack Query: `useFormasPago()`, `useCrearPedido()`.
  - Validación pre-checkout (US-069, US-070): verifica disponibilidad y precio actualizado contra `GET /productos/{id}` antes de despachar la mutation.
  - Pantalla de confirmación visual (`PedidoConfirmacion`) con número de pedido, total y CTA a "Ver mis pedidos" (US-071).
  - Limpieza del `cartStore` (`clearCart()`) tras la creación exitosa del pedido.
- **Endpoint auxiliar de catálogo en el backend**: `GET /api/v1/formas-pago` (lista las formas habilitadas) — necesario para poblar el selector del checkout (no hay módulo aún, se agrega como router liviano dentro del módulo `pedidos`).

## Capabilities

### New Capabilities
- `pedidos-backend`: módulo backend de pedidos — creación atómica con snapshots de precio/nombre por línea, snapshot de dirección, lock de stock `SELECT FOR UPDATE`, primer registro de historial, validaciones de disponibilidad y forma de pago, errores RFC 7807.
- `formas-pago-backend`: endpoint público (autenticado) `GET /api/v1/formas-pago` que lista las formas de pago habilitadas (`habilitado=true`), para alimentar el selector de checkout.

### Modified Capabilities
- `checkout-frontend`: agrega `CheckoutPage` real con `CheckoutForm` (resumen + dirección + forma de pago), validación pre-checkout, hooks `useFormasPago` y `useCrearPedido`, y pantalla `PedidoConfirmacion`. El `AddressSelector` existente se reutiliza sin cambios estructurales.
- `carrito-frontend`: el `CartDrawer` agrega navegación a `/checkout` desde el botón "Ir a checkout" y el `cartStore` se invoca con `clearCart()` desde el flujo de confirmación. Sin cambios en los selectores ni en la API del store.

## Impact

- **Backend**:
  - Nuevo módulo `backend/app/modules/pedidos/` (faltan `service.py`, `router.py`, `schemas.py`; `model.py` y `repository.py` ya existen). Se extiende `repository.py` con `create_with_detalles` y `historial_create`.
  - Extensión del `UnitOfWork` para exponer `pedidos`, `detalle_pedido`, `historial_pedido` y `forma_pago`.
  - Registro de los nuevos routers en `backend/app/main.py`.
  - Lock de stock `SELECT FOR UPDATE` aplicado sobre `Producto` por cada producto del carrito (productos ordenados por `id` ascendente para evitar deadlocks).
  - Se asume el seed de `EstadoPedido` (PENDIENTE...) y `FormaPago` (MERCADOPAGO, EFECTIVO, TRANSFERENCIA) ya está hecho en Sprint 0 — caso contrario se completa el `seed.py`.
- **Frontend**:
  - Reemplazo total de `frontend/src/pages/CheckoutPage.tsx`.
  - Nuevos archivos en `frontend/src/features/checkout/`: `CheckoutForm.tsx`, `PedidoConfirmacion.tsx`, `OrderSummary.tsx`, `PaymentMethodSelector.tsx`, hooks `useFormasPago.ts` y `useCrearPedido.ts`, endpoint `frontend/src/api/endpoints/pedidos.ts` y `frontend/src/api/endpoints/formasPago.ts`.
  - Nuevos tipos `frontend/src/types/pedidos.ts` y `frontend/src/types/formasPago.ts`.
  - Ajuste mínimo en `CartDrawer.tsx`: el botón "Ir a checkout" navega a `/checkout` via `useNavigate`.
- **Sin breaking changes** en módulos anteriores (auth, categorias, ingredientes, productos, direcciones, carrito).
- **Stock**: el endpoint NO decrementa stock todavía — el decremento atómico ocurre al confirmar el pago (Sprint 6, RN-FS03). Sprint 5 solo bloquea (FOR UPDATE) y valida disponibilidad, pero NO modifica `stock_cantidad` (queda explícito en design.md).
- **Pago**: la creación del registro `Pago` y la integración con MercadoPago se difiere a Sprint 6; este sprint solo guarda `forma_pago_codigo` como dato auxiliar dentro del pedido (no como FK persistente, se posterga al modelar `Pago`).
- **Seguridad**: el endpoint exige `CLIENT` o cualquier usuario autenticado; el `usuario_id` se toma del token JWT (nunca del body).
- **Dependencias**: ninguna nueva.
