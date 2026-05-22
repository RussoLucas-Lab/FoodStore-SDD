## 1. Backend — Migration y modelos

- [x] 1.1 Agregar columnas a `Pedido` en `backend/app/modules/pedidos/model.py`: `forma_pago_codigo: Optional[str]` (FK a `forma_pago.codigo`, `max_length=50`, nullable a nivel BD por compat con SQLite), `idempotency_key: Optional[str]` (max_length 100, nullable, unique parcial), `costo_envio: Decimal` (Numeric(10,2), NOT NULL, default 0)
- [x] 1.2 Generar migration Alembic `alembic revision --autogenerate -m "add forma_pago_codigo idempotency_key costo_envio to pedido"` y editar el upgrade para crear índice único parcial sobre `(usuario_id, idempotency_key)` donde `idempotency_key IS NOT NULL` (en SQLite usar `CREATE UNIQUE INDEX ... WHERE`)
- [x] 1.3 Verificar/completar seed en `backend/app/db/seed.py`: roles ADMIN/STOCK/PEDIDOS/CLIENT, estados `EstadoPedido` (PENDIENTE orden=1, CONFIRMADO=2, EN_PREP=3, EN_CAMINO=4, ENTREGADO=5 terminal, CANCELADO=6 terminal), formas de pago (MERCADOPAGO, EFECTIVO, TRANSFERENCIA con `habilitado=true`)
- [x] 1.4 Correr `alembic upgrade head` y `python -m app.db.seed` y verificar que `pedido` tiene las nuevas columnas

## 2. Backend — Schemas Pydantic

- [x] 2.1 Crear `backend/app/modules/pedidos/schemas.py` con `ItemPedidoCreate` (`producto_id: int >=1`, `cantidad: int >=1`, `personalizacion: list[int] | None = None`, opcional `precio_esperado: Decimal | None = None`)
- [x] 2.2 Agregar `PedidoCreate` (`direccion_id: int`, `forma_pago_codigo: str`, `items: list[ItemPedidoCreate]` con `min_length=1`, opcional `notas: str | None`)
- [x] 2.3 Agregar `DetallePedidoRead` (`id`, `producto_id`, `nombre_snapshot`, `precio_snapshot`, `cantidad`, `personalizacion`)
- [x] 2.4 Agregar `PedidoRead` (`id`, `estado_codigo`, `total`, `created_at`) y `PedidoDetail` (extiende PedidoRead con `subtotal`, `costo_envio`, `direccion_snapshot`, `items: list[DetallePedidoRead]`) — el Detail queda preparado para Sprint 7
- [x] 2.5 Crear `backend/app/modules/pedidos/schemas_forma_pago.py` (o agregar a `schemas.py`) con `FormaPagoRead` (`codigo: str`, `descripcion: str | None`)

## 3. Backend — Repositorios

- [x] 3.1 Extender `backend/app/modules/pedidos/repository.py` `PedidoRepository` con: `get_by_usuario_idempotency_key(usuario_id, key) -> Pedido | None` y `create_pedido(pedido) -> Pedido` (delega al `BaseRepository.create`)
- [x] 3.2 Crear `DetallePedidoRepository` en `backend/app/modules/pedidos/repository.py` con `create(detalle) -> DetallePedido` y `list_by_pedido(pedido_id) -> list[DetallePedido]`
- [x] 3.3 Crear `HistorialEstadoPedidoRepository` con `create(historial) -> HistorialEstadoPedido` y `list_by_pedido(pedido_id) -> list[HistorialEstadoPedido]`
- [x] 3.4 Crear `FormaPagoRepository` en `backend/app/modules/pedidos/repository.py` (mismo módulo, archivo) con `get_by_codigo(codigo) -> FormaPago | None` y `list_habilitadas() -> list[FormaPago]`
- [x] 3.5 Extender `backend/app/modules/productos/repository.py` con `lock_productos(producto_ids: list[int]) -> list[Producto]` que ejecuta `select(Producto).where(Producto.id.in_(ordered_ids)).with_for_update()` ordenado ascendentemente

## 4. Backend — Unit of Work

- [x] 4.1 Editar `backend/app/core/uow.py` para exponer en el `UnitOfWork` los nuevos repositorios: `self.pedidos = PedidoRepository(session)`, `self.detalle_pedido = DetallePedidoRepository(session)`, `self.historial_pedido = HistorialEstadoPedidoRepository(session)`, `self.formas_pago = FormaPagoRepository(session)`

