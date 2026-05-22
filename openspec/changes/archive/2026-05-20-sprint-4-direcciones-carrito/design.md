## Context

Sprint 3 dejó el catálogo público y el perfil del cliente operativos. La `ProductoCard` ya muestra un placeholder de "agregar al carrito" deshabilitado, pero el carrito como tal no existe ni hay forma de gestionar direcciones del cliente. Este sprint completa esos dos huecos para habilitar el flujo de checkout que vendrá en Sprint 5 (Pedidos) y Sprint 6 (Pagos / MercadoPago).

El backend del proyecto usa **repositorios in-memory** (no PostgreSQL real ni SQLAlchemy) — los "modelos" son clases Python planas, no SQLModel tables. Alembic existe en el repo pero no se ejecuta en este sprint. El patrón Router → Service → UoW → Repository sigue vigente, con un UoW in-memory ligero ya definido en `app/core/uow.py`.

El frontend ya tiene Zustand (`authStore`) y TanStack Query operativos. El `cartStore` será el segundo store del proyecto y el primero que use el middleware `persist` para sobrevivir a recargas (RN-CR01).

Stakeholders directos del sprint: cliente final (gestiona direcciones y arma carrito) y el equipo de desarrollo (necesita el `AddressSelector` y el `cartStore` para construir checkout y pedidos en sprints siguientes).

## Goals / Non-Goals

**Goals:**
- CRUD completo de direcciones del cliente autenticado con soft delete y dirección principal única por usuario (RN-DI01, RN-DI02).
- `cartStore` Zustand persistido en localStorage (RN-CR01) con `addItem`, `removeItem`, `updateCantidad`, `clearCart`.
- Personalización de items vía exclusión de ingredientes con tope = (n_ingredientes − 1) (RN-CR03, RN-CR04).
- Mismo producto puede convivir en el carrito con distintas personalizaciones (RN-CR02).
- `CartDrawer` lateral con lista de items, totales y botón "Vaciar carrito".
- Badge de cantidad total en el navbar, sincronizado con el store.
- `AddressSelector` reutilizable con CRUD inline de direcciones (alta rápida + edición + selección).
- Extensión de `ProductoCard` para abrir un modal de personalización antes de despachar `addItem`.

**Non-Goals:**
- Checkout completo, creación de pedido o reserva de stock (Sprint 5).
- Snapshot de dirección al confirmar el pedido (Sprint 5 — patrón `direccion_snapshot` en `Pedido`).
- Integración de pagos / MercadoPago / tokenización PCI-compliant (Sprint 6).
- Cupones, descuentos, envío calculado o impuestos.
- Geolocalización o validación de cobertura por zona de entrega.
- Sincronización del carrito entre dispositivos (queda en local únicamente).

## Decisions

### D1 — Modelo `Direccion` con FK a `Usuario` y flag `es_principal`

`Direccion` vive en su propio módulo con campos: `id`, `usuario_id`, `calle`, `numero`, `piso` (opcional), `depto` (opcional), `ciudad`, `provincia`, `codigo_postal`, `referencia` (opcional), `es_principal: bool`, `deleted_at`. La aplicación garantiza la invariante "máximo una principal por usuario" en el `service`, no a nivel de constraint de BD (los repos son in-memory y el proyecto no usa índices parciales SQL).

**Alternativa descartada**: campo `principal_direccion_id` en `Usuario`. Se descarta porque obliga a modificar `Usuario` desde un módulo externo y rompe la simetría con el resto del CRUD por entidad. El flag en `Direccion` mantiene cohesión del módulo.

### D2 — `PATCH /direcciones/{id}/principal` desmarca la anterior en el mismo Service

El service de direcciones expone `set_principal(uow, user_id, direccion_id)` que en una sola transacción del UoW: (a) carga todas las direcciones del usuario, (b) marca `es_principal=false` en la actual principal, (c) marca `es_principal=true` en la nueva. Si la nueva ya era principal, el endpoint es idempotente y responde 200 sin cambios.

