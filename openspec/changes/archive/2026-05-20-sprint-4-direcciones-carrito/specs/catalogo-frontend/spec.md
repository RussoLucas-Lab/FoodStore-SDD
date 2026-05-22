## MODIFIED Requirements

### Requirement: ProductoCard — tarjeta de producto
El sistema SHALL renderizar un componente `ProductoCard` por cada producto que muestre nombre, descripción truncada, precio formateado en ARS y badges de alérgenos. La card SHALL incluir un botón "Agregar al carrito" que abre el componente `AgregarAlCarritoModal` (definido en `carrito-frontend`) pasando el producto como input. El botón SHALL estar deshabilitado si `disponible=false`.

#### Scenario: Producto con alérgenos
- **WHEN** el producto tiene ingredientes con `es_alergeno=true`
- **THEN** la card muestra badges de alerta por cada alérgeno

#### Scenario: Producto no disponible
- **WHEN** el producto tiene `disponible=false`
- **THEN** la card muestra una indicación visual de "No disponible" y el botón de agregar al carrito está deshabilitado

#### Scenario: Click en "Agregar al carrito" abre el modal de personalización
- **WHEN** el usuario hace click en "Agregar al carrito" sobre un producto disponible
- **THEN** se abre `AgregarAlCarritoModal` con la lista de ingredientes del producto (obtenida vía `useProducto(id)`) y al confirmar se despacha `addItem` al `cartStore`

#### Scenario: Producto sin ingredientes
- **WHEN** el usuario hace click en "Agregar al carrito" sobre un producto disponible sin ingredientes
- **THEN** se abre `AgregarAlCarritoModal` con el mensaje "Este producto no tiene ingredientes personalizables" y solo permite ajustar la cantidad antes de confirmar
