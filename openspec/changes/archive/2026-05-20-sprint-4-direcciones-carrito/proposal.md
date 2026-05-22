## Why

Con el catálogo público operativo (Sprint 3) y el perfil del cliente funcional, el siguiente paso obligado es habilitar la compra: el cliente necesita gestionar direcciones de entrega y un carrito con personalización de productos. Sin estas dos piezas, los Sprints 5 (Pedidos) y 6 (Pagos/MercadoPago) no tienen punto de entrada — el checkout exige una dirección seleccionada y un carrito con items concretos.

## What Changes

- **Nuevo módulo `direcciones`** en el backend: CRUD completo de direcciones del cliente autenticado con soft delete y gestión de dirección principal única por usuario.
- **Nueva feature `carrito`** en el frontend: store Zustand persistido en localStorage con personalización de items (exclusión de ingredientes), drawer lateral y badge de cantidad en el navbar.
- **Nueva feature `checkout` (parcial)** en el frontend: componente `AddressSelector` con CRUD inline de direcciones reutilizable desde el flujo de checkout futuro.
- **Extensión de `ProductoCard`** (catálogo): botón "Agregar al carrito" que abre modal de personalización con la lista de ingredientes del producto.
- **Extensión del `Navbar`**: badge con la cantidad total de items del carrito y botón para abrir el `CartDrawer`.

## Capabilities

### New Capabilities
- `direcciones-backend`: CRUD de direcciones del cliente autenticado — listar propias, crear (con regla "primera = principal automática"), actualizar, cambiar dirección principal (solo una por usuario), soft delete.
- `carrito-frontend`: Store Zustand del carrito persistido en localStorage con soporte de personalización por exclusión de ingredientes, drawer lateral con items/totales y badge de cantidad en el navbar.
- `checkout-frontend`: Componente `AddressSelector` con CRUD inline de direcciones reutilizable desde checkout — selección de dirección de entrega, alta/edición rápida de direcciones desde el mismo flujo.

### Modified Capabilities
- `catalogo-frontend`: `ProductoCard` agrega un botón "Agregar al carrito" que abre un modal de personalización (`AgregarAlCarritoModal`) con la lista de ingredientes del producto y permite excluirlos antes de despachar la acción al `cartStore`. Extensión de comportamiento sin breaking changes en la grilla, los filtros ni los hooks existentes.

## Impact

- **Backend**: nuevo módulo `backend/app/modules/direcciones/` (model, schemas, repository, service, router). Registro en `main.py`. Sin cambios en módulos previos.
- **Frontend**:
  - Nueva feature `frontend/src/features/carrito/` (components, hooks).
  - Nueva feature `frontend/src/features/checkout/` (components: `AddressSelector`, hooks de direcciones).
  - Nuevo store `frontend/src/store/cartStore.ts` (Zustand con `persist` middleware).
  - Nuevo tipo `frontend/src/types/direcciones.ts` y endpoints `frontend/src/api/endpoints/direcciones.ts`.
  - Extensión de `frontend/src/features/catalogo/components/ProductoCard.tsx` y del componente `Navbar` para integrar carrito.
- **Dependencias frontend**: ya están instaladas `zustand` (Sprint 0) y `@tanstack/react-query` (Sprint 0). No se agregan dependencias nuevas.
- **Dependencias backend**: ninguna nueva — reutiliza FastAPI, repositorios in-memory existentes y el guard `get_current_user`.
- **Snapshot pattern**: la dirección de entrega no se snapshotea aún (se hace en Sprint 5 al crear el pedido); este sprint solo provee el CRUD y el selector.
- **Sin breaking changes** en módulos anteriores (auth, usuarios, categorias, ingredientes, productos, catalogo, perfil).
