## ADDED Requirements

### Requirement: PedidosList — historial paginado del cliente
La feature `pedidos` SHALL exponer un componente `PedidosList` accesible en la ruta `/pedidos` (protegida, rol CLIENT). SHALL mostrar los pedidos del usuario en lista paginada con: número de pedido (id), fecha de creación (`created_at`), total, estado con badge de color semántico (`PENDIENTE`=amarillo, `CONFIRMADO`=azul, `EN_PREP`=naranja, `EN_CAMINO`=violeta, `ENTREGADO`=verde, `CANCELADO`=rojo), y enlace al detalle. La lista SHALL usar `useQuery` de TanStack Query sobre `GET /api/v1/pedidos`. En estado de carga SHALL mostrar skeletons.

#### Scenario: Lista con pedidos
- **WHEN** un CLIENT navega a `/pedidos` y tiene pedidos
- **THEN** ve una lista paginada con id, fecha, total y badge de estado para cada pedido

#### Scenario: Lista vacía
- **WHEN** el CLIENT no tiene pedidos
- **THEN** ve un mensaje "No tenés pedidos aún" con un CTA para ir al catálogo

#### Scenario: Loading state
- **WHEN** la query está en estado `pending`
- **THEN** se muestran skeleton cards en lugar de los pedidos

#### Scenario: Error de red
- **WHEN** la query falla
- **THEN** se muestra un toast de error y la lista queda vacía

### Requirement: PedidoDetail — vista completa de un pedido
`PedidoDetail` SHALL ser accesible en `/pedidos/:id`. SHALL mostrar: información del pedido (id, fecha, estado, total, forma de pago, dirección de entrega desde `direccion_snapshot`), lista de items con `nombre_snapshot`, `precio_snapshot`, `cantidad` y personalizaciones, historial de estados (`HistorialTimeline`) y estado del pago (`PaymentStatus`). Usa `useQuery` sobre `GET /api/v1/pedidos/{id}`.

#### Scenario: Detalle con datos completos
- **WHEN** el CLIENT navega a `/pedidos/10`
- **THEN** ve la dirección, items con snapshots, el historial y el estado del pago

#### Scenario: Pedido no encontrado
- **WHEN** el `id` no pertenece al usuario o no existe
- **THEN** redirige a `/pedidos` con toast de error

#### Scenario: Botón cancelar visible en PENDIENTE
- **WHEN** el pedido está en estado PENDIENTE
- **THEN** aparece un botón "Cancelar pedido" que abre un modal de confirmación con input de motivo

#### Scenario: Botón cancelar oculto en otros estados
- **WHEN** el pedido está en CONFIRMADO, EN_PREP, EN_CAMINO, ENTREGADO o CANCELADO
- **THEN** NO aparece el botón de cancelación

### Requirement: HistorialTimeline — timeline visual de estados
`HistorialTimeline` SHALL renderizar el historial de estados como una línea de tiempo vertical. Cada nodo SHALL mostrar: estado destino, actor que realizó el cambio (`cambiado_por_id` si disponible), fecha y hora (`created_at`), y motivo (solo si no es null). El nodo actual SHALL estar visualmente destacado. Usa los datos de `historial` en `PedidoDetailRead`.

#### Scenario: Timeline con 4 estados
- **WHEN** el pedido hizo las transiciones PENDIENTE→CONFIRMADO→EN_PREP→EN_CAMINO
- **THEN** el timeline muestra 4 nodos ordenados cronológicamente, con el último (EN_CAMINO) destacado

#### Scenario: Nodo de cancelación con motivo
- **WHEN** uno de los nodos tiene estado CANCELADO y motivo no nulo
- **THEN** el nodo muestra el motivo bajo la fecha

#### Scenario: Estado inicial (creación)
- **WHEN** el pedido solo tiene el registro inicial (`estado_desde: null, estado_hasta: PENDIENTE`)
- **THEN** el timeline muestra un único nodo "Pedido creado — PENDIENTE"

### Requirement: PaymentStatus — estado del pago con polling
`PaymentStatus` SHALL renderizar el estado actual del pago (`PENDIENTE`, `EN_PROCESO`, `APROBADO`, `RECHAZADO`, `ERROR`) con un badge de color. Cuando el estado sea no-terminal (`PENDIENTE` o `EN_PROCESO`), SHALL hacer polling automático cada 30 segundos via `refetchInterval` de TanStack Query sobre `GET /api/v1/pagos/{pedido_id}`. Al llegar a un estado terminal, SHALL desactivar el polling. Si `pago` es null, muestra "Pago no iniciado".

#### Scenario: Polling activo en estado PENDIENTE
- **WHEN** el pago está en estado PENDIENTE
- **THEN** el componente refetch cada 30 s automáticamente

#### Scenario: Polling desactivado en APROBADO
- **WHEN** el pago llega a APROBADO
- **THEN** el polling se detiene y el badge muestra "Aprobado" en verde

#### Scenario: Estado RECHAZADO
- **WHEN** el pago está en RECHAZADO
- **THEN** el badge muestra "Rechazado" en rojo y no hay polling

#### Scenario: Sin pago iniciado
- **WHEN** `pago` es null en `PedidoDetailRead`
- **THEN** muestra "Pago no iniciado" sin badge de estado

### Requirement: Cancelación de pedido propio desde PedidoDetail
Cuando el pedido está en `PENDIENTE`, el cliente SHALL poder cancelarlo desde `PedidoDetail`. Al hacer clic en "Cancelar pedido", SHALL abrirse un modal que muestre las consecuencias y pida el motivo (campo de texto requerido). Al confirmar, SHALL llamar a `DELETE /api/v1/pedidos/{id}` con el motivo. En caso de éxito, SHALL invalidar la query del pedido (refetch) y mostrar toast de confirmación. En caso de error, SHALL mostrar el mensaje de error sin cerrar el modal.

#### Scenario: Flujo completo de cancelación
- **WHEN** el CLIENT hace clic en "Cancelar pedido", ingresa el motivo y confirma
- **THEN** se llama DELETE /pedidos/{id}, el estado del pedido cambia a CANCELADO y el timeline se actualiza

#### Scenario: Modal con motivo vacío
- **WHEN** el CLIENT intenta confirmar sin escribir el motivo
- **THEN** el input muestra error de validación y el botón de confirmar queda deshabilitado

#### Scenario: Invalidación de cache tras cancelar
- **WHEN** la cancelación es exitosa
- **THEN** TanStack Query invalida `['pedido', id]` y la vista se actualiza con el nuevo estado CANCELADO