## 5. Backend — Servicios

- [x] 5.1 Crear `backend/app/modules/pedidos/service.py` con `FormaPagoService.list_habilitadas(uow) -> list[FormaPagoRead]`
- [x] 5.2 Implementar `PedidoService.crear(uow, usuario_id: int, body: PedidoCreate, idempotency_key: str | None = None) -> PedidoRead`:
  - Si `idempotency_key`: buscar `pedidos.get_by_usuario_idempotency_key`; si existe → devolver ese PedidoRead (sin HTTP 201, el router decide 200)
  - Validar `items` no vacío → 400 `CART_EMPTY`
  - Validar dirección: `uow.direcciones.get_by_id(direccion_id)` + check `usuario_id` y `deleted_at IS NULL` → 404 `DIRECCION_NOT_FOUND`
  - Validar forma de pago: `uow.formas_pago.get_by_codigo` + `habilitado=true` → 400 `FORMA_PAGO_NOT_FOUND`
  - Lock pesimista de productos: `uow.productos.lock_productos(sorted(unique_producto_ids))`
  - Por cada item validar producto: existe, `deleted_at IS NULL` → 400 `PRODUCTO_NOT_FOUND`; `disponible=true` → 409 `PRODUCTO_NO_DISPONIBLE`; `stock_cantidad >= cantidad` → 409 `STOCK_INSUFICIENTE` (con `field: producto_id`)
  - Por cada item con `personalizacion`: validar cada `ingrediente_id` ∈ `producto_ingrediente(producto_id)` → 400 `INGREDIENTE_NO_DEL_PRODUCTO`
  - Construir `direccion_snapshot` dict con todos los campos enumerados en design (id, calle, numero, piso, depto, ciudad, provincia, codigo_postal, referencia, es_principal)
  - Crear `Pedido(usuario_id, estado_codigo='PENDIENTE', direccion_snapshot, forma_pago_codigo, total=0, costo_envio=0, idempotency_key)` y persistir via `uow.pedidos.create_pedido`
  - Por cada item: construir `DetallePedido(pedido_id, producto_id, precio_snapshot=producto.precio_base, nombre_snapshot=producto.nombre, cantidad, personalizacion)` y persistir via `uow.detalle_pedido.create`
  - Calcular `total = Σ(cantidad × precio_snapshot) + costo_envio (=0)`; actualizar `pedido.total`
  - Crear `HistorialEstadoPedido(pedido_id, estado_desde=None, estado_hasta='PENDIENTE', cambiado_por_id=usuario_id, motivo=None)` via `uow.historial_pedido.create`
  - NO modificar `Producto.stock_cantidad` (RN-FS03 difiere a Sprint 6)
  - Devolver `PedidoRead.model_validate(pedido)`
- [x] 5.3 Instanciar singletons `pedido_service = PedidoService()` y `forma_pago_service = FormaPagoService()` al final del archivo

## 6. Backend — Router

- [x] 6.1 Crear `backend/app/modules/pedidos/router.py` con `APIRouter(prefix="/api/v1")` y dos endpoints
- [x] 6.2 `POST /pedidos`: depende de `get_current_user`; recibe `body: PedidoCreate`, header opcional `Idempotency-Key: str | None = Header(default=None, alias="Idempotency-Key")`; usa `with UnitOfWork() as uow:` y llama `pedido_service.crear(uow, current_user.id, body, idempotency_key)`; retorna 201 si fue creación nueva, 200 si fue idempotency hit (el service puede devolver tupla `(pedido, was_existing)` o el router compara `created_at` vs ahora; **decisión más simple**: el service devuelve siempre `PedidoRead` y el router siempre 201 — la idempotencia se manifiesta solo en no-duplicación, el código HTTP queda 201 en ambos casos)
- [x] 6.3 `GET /formas-pago`: depende de `get_current_user`; llama `forma_pago_service.list_habilitadas(uow)`; retorna `list[FormaPagoRead]`
- [x] 6.4 Registrar el router en `backend/app/main.py`: `app.include_router(pedidos_router.router)`

## 7. Backend — Tests

