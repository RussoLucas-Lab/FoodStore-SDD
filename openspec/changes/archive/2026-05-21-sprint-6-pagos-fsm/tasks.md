## 1. Backend — Módulo Pagos: Modelos y Schemas

- [x] 1.1 Verificar que el modelo `Pago` en `backend/app/modules/pagos/model.py` tiene los campos: `id`, `pedido_id`, `estado_pago`, `idempotency_key`, `mp_preference_id`, `mp_payment_id`, `created_at`, `updated_at`
- [x] 1.2 Crear `backend/app/modules/pagos/schemas.py` con `PagoRead`, `CrearPagoRequest`, `CrearPagoResponse` (`preference_id`, `init_point`)
- [x] 1.3 Agregar `WEBHOOK_SECRET` y `MP_ACCESS_TOKEN` a `backend/.env.example`

## 2. Backend — Módulo Pagos: Repository y Service

- [x] 2.1 Crear `backend/app/modules/pagos/repository.py` con `PagoRepository(BaseRepository[Pago])`: métodos `get_by_pedido_id()`, `get_by_mp_payment_id()`, `create()`
- [x] 2.2 Crear `backend/app/modules/pagos/service.py` con `PagoService`:
  - `crear_preferencia(uow, pedido_id, usuario_id)` — valida pedido PENDIENTE + pertenece al usuario, idempotencia, crea preferencia MP SDK, persiste fila `Pago`
  - `procesar_webhook(uow, evento)` — valida firma, idempotencia por `mp_payment_id`, llama `PedidoService.confirmar_pedido()` si `status=approved`
  - `get_by_pedido(uow, pedido_id, usuario_id, rol)` — control de acceso CLIENT vs ADMIN
- [x] 2.3 Agregar validación de firma HMAC-SHA256 del header `x-signature` en `procesar_webhook()` usando `WEBHOOK_SECRET`
- [x] 2.4 Implementar idempotencia de webhook: verificar `pago.mp_payment_id` antes de procesar

## 3. Backend — Módulo Pagos: Router

- [x] 3.1 Crear `backend/app/modules/pagos/router.py` con:
  - `POST /api/v1/pagos/crear` (autenticado, rol CLIENT)
  - `POST /api/v1/pagos/webhook` (público, sin JWT)
  - `GET /api/v1/pagos/{pedido_id}` (autenticado, roles CLIENT/ADMIN/PEDIDOS)
- [x] 3.2 Registrar el router de pagos en `backend/app/main.py`

## 4. Backend — FSM de Pedidos: OrderStateMachine

- [x] 4.1 Crear `backend/app/modules/pedidos/fsm.py` con clase `OrderStateMachine`:
  - Mapa de transiciones permitidas (ver design.md tabla de roles)
  - Método `is_allowed(estado_actual, nuevo_estado, roles)` → bool
  - Marcar PENDIENTE → CONFIRMADO como automática (rechazar en PATCH manual)
  - Validar que ENTREGADO y CANCELADO son terminales
- [x] 4.2 Agregar método `requiere_motivo(nuevo_estado)` en `OrderStateMachine` (True si nuevo_estado == CANCELADO)

## 5. Backend — FSM de Pedidos: Endpoint PATCH y efectos de borde

- [x] 5.1 Agregar `CambiarEstadoRequest` y `CambiarEstadoResponse` en `backend/app/modules/pedidos/schemas.py`
- [x] 5.2 Agregar `PATCH /api/v1/pedidos/{id}/estado` en `backend/app/modules/pedidos/router.py` (autenticado)
- [x] 5.3 Implementar `PedidoService.cambiar_estado(uow, pedido_id, nuevo_estado, motivo, actor_id, actor_roles)`:
  - Validar pedido existe
  - Validar transición con `OrderStateMachine.is_allowed()`
  - Rechazar PENDIENTE → CONFIRMADO (RN-FS02)
  - Validar motivo obligatorio al cancelar (RN-FS09/RN-FS10)
  - Actualizar `pedido.estado_codigo`
  - Restaurar stock si CONFIRMADO → CANCELADO (RN-FS05)
  - Crear registro en `HistorialEstadoPedido` (append-only, RN-FS07)
- [x] 5.4 Implementar `PedidoService.confirmar_pedido(uow, pedido_id, actor_id)` llamado exclusivamente por `PagoService`:
  - Decrementar stock atómicamente por cada `DetallePedido` (RN-FS03/RN-FS04)
  - Rollback si stock resultante < 0
  - Crear registro en `HistorialEstadoPedido`
- [x] 5.5 Agregar `PedidoRepository.get_detalles_by_pedido_id()` si no existe
- [x] 5.6 Agregar `ProductoRepository.decrement_stock(producto_id, cantidad)` y `increment_stock(producto_id, cantidad)` si no existen

## 6. Backend — Pruebas de FSM y Pagos

