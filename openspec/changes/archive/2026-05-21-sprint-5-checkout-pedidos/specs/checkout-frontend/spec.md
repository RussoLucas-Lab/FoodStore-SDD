## ADDED Requirements

### Requirement: CheckoutPage compone el flujo completo
El sistema SHALL renderizar la página `/checkout` (`frontend/src/pages/CheckoutPage.tsx`) como un layout que orquesta el `CheckoutForm` y las pantallas de confirmación. La página SHALL ser accesible solo para usuarios autenticados (ya gateada por `ProtectedRoute`). Si el carrito está vacío, SHALL redirigir o mostrar un estado vacío con CTA a `/catalogo`.

#### Scenario: Carrito con items
- **WHEN** un usuario autenticado navega a `/checkout` con al menos un item en `cartStore.items`
- **THEN** se renderiza `CheckoutForm` con resumen, dirección y forma de pago

#### Scenario: Carrito vacío
- **WHEN** un usuario autenticado navega a `/checkout` con `cartStore.items=[]`
- **THEN** se muestra un mensaje "Tu carrito está vacío" con un botón "Ir al catálogo" que navega a `/catalogo`

#### Scenario: Sin autenticación
- **WHEN** un usuario no autenticado navega a `/checkout`
- **THEN** `ProtectedRoute` redirige a `/login` (comportamiento heredado, sin cambios)

### Requirement: CheckoutForm orquesta dirección, forma de pago y submit
El sistema SHALL renderizar un componente `CheckoutForm` que contiene: (a) `OrderSummary` (lee del `cartStore`), (b) `AddressSelector` (estado local `selectedDireccionId`), (c) `PaymentMethodSelector` (estado local `selectedFormaPago`), (d) banner de validación pre-checkout, (e) botón "Confirmar pedido". El botón SHALL estar deshabilitado mientras `selectedDireccionId === null`, `selectedFormaPago === null`, el carrito esté vacío, o la validación pre-checkout esté pendiente.

#### Scenario: Estado inicial
- **WHEN** se renderiza `CheckoutForm` con carrito no vacío
- **THEN** el botón "Confirmar pedido" está deshabilitado

#### Scenario: Habilitación tras seleccionar dirección y forma de pago
- **WHEN** el usuario selecciona una dirección y una forma de pago
- **THEN** el botón "Confirmar pedido" queda habilitado (asumiendo carrito no vacío y validación OK)

#### Scenario: Submit dispara la mutation
- **WHEN** el usuario hace click en "Confirmar pedido" con todo válido
- **THEN** se invoca `useCrearPedido().mutate({ direccion_id, forma_pago_codigo, items })` donde `items` se construye desde `cartStore.items` mapeando `{ producto_id, cantidad, personalizacion }`

#### Scenario: Submit en estado pending
- **WHEN** la mutation está en `isPending`
- **THEN** el botón muestra spinner y queda deshabilitado para evitar doble click

### Requirement: OrderSummary lee del cartStore y muestra totales
El sistema SHALL renderizar un componente `OrderSummary` que lee `useCartStore(s => s.items)` y muestra: por cada renglón, nombre, cantidad, precio unitario, subtotal y lista de ingredientes excluidos si los hay. Al pie SHALL mostrar `totalPrice` calculado por `selectTotalPrice`. NO SHALL permitir editar cantidades (solo lectura — para editar el usuario vuelve al carrito).

#### Scenario: Renderizado de items
- **WHEN** el carrito tiene 2 renglones
- **THEN** `OrderSummary` muestra 2 filas con nombre, cantidad y subtotal cada una

#### Scenario: Ingredientes excluidos visibles
- **WHEN** un renglón tiene `ingredientesExcluidosNombres=["Cebolla", "Aceitunas"]`
- **THEN** debajo del nombre se muestra "Sin: Cebolla, Aceitunas"

#### Scenario: Total
- **WHEN** el carrito tiene items con totalPrice=530.50
- **THEN** al pie se muestra "$530,50" (formato local)

### Requirement: PaymentMethodSelector lista formas de pago habilitadas
El sistema SHALL renderizar un componente `PaymentMethodSelector` con `props: { selectedCodigo: string | null, onSelect: (codigo: string) => void }` que obtiene las formas de pago vía `useFormasPago()` (TanStack Query). Cada forma SHALL renderizarse como una opción radio con su `descripcion`. La forma seleccionada SHALL marcarse visualmente.

#### Scenario: Lista poblada
- **WHEN** el hook devuelve 3 formas habilitadas
- **THEN** se renderizan 3 opciones radio

#### Scenario: Selección
- **WHEN** el usuario hace click en una opción
- **THEN** se invoca `onSelect(codigo)` con el código de la forma elegida

#### Scenario: Estado de carga
- **WHEN** `useFormasPago().isLoading === true`
- **THEN** se muestran skeleton loaders en lugar de las opciones

#### Scenario: Error al cargar
- **WHEN** `useFormasPago().isError === true`
- **THEN** se muestra "No se pudieron cargar las formas de pago" con un botón "Reintentar" que invoca `refetch()`

