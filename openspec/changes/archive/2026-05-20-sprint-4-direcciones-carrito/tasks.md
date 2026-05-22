## 1. Backend — Módulo `direcciones`

- [x] 1.1 Crear `backend/app/modules/direcciones/model.py` — clase `Direccion` (plain Python para repo in-memory) con campos `id`, `usuario_id`, `calle`, `numero`, `piso?`, `depto?`, `ciudad`, `provincia`, `codigo_postal`, `referencia?`, `es_principal: bool`, `deleted_at: datetime | None`
- [x] 1.2 Crear `backend/app/modules/direcciones/schemas.py` — `DireccionCreate`, `DireccionUpdate` (sin `es_principal`), `DireccionRead`, `DireccionSetPrincipalResponse` (Pydantic)
- [x] 1.3 Crear `backend/app/modules/direcciones/repository.py` — hereda `BaseRepository[Direccion]`; métodos: `list_by_usuario(user_id)` (excluye soft-deleted, ordena principal primero), `count_activas_by_usuario(user_id)`, `get_principal_by_usuario(user_id)`, `get_by_id_and_usuario(id, user_id)`
- [x] 1.4 Crear `backend/app/modules/direcciones/service.py` — métodos: `listar_propias(uow, user_id)`, `crear(uow, user_id, body)` (con RN-DI01: primera = principal automática), `actualizar(uow, user_id, id, body)` (ignora `es_principal` del body), `set_principal(uow, user_id, id)` (atómico: desmarca anterior + marca nueva), `eliminar(uow, user_id, id)` (con guard `PRINCIPAL_CANNOT_DELETE`)
- [x] 1.5 Crear `backend/app/modules/direcciones/router.py` — endpoints: `GET /direcciones`, `POST /direcciones`, `PUT /direcciones/{id}`, `PATCH /direcciones/{id}/principal`, `DELETE /direcciones/{id}`; todos requieren `get_current_user` como dependencia
- [x] 1.6 Registrar router de direcciones en `backend/app/main.py` con prefix `/api/v1`

## 2. Frontend — Tipos y API endpoints (direcciones)

- [x] 2.1 Crear `frontend/src/types/direcciones.ts` — tipos `DireccionRead`, `DireccionCreate`, `DireccionUpdate`
- [x] 2.2 Crear `frontend/src/api/endpoints/direcciones.ts` — funciones: `getDirecciones()`, `createDireccion(data)`, `updateDireccion(id, data)`, `setPrincipal(id)`, `deleteDireccion(id)`

## 3. Frontend — Store del carrito (cartStore)

- [x] 3.1 Crear `frontend/src/types/carrito.ts` — tipos `CartItem` (`lineId`, `productoId`, `nombre`, `precio`, `cantidad`, `ingredientesExcluidosIds: number[]`, `ingredientesExcluidosNombres: string[]`), `CartState`, `CartActions`
- [x] 3.2 Crear `frontend/src/store/cartStore.ts` — Zustand con middleware `persist` (key `food-store:cart:v1`); implementar acciones `addItem`, `removeItem`, `updateCantidad`, `clearCart`; función helper `buildLineId(productoId, excludedIds)` que ordena y serializa los ids para consolidación (RN-CR02); selectores `selectTotalItems`, `selectTotalPrice`
- [x] 3.3 Extender `frontend/src/store/uiStore.ts` — agregar slice `cartOpen: boolean` y action `toggleCart()` (crear el store si todavía no existe en el proyecto)
- [x] 3.4 Crear test unitario `frontend/src/store/cartStore.test.ts` — casos: addItem consolida mismo producto sin personalización, addItem mantiene separados mismo producto con distintas exclusiones, exclusiones en distinto orden = mismo lineId, updateCantidad a 0 elimina renglón, clearCart vacía, selectTotalItems y selectTotalPrice correctos

## 4. Frontend — Feature `carrito` (componentes)

- [x] 4.1 Crear `frontend/src/features/carrito/components/CartDrawer.tsx` — sidebar deslizable desde la derecha controlado por `useUiStore(s => s.cartOpen)`; renderiza lista de renglones, totales y botones "Vaciar" / "Ir a checkout"
- [x] 4.2 Crear `frontend/src/features/carrito/components/CartItemCard.tsx` — render de un renglón: nombre, precio, lista de exclusiones, botones `+` / `−` / "Eliminar", subtotal
- [x] 4.3 Crear `frontend/src/features/carrito/components/CartBadge.tsx` — ícono con badge superpuesto que muestra `selectTotalItems`; click invoca `toggleCart()`
- [x] 4.4 Exportar componentes desde `frontend/src/features/carrito/index.ts`
- [x] 4.5 Montar `<CartDrawer />` una sola vez en el layout raíz (`App.tsx` o equivalente)
- [x] 4.6 Integrar `<CartBadge />` en el `Navbar` (componente del layout-base)

