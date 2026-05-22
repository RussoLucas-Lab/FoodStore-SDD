## ADDED Requirements

### Requirement: cartStore — Zustand persistido en localStorage (RN-CR01)
El sistema SHALL exponer un store Zustand `cartStore` en `frontend/src/store/cartStore.ts` que persista su slice `items` en `localStorage` con la key `food-store:cart:v1` usando el middleware `persist` de Zustand.

#### Scenario: Recarga de página preserva el carrito
- **WHEN** un usuario agrega 1 o más items y recarga la página (F5)
- **THEN** al volver a montar, `useCartStore(s => s.items)` devuelve los mismos items con la misma cantidad y personalizaciones

#### Scenario: Persistencia versionada
- **WHEN** se inspecciona `localStorage`
- **THEN** existe una entrada con key `food-store:cart:v1` cuyo valor incluye la lista `items` serializada

#### Scenario: Suscripción por slice
- **WHEN** un componente hace `useCartStore(s => s.items)`
- **THEN** solo re-renderiza cuando cambia `items`, no cuando cambian acciones u otros campos

### Requirement: addItem — alta con consolidación por personalización (RN-CR02)
El cartStore SHALL exponer `addItem(producto, cantidad, ingredientesExcluidosIds)` que agrega un item al carrito. Si ya existe un item con el mismo `productoId` y el mismo conjunto de `ingredientesExcluidosIds`, la acción SHALL sumar `cantidad` al item existente en lugar de crear uno nuevo. Si no existe coincidencia, SHALL crear un nuevo item.

#### Scenario: Mismo producto sin personalización agregado dos veces
- **WHEN** se llama `addItem(productoA, 1, [])` dos veces consecutivas
- **THEN** el carrito tiene un único item con `productoId=A`, `cantidad=2` y `ingredientesExcluidosIds=[]`

#### Scenario: Mismo producto con distintas personalizaciones
- **WHEN** se llama `addItem(productoA, 1, [])` y luego `addItem(productoA, 1, [3])`
- **THEN** el carrito tiene dos items distintos con `productoId=A`: uno sin exclusiones (cant=1) y otro con `ingredientesExcluidosIds=[3]` (cant=1)

#### Scenario: Mismo producto con exclusiones en distinto orden son el mismo item
- **WHEN** se llama `addItem(productoA, 1, [1, 2])` y luego `addItem(productoA, 1, [2, 1])`
- **THEN** el carrito tiene un único item con `productoId=A`, `cantidad=2` y exclusiones `[1, 2]` (set-equivalencia)

### Requirement: removeItem — eliminación de renglón completo
El cartStore SHALL exponer `removeItem(lineId)` que elimina del carrito el renglón identificado por su `lineId` independientemente de la cantidad.

#### Scenario: Eliminación de un renglón existente
- **WHEN** el carrito tiene 3 renglones y se llama `removeItem(lineId)` sobre uno de ellos
- **THEN** el carrito queda con 2 renglones y el renglón eliminado no figura

#### Scenario: removeItem sobre lineId inexistente
- **WHEN** se llama `removeItem("inexistente")`
- **THEN** el state no cambia y no se lanza error

### Requirement: updateCantidad — ajuste de cantidad de un renglón
El cartStore SHALL exponer `updateCantidad(lineId, cantidad)` que actualiza la cantidad de un renglón. Si `cantidad <= 0`, el renglón SHALL eliminarse del carrito. La cantidad SHALL ser entera y mayor o igual a 1 para mantener el renglón.

#### Scenario: Aumentar cantidad
- **WHEN** un renglón tiene `cantidad=2` y se llama `updateCantidad(lineId, 5)`
- **THEN** el renglón queda con `cantidad=5`

#### Scenario: Bajar a cero elimina el renglón
- **WHEN** se llama `updateCantidad(lineId, 0)` sobre un renglón existente
- **THEN** el renglón se elimina del carrito

#### Scenario: Negativo elimina el renglón
- **WHEN** se llama `updateCantidad(lineId, -3)` sobre un renglón existente
- **THEN** el renglón se elimina del carrito

### Requirement: clearCart — vaciado total
El cartStore SHALL exponer `clearCart()` que deja el array `items` vacío.

#### Scenario: Vaciado con items
- **WHEN** el carrito tiene N items y se llama `clearCart()`
- **THEN** `items` queda como `[]` y el `localStorage` se actualiza al siguiente tick

### Requirement: Selectores derivados — totalItems y totalPrice
El cartStore SHALL exponer selectores `selectTotalItems(state)` y `selectTotalPrice(state)` (o getters memoizados equivalentes) calculados desde `items` en cada lectura. `totalItems` SHALL ser la suma de `cantidad` de todos los renglones; `totalPrice` SHALL ser la suma de `precio * cantidad` por renglón.

#### Scenario: Total de items
- **WHEN** el carrito tiene renglones `[{cantidad:2}, {cantidad:3}]`
- **THEN** `selectTotalItems` devuelve 5