**Alternativa descartada**: dos endpoints separados (DELETE principal + POST principal). Se descarta por requerir doble round-trip y porque RN-DI02 expresa el cambio como una operación atómica.

### D3 — Primera dirección creada se marca principal automáticamente en el Service (RN-DI01)

`crear(uow, user_id, body)` consulta `count_by_usuario(user_id)`; si es 0, fuerza `es_principal=true` en el create ignorando el valor del body. Si es > 0, respeta el valor del body por defecto en `false` (el cliente puede luego usar el PATCH para promocionarla).

### D4 — Soft delete con regla: no se puede borrar la principal si hay otras

`delete(uow, user_id, direccion_id)` valida: si `es_principal=true` y existen otras direcciones activas del usuario, responde 400 `{ "code": "PRINCIPAL_CANNOT_DELETE", "detail": "Promocioná otra dirección como principal antes de eliminar esta" }`. Si es la única dirección activa, el delete procede (el usuario queda sin direcciones, lo que es válido para clientes nuevos sin compras).

**Alternativa descartada**: auto-promocionar otra dirección al borrar la principal. Descartada porque puede confundir al cliente: la nueva principal sería arbitraria. Mejor pedir acción explícita.

### D5 — `CartItem` se identifica por composite key `(productoId, ingredientesExcluidosIdsSorted)`

Para cumplir RN-CR02 ("mismo producto puede estar varias veces si tiene personalizaciones distintas"), el `cartStore` no usa `productoId` como clave única. Genera un `lineId` determinista al hacer `addItem`: `lineId = ${productoId}::${[...ingredientesExcluidosIds].sort().join(",")}`. Esto garantiza que dos items con la misma personalización se agreguen como un único renglón (sumando cantidad) y dos personalizaciones distintas conviven como renglones separados.

**Alternativa descartada**: `lineId = crypto.randomUUID()`. Descartada porque entonces agregar dos veces el mismo producto con la misma personalización generaría dos renglones, contradiciendo la UX esperada.

### D6 — `cartStore` con `persist` middleware de Zustand, key `food-store:cart:v1`

```ts
persist(
  (set, get) => ({ items: [], addItem, removeItem, updateCantidad, clearCart, ... }),
  { name: "food-store:cart:v1", storage: createJSONStorage(() => localStorage) }
)
```

El sufijo `:v1` permite invalidar el carrito persistido si el shape cambia en sprints futuros (e.g., cuando se snapshot precio en Sprint 5). Solo se persiste `items`; los selectores derivados (`totalItems`, `totalPrice`) se recomputan en cada render.

**Alternativa descartada**: persistir todo el state. Descartada para evitar serializar funciones o estado de UI.

### D7 — Modal de personalización separado de la `ProductoCard`

`ProductoCard` ya está en `features/catalogo/`. El nuevo componente `AgregarAlCarritoModal` también vive en `features/catalogo/components/` (no en `features/carrito/`) porque su input es un producto del catálogo y su ciclo de vida es disparado desde la card. El modal usa el hook `useProducto(id)` para traer los ingredientes (ya implementado en Sprint 3) y llama a `useCartStore(s => s.addItem)` para despachar la acción.

Esto NO viola la regla de "no cross-imports entre features": `features/catalogo/` importa del `store/` (capa transversal), no de `features/carrito/`. Esa regla aplica a `features/* → features/*`, no a `features/* → store/*`.

**Alternativa descartada**: poner el modal en `features/carrito/`. Descartada porque su input y disparo son del catálogo, no del carrito.

### D8 — `CartDrawer` controlado por `uiStore`, no por estado local del navbar

Para evitar prop-drilling y mantener el drawer abrible desde múltiples puntos (badge del navbar, "Ver carrito" en un futuro mini-cart de checkout), se agrega `cartOpen: boolean` + `toggleCart()` al `uiStore` existente. El `CartDrawer` se monta una sola vez en el layout raíz y se muestra/oculta según `useUiStore(s => s.cartOpen)`.