### Requirement: Hooks TanStack Query — useFormasPago y useCrearPedido
El sistema SHALL exponer en `frontend/src/features/checkout/hooks/`:
- `useFormasPago()` (useQuery con key `['formas-pago']`, llama `GET /api/v1/formas-pago`)
- `useCrearPedido()` (useMutation que llama `POST /api/v1/pedidos` con body `{ direccion_id, forma_pago_codigo, items }`; envía header `Idempotency-Key` con UUID generado al inicio del flujo)

#### Scenario: useFormasPago query key estable
- **WHEN** dos componentes consumen `useFormasPago()` en simultáneo
- **THEN** TanStack Query deduplica la request

#### Scenario: useCrearPedido envía Idempotency-Key
- **WHEN** se dispara `useCrearPedido().mutate(body)`
- **THEN** la request HTTP incluye un header `Idempotency-Key` con un UUID v4 estable durante el ciclo de vida del componente `CheckoutForm`

#### Scenario: onSuccess limpia el carrito y navega
- **WHEN** la mutation resuelve con `data: PedidoRead`
- **THEN** se invoca `useCartStore.getState().clearCart()` y `navigate('/checkout/confirmado', { state: { pedido: data } })`

#### Scenario: onError mantiene el carrito
- **WHEN** la mutation falla con HTTP 4xx o 5xx
- **THEN** el `cartStore.items` permanece intacto y se muestra un toast con `error.detail`

### Requirement: Validación pre-checkout (US-069, US-070)
El `CheckoutForm` SHALL ejecutar al montar (y al cambiar `cartStore.items`) una validación: para cada `productoId` único del carrito, hacer `GET /api/v1/productos/{id}`; comparar `precio_base` actual vs. `precio` guardado en el `cartItem` y `disponible`/`stock_cantidad` vs. la cantidad pedida. Si hay discrepancias:
- Si algún producto vino con `disponible=false`, `deleted_at!=null` o `stock_cantidad < cantidad` → mostrar banner de error "Algunos productos ya no están disponibles" y deshabilitar el botón "Confirmar pedido".
- Si algún `precio_base` difiere → mostrar banner "Los precios cambiaron" con la diferencia y un botón "Actualizar precios y continuar" que llama a un callback que sincroniza el `cartStore` (actualiza el `precio` de las líneas afectadas).

#### Scenario: Todos los productos disponibles y al precio original
- **WHEN** la validación pre-checkout retorna OK para todos los items
- **THEN** no se muestra banner y el botón "Confirmar pedido" queda habilitado

#### Scenario: Un producto fuera de stock
- **WHEN** la validación detecta `stock_cantidad < cantidad` para algún producto
- **THEN** se muestra banner de error y el botón "Confirmar pedido" queda deshabilitado

#### Scenario: Cambio de precio
- **WHEN** la validación detecta que `precio_base` (actual) > `precio` (en carrito) para algún item
- **THEN** se muestra banner "Los precios cambiaron" con el botón "Actualizar precios y continuar"; al hacer click, el `cartStore` actualiza los precios y el banner desaparece, dejando el botón "Confirmar pedido" habilitado

#### Scenario: Producto eliminado
- **WHEN** la validación recibe HTTP 404 para algún `productoId`
- **THEN** se muestra banner de error y el botón "Confirmar pedido" queda deshabilitado

### Requirement: Pantalla de confirmación de pedido (US-071)
El sistema SHALL exponer una ruta `/checkout/confirmado` que renderiza un componente `PedidoConfirmacion`. La pantalla SHALL mostrar: ícono de éxito, número de pedido (`pedido.id`), total formateado, mensaje "Tu pedido fue creado correctamente" y dos CTAs: "Ver mis pedidos" (navega a `/pedidos`) y "Seguir comprando" (navega a `/catalogo`). El `pedido` SHALL leerse desde `location.state.pedido` (pasado por `navigate(..., { state })`).

#### Scenario: Pedido recibido por state
- **WHEN** el usuario llega a `/checkout/confirmado` con `location.state.pedido = { id: 42, total: 530.50, estado_codigo: "PENDIENTE", created_at: "..." }`
- **THEN** se muestra "Pedido #42", total formateado y los CTAs

#### Scenario: Refresh sin state
- **WHEN** el usuario refresca la página en `/checkout/confirmado` perdiendo `location.state`
- **THEN** se muestra un fallback "Tu pedido fue creado, podés verlo en Mis Pedidos" y el CTA "Ver mis pedidos"

#### Scenario: CTAs navegan correctamente
- **WHEN** el usuario hace click en "Ver mis pedidos"
- **THEN** navega a `/pedidos`

#### Scenario: Carrito ya vaciado
- **WHEN** el usuario llega a `/checkout/confirmado` tras una creación exitosa
- **THEN** `useCartStore(s => s.items)` devuelve `[]` (clearCart fue invocado en el `onSuccess` del hook)
