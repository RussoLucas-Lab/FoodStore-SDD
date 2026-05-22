## Context

Tras Sprint 5, los pedidos se crean correctamente en estado PENDIENTE con snapshots y validación de stock, pero el flujo queda bloqueado: no existe integración con MercadoPago para procesar el cobro, ni la FSM de pedidos para avanzar estados. El stock no se decrementa hasta que se confirma el pago (decisión de Sprint 5), por lo que habilitar la FSM + webhook es la deuda técnica más urgente. El modelo `Pago` ya existe en la BD desde Sprint 0; solo falta activar los flujos de escritura.

El proyecto usa in-memory repositories como sustituto de SQLAlchemy real + PostgreSQL para el entorno de desarrollo. Los patrones de UoW y Repository aplican igual.

## Goals / Non-Goals

**Goals:**
- Integrar MercadoPago SDK Python para crear preferencias de pago con `idempotency_key`
- Implementar endpoint webhook IPN `POST /pagos/webhook` que transiciona pedido PENDIENTE → CONFIRMADO automáticamente
- Implementar FSM completa de pedidos (`PATCH /pedidos/{id}/estado`) con todas las transiciones permitidas
- Decrementar/restaurar stock atómicamente en las transiciones que lo requieren
- Renderizar `CardPayment` con MercadoPago SDK React en checkout
- Integrar `paymentStore` con polling de estado cada 30 segundos

**Non-Goals:**
- Soporte multi-currency o multi-gateway (solo MercadoPago en este sprint)
- Notificaciones push o WebSocket en tiempo real (el polling cubre el requisito)
- Devoluciones / refunds automatizados (fuera de alcance)
- Gestión de disputas o chargebacks

## Decisions

### D1 — OrderStateMachine como clase standalone en `pedidos/fsm.py`

**Decisión**: Extraer la lógica de transiciones a una clase `OrderStateMachine` separada, importada por `PedidoService`.

**Alternativa descartada**: Inline en el service (todo en `pedidos/service.py`). Descartada porque el service ya es complejo y la FSM tiene lógica propia que conviene testear de forma aislada.

**Rationale**: La FSM define el mapa de transiciones permitidas, quién puede ejecutarlas y los efectos de borde (stock, historial). Encapsularla en `pedidos/fsm.py` hace el código más testeable y alinea con SRP.

### D2 — Webhook valida firma X-Signature de MercadoPago

**Decisión**: Validar la firma HMAC-SHA256 enviada por MercadoPago en el header `x-signature` antes de procesar cualquier evento IPN. Rechazar con HTTP 400 si no coincide.

**Alternativa descartada**: Confiar solo en el IP source de MercadoPago. Descartada porque es frágil (IPs cambian) y no es PCI-recommended.

**Rationale**: MercadoPago envía un header `x-signature` con HMAC del body usando el `WEBHOOK_SECRET`. Validar esto previene replay attacks y procesamiento de eventos falsos.

### D3 — Idempotencia de webhook: campo `mp_payment_id` en tabla `Pago`

**Decisión**: Antes de procesar un IPN, consultar si ya existe una fila en `pago` con `mp_payment_id = evento.data.id`. Si existe, devolver HTTP 200 sin reprocesar.

**Rationale**: MercadoPago puede reenviar el mismo IPN varias veces (política "at least once"). Sin idempotencia, el pedido se confirmaría y el stock se decrementaría múltiples veces.

### D4 — Frontend polling con `setInterval` en `usePaymentStatus`

**Decisión**: Crear un hook `usePaymentStatus(pedidoId)` que hace `GET /api/v1/pagos/{pedido_id}` cada 30 segundos mientras `paymentStore.status` sea `processing`. Se detiene cuando el estado es `approved`, `rejected` o `error`.

**Alternativa descartada**: WebSocket. Descartada por complejidad de infraestructura fuera del alcance del sprint.

**Rationale**: El polling de 30 s cumple US-072 con implementación simple y sin dependencias adicionales. El hook limpia el interval en el `useEffect` cleanup.

### D5 — `paymentStore` como FSM de UI con 5 estados

**Decisión**: `paymentStore` gestiona el estado del pago con la FSM: `idle → processing → approved | rejected | error`. Las transiciones se disparan desde `useCrearPedido.onSuccess` (→ processing) y desde el webhook response del polling (→ approved/rejected).

**Rationale**: Mantener el estado de pago en Zustand permite que cualquier componente (pantalla de confirmación, header) reaccione sin prop-drilling.

### D6 — Stock decrementa en `PENDIENTE → CONFIRMADO` dentro del UoW

**Decisión**: El decremento de stock (`Producto.stock_cantidad -= cantidad`) ocurre dentro del mismo `UnitOfWork` que registra la transición de estado y crea el historial. Si el decremento deja stock negativo (race condition), lanzar `HTTPException(409)` y hacer rollback.

**Rationale**: Atomicidad garantizada. El lock pesimista de Sprint 5 ya está en `POST /pedidos`; aquí el riesgo de race condition es bajo ya que el pedido ya fue validado, pero el guard doble protege ante casos extremos.

## Risks / Trade-offs

- **[Risk] Webhook URL no accesible en desarrollo local** → Mitigation: documentar uso de ngrok (`ngrok http 8000`) para exponer el endpoint durante desarrollo. Agregar en README.
- **[Risk] MP puede reenviar IPN con delay de minutos** → Mitigation: el frontend no espera solo al webhook; el polling verifica el estado en la API propia, que consulta el estado del pago directamente a MP si es necesario.
- **[Risk] Stock decrementado pero pago revertido por banco** → Mitigation: el servicio de pagos implementará `PATCH /pedidos/{id}/estado` con transición a CANCELADO restaurando el stock. La lógica de chargeback/refund automático está fuera del alcance de este sprint.
- **[Risk] `paymentStore` persiste entre sesiones si no se limpia** → Mitigation: `paymentStore` no tiene `persist`. Se resetea a `idle` al montar `CheckoutForm` (`useEffect` con `resetPayment()` on mount).

## Open Questions

- ¿El `WEBHOOK_SECRET` de MercadoPago está configurado en el sandbox o se genera al crear la preferencia? → Revisar en la cuenta MP de prueba antes de implementar la validación de firma.
- ¿Se requiere soporte para `forma_pago_codigo=EFECTIVO` / `TRANSFERENCIA` en Sprint 6, o solo MERCADOPAGO? → Por ahora solo MERCADOPAGO activa el flujo de pagos; las otras formas quedan en PENDIENTE manual.