- [x] 6.1 Crear `backend/tests/test_pagos.py`: test creación de preferencia, test idempotencia, test webhook approved, test webhook firma inválida, test idempotencia webhook
- [x] 6.2 Crear `backend/tests/test_pedidos_fsm.py`: test cada transición válida, test transiciones inválidas, test motivo obligatorio, test decremento stock, test restauración stock, test PENDIENTE→CONFIRMADO bloqueada en PATCH
- [x] 6.3 Correr `pytest backend/tests/` y verificar que todos los tests pasan

## 7. Frontend — CardPayment y hook de creación de pago

- [x] 7.1 Instalar `@mercadopago/sdk-react` con `npm install @mercadopago/sdk-react`
- [x] 7.2 Crear `frontend/src/features/checkout/components/CardPayment.tsx`:
  - Recibe `props: { pedidoId: number }`
  - Al montar, llama `POST /api/v1/pagos/crear` vía `useCrearPreferencia(pedidoId)` para obtener `preferenceId`
  - Renderiza brick/formulario de MP SDK con el `preferenceId`
  - Maneja estado de carga (spinner) y error (mensaje + botón reintentar)
- [x] 7.3 Crear `frontend/src/features/checkout/hooks/useCrearPreferencia.ts` (useMutation → `POST /api/v1/pagos/crear`)
- [x] 7.4 Crear `frontend/src/features/checkout/hooks/usePaymentStatus.ts`:
  - Acepta `pedidoId: number | null`
  - Solo activo cuando `paymentStore.status === 'processing'` y `pedidoId != null`
  - Polling cada 30 s con `setInterval` + cleanup en desmontaje
  - Llama `GET /api/v1/pagos/{pedido_id}` y actualiza `paymentStore` según resultado

## 8. Frontend — paymentStore

- [x] 8.1 Actualizar `frontend/src/store/paymentStore.ts` con estado FSM: `idle | processing | approved | rejected | error`
- [x] 8.2 Exponer acciones: `setProcessing(pedidoId: number)`, `setApproved()`, `setRejected()`, `setError(msg: string)`, `reset()`
- [x] 8.3 Asegurar que el store NO tiene `persist` configurado
- [x] 8.4 Tipar el store con TypeScript estricto (sin `any`)

## 9. Frontend — Pantallas de resultado de pago

- [x] 9.1 Crear `frontend/src/features/checkout/components/PagoExitoso.tsx`:
  - Muestra ícono check, "¡Tu pago fue aprobado!", número de pedido y total
  - CTAs: "Ver mi pedido" (`/pedidos/{id}`) y "Seguir comprando" (`/catalogo`)
  - Llama `clearCart()` al montar si carrito no está vacío
- [x] 9.2 Crear `frontend/src/features/checkout/components/PagoRechazado.tsx`:
  - Muestra ícono error, mensaje de rechazo
  - CTAs: "Intentar de nuevo" (resetea store, navega a `/checkout`) y "Cancelar pedido" (PATCH estado → CANCELADO)
- [x] 9.3 Agregar rutas `/checkout/pago-exitoso` y `/checkout/pago-rechazado` en React Router
- [x] 9.4 Lógica de redirección en `CheckoutPage`: cuando `paymentStore.status` cambia a `approved` → navegar a `/checkout/pago-exitoso`; a `rejected`/`error` → navegar a `/checkout/pago-rechazado`

## 10. Frontend — Integración en CheckoutForm

- [x] 10.1 Modificar `frontend/src/features/checkout/components/CheckoutForm.tsx`:
  - Agregar `useEffect(() => { paymentStore.reset() }, [])` al montar
  - Tras creación exitosa del pedido (`useCrearPedido.onSuccess`): llamar `paymentStore.setProcessing(pedido.id)` y renderizar `CardPayment`
- [x] 10.2 Agregar `usePaymentStatus(pedidoId)` en el componente que renderiza `CardPayment` o en `CheckoutPage`
- [x] 10.3 Verificar que el flujo completo funciona: crear pedido → ver CardPayment → pago aprobado (sandbox) → pantalla éxito

## 11. Verificación end-to-end

- [ ] 11.1 Levantar backend con `uvicorn app.main:app --reload` y verificar que Swagger muestra los nuevos endpoints de pagos y FSM
- [ ] 11.2 Probar manualmente con sandbox MP: crear preferencia → pagar → recibir webhook (ngrok) → pedido pasa a CONFIRMADO
- [ ] 11.3 Probar transiciones FSM vía Swagger: CONFIRMADO→EN_PREP, EN_PREP→EN_CAMINO, EN_CAMINO→ENTREGADO, cancelaciones con motivo
- [ ] 11.4 Probar caso de error: webhook con firma inválida devuelve 400; transición no permitida devuelve 422; cancelar sin motivo devuelve 422
- [ ] 11.5 Verificar frontend: flujo completo carrito → checkout → CardPayment → pago sandbox → pantalla éxito