## 5. Frontend — Extensión del catálogo (ProductoCard + Modal)

- [x] 5.1 Crear `frontend/src/features/catalogo/components/AgregarAlCarritoModal.tsx` — modal con header "Personalizá tu pedido", lista de checkboxes de ingredientes (obtenidos vía `useProducto(id)`), control de cantidad (`+`/`−`, mínimo 1), botones "Cancelar" / "Agregar al carrito"; implementar tope RN-CR04 (deshabilitar checkboxes cuando ya hay `n_ingredientes - 1` marcados)
- [x] 5.2 Modificar `frontend/src/features/catalogo/components/ProductoCard.tsx` — agregar botón "Agregar al carrito" (deshabilitado si `disponible=false`) que abre `AgregarAlCarritoModal` con el producto como input
- [x] 5.3 Confirmar que `useProducto(id)` (Sprint 3) devuelve los ingredientes en el shape esperado por el modal; ajustar si hace falta

## 6. Frontend — Hooks de direcciones (TanStack Query)

- [x] 6.1 Crear `frontend/src/features/checkout/hooks/useDirecciones.ts` — `useDirecciones()` con `useQuery({ queryKey: ['direcciones'], queryFn: getDirecciones })`
- [x] 6.2 En el mismo archivo, agregar: `useCreateDireccion()`, `useUpdateDireccion()`, `useSetPrincipal()`, `useDeleteDireccion()` — todos `useMutation` con `onSuccess` que invalida `['direcciones']` y muestra toast de éxito; en `onError` muestra toast con `detail` del backend

## 7. Frontend — Feature `checkout` (AddressSelector)

- [x] 7.1 Crear `frontend/src/features/checkout/components/AddressForm.tsx` — formulario inline reutilizable (alta y edición) usando TanStack Form con campos `calle`, `numero`, `piso?`, `depto?`, `ciudad`, `provincia`, `codigo_postal`, `referencia?`; validación inline de requeridos; recibe `initialValues?` y `onSubmit`
- [x] 7.2 Crear `frontend/src/features/checkout/components/AddressSelector.tsx` — recibe `props: { selectedId: number | null, onSelect: (id: number) => void }`; renderiza lista de direcciones (con badge "Principal" donde aplique), botones por item ("Editar", "Eliminar", "Hacer principal" si no es principal), link "+ Agregar dirección" que abre `AddressForm` inline en modo alta; al alta exitosa auto-selecciona la nueva
- [x] 7.3 Implementar manejo de errores: toast con `detail` del backend en cada mutation (especialmente `PRINCIPAL_CANNOT_DELETE`)
- [x] 7.4 Implementar lógica: al eliminar la dirección actualmente seleccionada, invocar `onSelect` con el id de la principal restante o `null`
- [x] 7.5 Exportar `AddressSelector` desde `frontend/src/features/checkout/index.ts`

## 8. Tests backend

- [x] 8.1 Crear `backend/tests/test_direcciones.py` — tests CRUD: listar propias (200, orden principal primero), listar sin auth (401), crear primera = principal auto, crear N-ésima sin promoción, validación campos requeridos (422), actualizar exitoso, actualizar ignora `es_principal` del body, actualizar dirección de otro (404), PATCH principal exitoso (desmarca anterior), PATCH idempotente, PATCH dirección de otro (404), DELETE no principal (204), DELETE única dirección (204), DELETE principal con otras activas (400 PRINCIPAL_CANNOT_DELETE), DELETE dirección de otro (404)
- [x] 8.2 Test de invariante "máximo una principal por usuario" tras una secuencia de operaciones (crear 3, PATCH principal sobre la segunda, verificar conteo)

## 9. Tests frontend

- [x] 9.1 Confirmar que el test del `cartStore` (tarea 3.4) cubre RN-CR01, RN-CR02, RN-CR03, RN-CR04 (este último vía test del modal o validación de la función helper)
- [x] 9.2 Crear `frontend/src/features/carrito/components/AgregarAlCarritoModal.test.tsx` — tests: modal con 4 ingredientes permite excluir hasta 3, el 4to checkbox queda deshabilitado al llegar al tope, modal sin ingredientes solo permite cantidad, confirmación llama `addItem` con args correctos

## 10. Documentación y cierre

- [x] 10.1 Confirmar que `docs/API_SPEC.md` ya documenta el módulo `direcciones` y los endpoints implementados (alinear si difiere)
- [x] 10.2 Confirmar que `docs/BUSINESS_RULES.md` ya cita RN-DI01, RN-DI02 y RN-CR01..04 (alinear si difiere)
- [x] 10.3 Verificación manual end-to-end: registrarse, abrir catálogo, agregar 2 productos con personalizaciones distintas, abrir drawer, modificar cantidad, recargar página y confirmar persistencia, abrir flujo donde se monte `AddressSelector` (página de prueba ad-hoc o ruta temporal `/test-address`), crear/editar/eliminar/promover direcciones, validar errores
