## Why

El flujo de pedidos carece de integración de pago real y de la máquina de estados (FSM) que controla sus transiciones. Sin esto, los pedidos quedan bloqueados en PENDIENTE indefinidamente y no existe mecanismo para confirmar, avanzar ni cancelar órdenes de forma segura y auditable.

## What Changes

- **Nuevo módulo `pagos`** en backend: creación de preferencia MercadoPago con `idempotency_key`, recepción del webhook IPN y consulta de estado de pago por pedido.
- **FSM completa de pedidos** en backend: endpoint `PATCH /pedidos/{id}/estado`, clase `OrderStateMachine`, decremento/restauración atómica de stock y registro append-only en `HistorialEstadoPedido`.
- **Flujo de pago en frontend**: componente `CardPayment` con MercadoPago SDK React, integración de `paymentStore`, polling de estado cada 30 s y pantallas de éxito/error.

## Capabilities

### New Capabilities

- `pagos-backend`: Módulo backend de pagos MercadoPago — crear preferencia con idempotency_key (RN-MP01), procesar webhook IPN (topic=payment) para avanzar pedido a CONFIRMADO, consultar estado de pago por pedido_id.

### Modified Capabilities

- `pedidos-backend`: Agregar `PATCH /pedidos/{id}/estado` con validación FSM, `OrderStateMachine` con todas las transiciones permitidas, decremento atómico de stock al confirmar (RN-FS03), restauración al cancelar desde CONFIRMADO (RN-FS05), INSERT append-only en `HistorialEstadoPedido` (RN-FS07), motivo obligatorio al cancelar (RN-FS09/RN-FS10).
- `checkout-frontend`: Agregar componente `CardPayment` (MercadoPago SDK React), integrar `paymentStore` (idle/processing/approved/rejected/error), polling de estado de pago cada 30 s (US-072), pantalla de éxito y pantalla de error con opción de reintento.

## Impact

- **Backend**: nuevo módulo `app/modules/pagos/` (model, repository, schemas, service, router). Cambios en `app/modules/pedidos/service.py` (FSM, stock atómico). Nueva dependencia: SDK `mercadopago`.
- **Frontend**: nuevo componente `CardPayment` en `features/checkout/`. Actualización de `store/paymentStore.ts` y hooks de checkout. Nueva dependencia: `@mercadopago/sdk-react`.
- **Infraestructura**: endpoint público `POST /pagos/webhook` que MercadoPago llama vía HTTPS (requiere URL accesible en producción o ngrok en desarrollo).
- **Base de datos**: tabla `Pago` ya existe en el modelo (Sprint 0). Solo se activan los flujos de escritura.
