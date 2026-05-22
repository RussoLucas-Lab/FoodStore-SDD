## ADDED Requirements

### Requirement: AddressSelector — selector con CRUD inline de direcciones
El sistema SHALL renderizar un componente `AddressSelector` en `frontend/src/features/checkout/components/` que recibe `props: { selectedId: number | null, onSelect: (id: number) => void }` y muestra la lista de direcciones del usuario autenticado obtenida vía `useDirecciones()` (TanStack Query). Cada dirección SHALL renderizarse como una opción seleccionable (radio button) con su texto formateado y un badge "Principal" si `es_principal=true`.

#### Scenario: Lista con direcciones
- **WHEN** el usuario tiene N direcciones activas
- **THEN** el componente renderiza N opciones; la principal aparece primero con badge "Principal"

#### Scenario: Selección preseleccionada
- **WHEN** `selectedId` coincide con el id de una dirección existente
- **THEN** esa opción se muestra como seleccionada visualmente

#### Scenario: Cambio de selección
- **WHEN** el usuario hace click en otra opción
- **THEN** se invoca `onSelect(nuevoId)` con el id de la opción elegida

#### Scenario: Sin direcciones
- **WHEN** el usuario no tiene direcciones activas
- **THEN** se muestra un mensaje "Aún no tenés direcciones registradas" y el formulario inline de alta queda visible por defecto

#### Scenario: Estado de carga
- **WHEN** `useDirecciones().isLoading` es true
- **THEN** se muestran skeleton loaders en lugar de las opciones

### Requirement: AddressSelector — alta inline de dirección
El `AddressSelector` SHALL exponer un link/botón "+ Agregar dirección" que abre un mini-formulario inline (no modal) con campos `calle`, `numero`, `piso?`, `depto?`, `ciudad`, `provincia`, `codigo_postal`, `referencia?`. Al guardar SHALL llamar `useCreateDireccion()` (mutation) y al éxito SHALL: (a) invalidar `['direcciones']`, (b) cerrar el formulario, (c) auto-seleccionar la nueva dirección vía `onSelect(nuevoId)`.

#### Scenario: Alta exitosa
- **WHEN** el usuario completa el formulario válido y hace click en "Guardar"
- **THEN** se ejecuta `useCreateDireccion()`; al volver la respuesta, la lista se refresca, el form se cierra y `onSelect(nuevoId)` se invoca con el id de la dirección creada

#### Scenario: Validación inline
- **WHEN** el usuario intenta guardar con campos requeridos vacíos
- **THEN** los campos vacíos muestran mensaje de error y la mutación no se dispara

#### Scenario: Error de servidor
- **WHEN** la mutación falla con HTTP 4xx o 5xx
- **THEN** se muestra un toast con el `detail` del error y el formulario permanece abierto con los datos del usuario

#### Scenario: Cancelar alta
- **WHEN** el usuario hace click en "Cancelar" en el formulario inline
- **THEN** el formulario se cierra sin cambios y sin disparar mutación

### Requirement: AddressSelector — edición inline de dirección
El `AddressSelector` SHALL permitir editar una dirección existente vía un botón "Editar" por item que abre el mismo formulario inline pre-poblado. Al guardar SHALL llamar `useUpdateDireccion()` y al éxito SHALL invalidar `['direcciones']` y cerrar el formulario manteniendo la selección actual.

#### Scenario: Edición exitosa
- **WHEN** el usuario edita una dirección y guarda con datos válidos
- **THEN** se ejecuta la mutation, la lista se refresca y el formulario se cierra; la selección previa se mantiene

#### Scenario: Edición de dirección de otro usuario
- **WHEN** el backend responde HTTP 404 (caso teórico de race condition)
- **THEN** se muestra un toast "Dirección no encontrada" y la lista se refresca

### Requirement: AddressSelector — eliminar dirección
El `AddressSelector` SHALL permitir eliminar una dirección via botón "Eliminar" por item, mostrando un diálogo de confirmación previo. Al confirmar SHALL llamar `useDeleteDireccion()`. Si la dirección eliminada era la `selectedId`, SHALL invocar `onSelect(null)` o seleccionar automáticamente la principal restante.

#### Scenario: Eliminación de dirección no seleccionada
- **WHEN** el usuario elimina una dirección distinta a la seleccionada
- **THEN** se ejecuta el delete, la lista se refresca y `selectedId` no cambia

#### Scenario: Eliminación de la dirección seleccionada
- **WHEN** el usuario elimina la dirección que estaba seleccionada
- **THEN** tras el refetch, se invoca `onSelect` con el id de la dirección principal restante (si existe) o `null`

#### Scenario: Backend rechaza eliminar principal con otras activas
- **WHEN** el backend responde HTTP 400 con `code: "PRINCIPAL_CANNOT_DELETE"`
- **THEN** se muestra un toast con el `detail` y la dirección sigue en la lista

### Requirement: AddressSelector — promover a principal
El `AddressSelector` SHALL permitir promocionar una dirección no principal a principal via un botón "Hacer principal" por item, que llama `useSetPrincipal()`. Al éxito la lista se refresca y la nueva principal aparece con el badge.

#### Scenario: Promoción exitosa
- **WHEN** el usuario hace click en "Hacer principal" en una dirección con `es_principal=false`
- **THEN** se ejecuta la mutation; tras el refetch, esa dirección muestra el badge "Principal" y la anterior principal lo pierde

#### Scenario: Botón oculto en la principal
- **WHEN** una dirección ya es principal
- **THEN** el botón "Hacer principal" no se renderiza para ese item (solo se ve el badge)

### Requirement: Hooks TanStack Query para direcciones
El sistema SHALL exponer en `frontend/src/features/checkout/hooks/useDirecciones.ts` los hooks: `useDirecciones()` (useQuery con key `['direcciones']`), `useCreateDireccion()`, `useUpdateDireccion()`, `useSetPrincipal()` y `useDeleteDireccion()` (useMutation, todos con invalidación de `['direcciones']` en `onSuccess`).

#### Scenario: useDirecciones query key estable
- **WHEN** dos componentes consumen `useDirecciones()` en simultáneo
- **THEN** TanStack Query deduplica la request y ambos reciben los mismos datos

#### Scenario: Invalidación tras mutation
- **WHEN** cualquiera de las mutations resuelve con éxito
- **THEN** se invoca `queryClient.invalidateQueries({ queryKey: ['direcciones'] })` y los componentes que consumen el query refetchan