- [x] 7.1 `backend/tests/pedidos/test_crear_pedido_happy.py`: crear pedido con 1 item, asegurar HTTP 201, snapshots correctos, historial con `estado_desde=NULL`
- [x] 7.2 `test_crear_pedido_multi_item.py`: 3 items con uno personalizado; verificar 3 filas detalle y total correcto
- [x] 7.3 `test_crear_pedido_rollback.py`: simular falla en 3° item (stock insuficiente) y verificar que NO quedó nada persistido
- [x] 7.4 `test_crear_pedido_validaciones.py`: cubre CART_EMPTY, DIRECCION_NOT_FOUND (ajena/eliminada/inexistente), FORMA_PAGO_NOT_FOUND, PRODUCTO_NOT_FOUND, PRODUCTO_NO_DISPONIBLE, STOCK_INSUFICIENTE, INGREDIENTE_NO_DEL_PRODUCTO
- [x] 7.5 `test_crear_pedido_idempotency.py`: dos requests con misma `Idempotency-Key` → 1 sola fila en BD; el segundo devuelve el mismo PedidoRead
- [x] 7.6 `test_crear_pedido_no_decrementa_stock.py`: verificar que `Producto.stock_cantidad` no cambia tras crear el pedido
- [x] 7.7 `test_crear_pedido_snapshot_inmutable.py`: crear pedido, modificar `Producto.precio_base` y `Producto.nombre`, verificar que `DetallePedido` mantiene los originales; modificar/soft-delete `Direccion` y verificar `direccion_snapshot` intacto
- [x] 7.8 `test_formas_pago.py`: GET `/formas-pago` autenticado devuelve solo habilitadas, sin auth → 401, lista vacía si todas deshabilitadas
- [x] 7.9 `test_service_no_commit.py`: smoke test usando `grep`/inspect AST para verificar que `PedidoService` no contiene `session.commit()` ni `session.rollback()`
- [x] 7.10 Correr `pytest backend/tests/pedidos -v` y dejar todos en verde

## 8. Frontend — Tipos y endpoints

- [x] 8.1 Crear `frontend/src/types/pedidos.ts` con `PedidoRead`, `DetallePedidoRead`, `PedidoDetail`, `ItemPedidoCreate`, `PedidoCreate`
- [x] 8.2 Crear `frontend/src/types/formasPago.ts` con `FormaPagoRead`
- [x] 8.3 Crear `frontend/src/api/endpoints/pedidos.ts` con `crearPedido(body: PedidoCreate, idempotencyKey: string) => Promise<PedidoRead>` (envía header `Idempotency-Key`)
- [x] 8.4 Crear `frontend/src/api/endpoints/formasPago.ts` con `listFormasPago() => Promise<FormaPagoRead[]>`

## 9. Frontend — Hooks TanStack Query

- [x] 9.1 Crear `frontend/src/features/checkout/hooks/useFormasPago.ts` con `useFormasPago()` (useQuery key `['formas-pago']`)
- [x] 9.2 Crear `frontend/src/features/checkout/hooks/useCrearPedido.ts` con `useCrearPedido(idempotencyKey: string)` que retorna useMutation invocando `crearPedido`
- [x] 9.3 Exportar ambos en `frontend/src/features/checkout/hooks/index.ts`

## 10. Frontend — Componentes del Checkout

- [x] 10.1 Crear `frontend/src/features/checkout/components/OrderSummary.tsx` (read-only, lee `useCartStore(s => s.items)`, muestra renglones y total)
- [x] 10.2 Crear `frontend/src/features/checkout/components/PaymentMethodSelector.tsx` con props `{ selectedCodigo, onSelect }`, consume `useFormasPago`, renderiza radios con skeleton/error states
- [x] 10.3 Crear `frontend/src/features/checkout/components/PreCheckoutValidator.tsx` (o hook `usePreCheckoutValidation`) que: por cada `productoId` único hace `GET /productos/{id}`, compara `disponible`/`stock_cantidad`/`precio_base`, expone estado `{ status: 'idle' | 'checking' | 'ok' | 'stock-error' | 'price-changed', diffs: [...] }` y callback `acceptNewPrices()`
- [x] 10.4 Crear `frontend/src/features/checkout/components/CheckoutForm.tsx` que orquesta `OrderSummary`, `AddressSelector`, `PaymentMethodSelector`, `PreCheckoutValidator` y un botón "Confirmar pedido". Maneja estados locales `selectedDireccionId`, `selectedFormaPago`, `idempotencyKey` (generado con `crypto.randomUUID()` en `useMemo([])`)
- [x] 10.5 Crear `frontend/src/features/checkout/components/PedidoConfirmacion.tsx` que lee `useLocation().state?.pedido` y muestra ícono éxito, número de pedido, total, dos CTAs ("Ver mis pedidos" → `/pedidos`, "Seguir comprando" → `/catalogo`); fallback si no hay state
- [x] 10.6 Exportar todos los componentes en `frontend/src/features/checkout/components/index.ts` (sin tocar exports existentes)

