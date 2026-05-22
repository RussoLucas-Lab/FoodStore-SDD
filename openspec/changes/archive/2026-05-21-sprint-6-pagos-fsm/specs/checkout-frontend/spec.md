## ADDED Requirements

### Requirement: CardPayment — componente MercadoPago SDK React
El sistema SHALL renderizar un componente `CardPayment` en `frontend/src/features/checkout/components/CardPayment.tsx` que usa `@mercadopago/sdk-react` para mostrar el formulario de tarjeta tokenizado. El componente SHALL recibir `props: { preferenceId: string, pedidoId: number }`. Al inicializarse SHALL llamar `POST /api/v1/pagos/crear` con el `pedidoId` para obtener el `preferenceId` si no fue provisto, o usar el provisto directamente. El formulario de MP SHALL renderizarse dentro de la pantalla de checkout tras la confirmación del pedido.

#### Scenario: Renderizado con preferenceId
- **WHEN** se renderiza `CardPayment` con `preferenceId="xxx"` válido
- **THEN** el SDK de MercadoPago renderiza el formulario de pago (brick/checkout pro) dentro del componente

#### Scenario: Formulario no renderiza sin preferenceId
- **WHEN** `preferenceId` es null o vacío
- **THEN** se muestra un spinner o skeleton hasta que el `POST /api/v1/pagos/crear` devuelva el ID

#### Scenario: Error al crear preferencia
- **WHEN** `POST /api/v1/pagos/crear` falla con HTTP 4xx/5xx
- **THEN** se muestra un mensaje "No se pudo iniciar el pago. Intentá de nuevo." con botón "Reintentar"

### Requirement: paymentStore integrado con flujo de pago (US-072)
El sistema SHALL actualizar `paymentStore` a través de las siguientes transiciones de estado durante el flujo de pago:
- `idle` (estado inicial)
- `processing`: al confirmar el pedido exitosamente y navegar a la pantalla de pago
- `approved`: cuando el polling detecta `estado_pago="APROBADO"` en `GET /api/v1/pagos/{pedido_id}`
- `rejected`: cuando el polling detecta `estado_pago="RECHAZADO"`
- `error`: cuando el polling falla con un error de red o HTTP 5xx

El `paymentStore` SHALL NO persistir entre sesiones (sin `persist`). SHALL exponer `setProcessing()`, `setApproved()`, `setRejected()`, `setError()`, `reset()`.

#### Scenario: Transición idle → processing
- **WHEN** `useCrearPedido().onSuccess` se dispara
- **THEN** `paymentStore.status` cambia de `idle` a `processing`

#### Scenario: Transición processing → approved
- **WHEN** `usePaymentStatus(pedidoId)` obtiene `estado_pago="APROBADO"` del polling
- **THEN** `paymentStore.status` cambia a `approved` y el polling se detiene

#### Scenario: Reset al montar CheckoutForm
- **WHEN** se monta el componente `CheckoutForm`
- **THEN** se invoca `paymentStore.reset()` via `useEffect` con dependency array vacío, dejando el estado en `idle`

### Requirement: Polling de estado de pago cada 30 segundos (US-072)
El sistema SHALL implementar un hook `usePaymentStatus(pedidoId: number | null)` que, cuando `pedidoId` no es null y `paymentStore.status === 'processing'`, ejecuta `GET /api/v1/pagos/{pedido_id}` cada 30 segundos usando `setInterval` dentro de un `useEffect`. El polling SHALL detenerse cuando el status pase a `approved`, `rejected` o `error`, o cuando el componente se desmonte (cleanup del interval).

#### Scenario: Polling activo mientras processing
- **WHEN** `paymentStore.status === 'processing'` y `pedidoId=42`
- **THEN** el hook hace una llamada a `GET /api/v1/pagos/42` inmediatamente y luego cada 30 segundos

#### Scenario: Polling se detiene al aprobar
- **WHEN** el polling detecta `estado_pago="APROBADO"`
- **THEN** el `setInterval` es limpiado y no se hacen más llamadas

#### Scenario: Cleanup al desmontar
- **WHEN** el componente que usa `usePaymentStatus` se desmonta mientras el polling está activo
- **THEN** el `useEffect` cleanup invoca `clearInterval` y no hay memory leaks

#### Scenario: No inicia polling si pedidoId es null
- **WHEN** `usePaymentStatus(null)` se invoca
- **THEN** no se hace ninguna llamada HTTP

### Requirement: Pantalla de éxito de pago
El sistema SHALL renderizar una pantalla de éxito en `/checkout/pago-exitoso` cuando `paymentStore.status === 'approved'`. La pantalla SHALL mostrar: ícono de check verde, "¡Tu pago fue aprobado!", número de pedido, total formateado y dos CTAs: "Ver mi pedido" (navega a `/pedidos/{id}`) y "Seguir comprando" (navega a `/catalogo`). Al montar la pantalla SHALL invocar `useCartStore.getState().clearCart()` si el carrito no fue vaciado previamente.

#### Scenario: Pantalla de éxito con datos
- **WHEN** el usuario llega a `/checkout/pago-exitoso` con `paymentStore.status === 'approved'` y `pedidoId=42`
- **THEN** se muestra "¡Tu pago fue aprobado!", "Pedido #42" y los CTAs

#### Scenario: CTA "Ver mi pedido" navega correctamente
- **WHEN** el usuario hace click en "Ver mi pedido"
- **THEN** navega a `/pedidos/42`

#### Scenario: Acceso directo sin estado approved
- **WHEN** un usuario navega directamente a `/checkout/pago-exitoso` sin `paymentStore.status === 'approved'`
- **THEN** redirige a `/checkout` o muestra "No hay pago aprobado" con CTA a `/pedidos`

### Requirement: Pantalla de pago rechazado con opción de reintento
El sistema SHALL renderizar una pantalla de error de pago cuando `paymentStore.status === 'rejected' | 'error'`. La pantalla SHALL mostrar: ícono de error rojo, "Tu pago no pudo procesarse", descripción del problema y dos CTAs: "Intentar de nuevo" (resetea `paymentStore` a `idle` y navega a `/checkout`) y "Cancelar pedido" (invoca `DELETE /api/v1/pedidos/{id}` para cancelar).

#### Scenario: Pantalla de rechazo con CTA reintentar
- **WHEN** `paymentStore.status === 'rejected'`
- **THEN** se muestra el mensaje de error y el botón "Intentar de nuevo"

#### Scenario: Reintento resetea el store y vuelve a checkout
- **WHEN** el usuario hace click en "Intentar de nuevo"
- **THEN** `paymentStore.reset()` se invoca y se navega a `/checkout` con el carrito intacto

#### Scenario: Cancelar pedido desde pantalla de error
- **WHEN** el usuario hace click en "Cancelar pedido"
- **THEN** se invoca `DELETE /api/v1/pedidos/{id}` (o `PATCH .../estado` con CANCELADO + motivo "Pago rechazado por el usuario"), el carrito se vacía y se navega a `/catalogo`
