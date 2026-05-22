## ADDED Requirements

### Requirement: Botón "Ir a checkout" navega a /checkout y cierra el drawer
El `CartDrawer` SHALL implementar el handler del botón "Ir a checkout" de modo que, al hacer click, invoque `useNavigate()('/checkout')` y cierre el drawer (`useUiStore.getState().setCartOpen(false)` o equivalente). El botón SHALL seguir deshabilitado mientras `items.length === 0` (comportamiento ya definido en la requirement existente del CartDrawer).

#### Scenario: Click con items en el carrito
- **WHEN** el carrito tiene al menos un item y el usuario hace click en "Ir a checkout"
- **THEN** la app navega a `/checkout` y el `CartDrawer` se cierra

#### Scenario: Botón deshabilitado con carrito vacío
- **WHEN** el carrito está vacío
- **THEN** el botón "Ir a checkout" está deshabilitado y un click no produce navegación ni cambio de estado

#### Scenario: Usuario no autenticado
- **WHEN** un usuario sin sesión hace click en "Ir a checkout" con items en el carrito
- **THEN** la navegación a `/checkout` resulta en redirect a `/login` por `ProtectedRoute` (comportamiento heredado)

### Requirement: clearCart se invoca desde el flujo de confirmación de pedido
El `cartStore.clearCart()` SHALL ser invocable desde fuera del feature `carrito` para vaciar el carrito tras la confirmación exitosa de un pedido. El feature `checkout` SHALL llamarlo via `useCartStore.getState().clearCart()` en el `onSuccess` de `useCrearPedido()`.

#### Scenario: Tras crear un pedido exitosamente
- **WHEN** `POST /api/v1/pedidos` responde 201 y el `onSuccess` del hook se ejecuta
- **THEN** `useCartStore.getState().clearCart()` se invoca y `cartStore.items` queda en `[]`

#### Scenario: Persistencia tras clearCart
- **WHEN** `clearCart()` se invoca durante el flujo de confirmación
- **THEN** `localStorage` se actualiza al siguiente tick reflejando `items: []`

#### Scenario: Falla la creación del pedido
- **WHEN** `POST /api/v1/pedidos` falla con HTTP 4xx o 5xx
- **THEN** `clearCart()` NO se invoca y `cartStore.items` permanece intacto para permitir reintento