## 11. Frontend — Pages y rutas

- [x] 11.1 Reemplazar `frontend/src/pages/CheckoutPage.tsx` por una page que: lee `useCartStore(s => s.items)`; si vacío, muestra estado vacío con CTA a `/catalogo`; si no vacío, renderiza `<CheckoutForm />`
- [x] 11.2 Crear `frontend/src/pages/PedidoConfirmadoPage.tsx` que renderiza `<PedidoConfirmacion />`
- [x] 11.3 Editar `frontend/src/App.tsx`: agregar `<Route path="/checkout/confirmado" element={<ProtectedRoute><PedidoConfirmadoPage /></ProtectedRoute>} />` dentro del `AppLayout`

## 12. Frontend — Integración con carrito

- [x] 12.1 Editar `frontend/src/features/carrito/components/CartDrawer.tsx`: el botón "Ir a checkout" usa `useNavigate()` para ir a `/checkout` y cierra el drawer via `useUiStore.getState().setCartOpen(false)` (o equivalente, dependiendo de la API del uiStore)
- [x] 12.2 En `useCrearPedido` `onSuccess`: invocar `useCartStore.getState().clearCart()` y `navigate('/checkout/confirmado', { state: { pedido: data } })`
- [x] 12.3 En `useCrearPedido` `onError`: mostrar toast con `error.response?.data?.detail` y NO limpiar el carrito

## 13. Frontend — Tests

- [x] 13.1 `frontend/src/features/checkout/components/__tests__/CheckoutForm.test.tsx`: render con carrito poblado, dirección y forma de pago seleccionadas → botón habilitado; submit dispara mutation con body correcto
- [x] 13.2 `frontend/src/features/checkout/components/__tests__/OrderSummary.test.tsx`: render con items, verifica subtotales y total
- [x] 13.3 `frontend/src/features/checkout/components/__tests__/PaymentMethodSelector.test.tsx`: mock hook con 3 formas; click en una invoca `onSelect`
- [x] 13.4 `frontend/src/features/checkout/components/__tests__/PedidoConfirmacion.test.tsx`: render con `location.state.pedido` muestra número y total; render sin state muestra fallback
- [x] 13.5 Test integración: tras success de `useCrearPedido`, `useCartStore.items` queda vacío y navigate fue invocado con `/checkout/confirmado`

## 14. Verificación end-to-end

- [x] 14.1 Levantar backend (`uvicorn app.main:app --reload`) y frontend (`npm run dev`)
- [ ] 14.2 Login como CLIENT, agregar items al carrito desde el catálogo, abrir `CartDrawer`, click "Ir a checkout"
- [ ] 14.3 En `/checkout`: seleccionar dirección (o crear una inline), seleccionar forma de pago, verificar resumen, click "Confirmar pedido"
- [ ] 14.4 Verificar redirect a `/checkout/confirmado` con número de pedido y total correctos
- [ ] 14.5 Verificar en BD que existe: 1 fila `pedido` (estado=PENDIENTE, total correcto, direccion_snapshot completo, forma_pago_codigo), N filas `detalle_pedido` (con snapshots), 1 fila `historial_estado_pedido` (estado_desde=NULL)
- [ ] 14.6 Verificar que `Producto.stock_cantidad` NO cambió
- [ ] 14.7 Probar doble click rápido en "Confirmar pedido": verificar que solo se crea 1 pedido (idempotencia)
- [ ] 14.8 Probar checkout con producto sin stock suficiente → banner de error y botón bloqueado
- [ ] 14.9 Probar Swagger en `/docs`: `POST /pedidos` y `GET /formas-pago` documentados con sus schemas
- [ ] 14.10 Verificar checklist CE-10 del proyecto: `grep -r "session.commit" backend/app/modules/pedidos/service.py` → debe estar vacío