`uiStore` ya está mencionado en CLAUDE.md como uno de los 4 stores del proyecto. Este sprint inicializa su shape mínimo (`cartOpen` + `toggleCart`).

### D9 — `AddressSelector` con CRUD inline y modo controlado

`AddressSelector` recibe `selectedId: number | null` + `onSelect(id: number)` y muestra: (a) lista de direcciones del usuario con radio button, (b) badge "Principal" en la principal, (c) botones "Editar" / "Eliminar" por item, (d) link "+ Agregar dirección" que abre un mini-form inline (no modal) para alta rápida.

El componente vive en `features/checkout/components/` aunque checkout completo no se implementa en este sprint. Esto es deliberado: el `AddressSelector` es el "primer ladrillo" de checkout, y dejarlo en `features/direcciones/` requeriría crear una feature dedicada solo para una vista que solo se usa desde checkout. Por SRP del slice, vive donde se consume.

**Alternativa descartada**: crear `features/direcciones/`. Descartada porque la única superficie UI de direcciones en este sprint es el selector en checkout. Si en el futuro se agrega una página "Mis direcciones" standalone, se promueve a feature propia.

### D10 — Hooks TanStack Query para direcciones, no Zustand

Las direcciones son **estado del servidor** (vienen del backend, se modifican vía mutaciones). Cumplen el patrón documentado en CLAUDE.md "TanStack Query = estado del servidor". Por lo tanto:

- `useDirecciones()` — `useQuery(['direcciones'])`
- `useCreateDireccion()`, `useUpdateDireccion()`, `useSetPrincipal()`, `useDeleteDireccion()` — `useMutation` con invalidación de `['direcciones']` en `onSuccess`.

No hay `direccionesStore` Zustand.

## Risks / Trade-offs

- **[Riesgo] Carrito persistido con productos eliminados** → Si el ADMIN elimina (soft delete) un producto que algún cliente tiene en su carrito local, al abrir el drawer se mostrarían items "huérfanos". **Mitigación**: en Sprint 5 (checkout), validar la lista de items contra el backend antes de crear el pedido y mostrar un toast removiendo items inválidos. Para este sprint, los items huérfanos solo afectan la UI del drawer; al pasar a checkout futuro se filtran.

- **[Riesgo] Carrito persistido con precios desactualizados** → El precio guardado en `localStorage` puede diferir del precio actual del producto. **Mitigación**: el snapshot de precio se hace en el backend al crear el pedido (Sprint 5), por lo que el cliente verá el precio correcto en el resumen del checkout. En el drawer mostramos el precio guardado y advertimos en el checkout si difiere.

- **[Riesgo] Invariante de "una principal por usuario" violable por race condition** → Dos PATCH `/principal` concurrentes podrían dejar dos principales. **Mitigación**: con repositorios in-memory y un único proceso del backend de desarrollo, el riesgo es bajo. Cuando se migre a PostgreSQL real (fuera del scope del TPI), se agregará un índice parcial único `WHERE es_principal AND deleted_at IS NULL AND usuario_id = ?`.

- **[Trade-off] `AddressSelector` en `features/checkout/`** → Si en el futuro se necesita una página "Mis direcciones" independiente del checkout, habrá que mover/duplicar componentes. Aceptado para Sprint 4: evita crear una feature huérfana de una sola vista.

- **[Trade-off] `lineId` derivado vs. UUID aleatorio** → El lineId derivado no permite tener dos renglones idénticos manualmente separados (caso de uso: "quiero 2 pizzas iguales pero comprarlas en distintos momentos visuales"). Aceptado: el caso de uso normal es sumar cantidades, no duplicar renglones.

- **[Trade-off] Borrar dirección principal requiere acción explícita del usuario** → Más fricción que el auto-promote. Aceptado por claridad: el cliente decide qué dirección queda como principal.