#### Scenario: Total de precios
- **WHEN** el carrito tiene renglones `[{precio:100, cantidad:2}, {precio:50, cantidad:1}]`
- **THEN** `selectTotalPrice` devuelve 250

#### Scenario: Carrito vacío
- **WHEN** el carrito no tiene items
- **THEN** `selectTotalItems` devuelve 0 y `selectTotalPrice` devuelve 0

### Requirement: AgregarAlCarritoModal — personalización antes de agregar (RN-CR03, RN-CR04)
El sistema SHALL renderizar un componente `AgregarAlCarritoModal` que muestre la lista de ingredientes del producto con checkboxes "Excluir". El usuario SHALL poder marcar como excluidos hasta `(total_ingredientes - 1)` ingredientes; el último ingrediente disponible NO puede ser excluido. Al confirmar, SHALL despachar `addItem(producto, cantidad, ingredientesExcluidosIds)`.

#### Scenario: Producto con N ingredientes
- **WHEN** se abre el modal sobre un producto con 4 ingredientes y el usuario excluye 2
- **THEN** al confirmar, se llama `addItem(producto, 1, [id1, id2])` y el modal se cierra

#### Scenario: Tope de exclusiones (RN-CR04)
- **WHEN** el producto tiene 3 ingredientes y el usuario ya marcó 2 como excluidos
- **THEN** el checkbox del tercer ingrediente está deshabilitado y muestra un tooltip "Tenés que mantener al menos un ingrediente"

#### Scenario: Producto sin ingredientes
- **WHEN** se abre el modal sobre un producto sin ingredientes asociados
- **THEN** el modal muestra "Este producto no tiene ingredientes personalizables" y solo permite ajustar cantidad

#### Scenario: Cantidad mínima 1
- **WHEN** el usuario intenta bajar la cantidad por debajo de 1 en el modal
- **THEN** el botón "−" queda deshabilitado en cantidad=1

### Requirement: CartDrawer — sidebar lateral con items y totales
El sistema SHALL renderizar un componente `CartDrawer` que se monta una vez en el layout raíz y se muestra/oculta según `useUiStore(s => s.cartOpen)`. El drawer SHALL listar todos los renglones del carrito con: imagen/nombre del producto, lista de ingredientes excluidos (si los hay), cantidad con botones `+` / `−`, subtotal por renglón, botón "Eliminar". Al pie SHALL mostrar el `totalPrice`, botón "Vaciar carrito" y botón "Ir a checkout" (deshabilitado si `items.length === 0`).

#### Scenario: Apertura del drawer
- **WHEN** el usuario hace click en el badge del carrito en el navbar
- **THEN** se llama `toggleCart()` en `uiStore` y el drawer entra desde el lateral derecho

#### Scenario: Drawer con items
- **WHEN** el drawer está abierto y el carrito tiene 2 renglones
- **THEN** se renderizan 2 cards de renglón con sus datos, totalPrice al pie y botón "Ir a checkout" habilitado

#### Scenario: Drawer vacío
- **WHEN** el carrito está vacío
- **THEN** el drawer muestra "Tu carrito está vacío" y el botón "Ir a checkout" está deshabilitado

#### Scenario: Modificación inline de cantidad
- **WHEN** el usuario hace click en `+` o `−` sobre un renglón
- **THEN** se llama `updateCantidad(lineId, nuevaCantidad)` y el subtotal del renglón y el `totalPrice` se actualizan en el render siguiente

#### Scenario: Eliminar un renglón
- **WHEN** el usuario hace click en "Eliminar" sobre un renglón
- **THEN** se llama `removeItem(lineId)` y el renglón desaparece de la lista

#### Scenario: Vaciar carrito con confirmación
- **WHEN** el usuario hace click en "Vaciar carrito" y confirma el diálogo
- **THEN** se llama `clearCart()` y el drawer pasa a estado vacío

### Requirement: Badge de cantidad en el Navbar
El sistema SHALL renderizar en el Navbar un ícono de carrito con un badge superpuesto que muestra `selectTotalItems(state)`. El badge SHALL ocultarse cuando `totalItems === 0`. Al hacer click en el ícono SHALL invocar `toggleCart()` del `uiStore`.

#### Scenario: Carrito vacío
- **WHEN** el cliente no tiene items en el carrito
- **THEN** el ícono se renderiza sin badge

#### Scenario: Carrito con items
- **WHEN** el carrito tiene 5 items en total (suma de cantidades)
- **THEN** el badge muestra "5"

#### Scenario: Click abre el drawer
- **WHEN** el usuario hace click en el ícono del navbar
- **THEN** se invoca `toggleCart()` y el `CartDrawer` se abre

#### Scenario: Actualización reactiva
- **WHEN** se agrega un item desde el catálogo
- **THEN** el badge del navbar se actualiza sin recargar la página
