# Spec: gestion-pedidos-admin-frontend

## Overview
Cubre el panel de gestión de pedidos para operadores con rol ADMIN o PEDIDOS. Incluye la tabla global de pedidos con filtros y búsqueda, el avance manual de estado via FSM, la vista de detalle desde el panel admin, y el control de acceso por rol.

## Requirements

### Requirement: GestionPedidos — listado global para roles ADMIN/PEDIDOS
El panel admin SHALL exponer el componente `GestionPedidos` accesible en `/admin/pedidos` (protegida, roles ADMIN o PEDIDOS). SHALL mostrar todos los pedidos del sistema en una tabla paginada con columnas: id, cliente (`usuario_id` o nombre si está disponible), fecha, estado (badge), total y botón de acciones. Usa `useQuery` sobre `GET /api/v1/pedidos` (el backend filtra automáticamente por rol). Debe incluir filtro de estado via chips (uno por cada estado de la FSM) y búsqueda por id de pedido.

#### Scenario: ADMIN ve todos los pedidos
- **WHEN** un ADMIN navega a `/admin/pedidos`
- **THEN** ve la tabla con todos los pedidos del sistema, no filtrados por usuario

#### Scenario: PEDIDOS ve todos los pedidos
- **WHEN** un usuario con rol PEDIDOS navega a `/admin/pedidos`
- **THEN** ve la misma tabla que el ADMIN

#### Scenario: Filtro por estado
- **WHEN** el gestor hace clic en el chip "EN_PREP"
- **THEN** la tabla se filtra mostrando solo pedidos en estado EN_PREP

#### Scenario: Búsqueda por id
- **WHEN** el gestor escribe un número en el campo de búsqueda
- **THEN** la tabla filtra por pedidos cuyo id coincide

#### Scenario: Tabla vacía
- **WHEN** no hay pedidos que coincidan con los filtros activos
- **THEN** muestra mensaje "No hay pedidos con los filtros seleccionados"

### Requirement: Avance de estado FSM desde GestionPedidos
En cada fila de la tabla GestionPedidos, el botón de acciones SHALL mostrar el siguiente estado posible según la FSM para el rol del actor. Al hacer clic en "Avanzar estado", SHALL abrirse un modal de confirmación mostrando la transición `estado_actual → siguiente_estado`. Al confirmar, SHALL llamar `PATCH /api/v1/pedidos/{id}/estado` con el nuevo estado. En caso de éxito, SHALL refetch la tabla e invalidar el cache del pedido.

#### Scenario: Gestor avanza de CONFIRMADO a EN_PREP
- **WHEN** un usuario PEDIDOS hace clic en "Avanzar" en un pedido CONFIRMADO y confirma
- **THEN** se llama PATCH /pedidos/{id}/estado con `nuevo_estado="EN_PREP"`, la tabla se actualiza y el badge del pedido cambia

#### Scenario: Botón deshabilitado en estado terminal
- **WHEN** el pedido está en ENTREGADO o CANCELADO
- **THEN** no aparece el botón de avanzar (estados terminales)

#### Scenario: Error de transición
- **WHEN** la transición falla (ej: el backend devuelve 422)
- **THEN** el modal muestra el mensaje de error sin cerrar ni modificar la tabla

#### Scenario: Modal de confirmación muestra la transición
- **WHEN** el gestor hace clic en "Avanzar" sobre un pedido EN_PREP
- **THEN** el modal muestra "¿Confirmar transición: EN_PREP → EN_CAMINO?" con botones Cancelar y Confirmar

### Requirement: Detalle de pedido desde GestionPedidos
Al hacer clic en el id del pedido en la tabla, SHALL navegar a una vista de detalle del pedido (puede reutilizar `PedidoDetail`) con la misma información que ve el cliente más la posibilidad de avanzar estado FSM directamente desde ese detalle.

#### Scenario: Click en id de pedido
- **WHEN** el gestor hace clic en el id "42" en la tabla
- **THEN** navega a `/admin/pedidos/42` con el detalle completo del pedido

#### Scenario: Detalle con opción de avanzar estado
- **WHEN** el gestor está en el detalle de un pedido en EN_PREP
- **THEN** ve el botón "Avanzar a EN_CAMINO" que ejecuta el mismo PATCH

### Requirement: Acceso restringido a roles ADMIN y PEDIDOS
La ruta `/admin/pedidos` SHALL estar protegida por `ProtectedRoute` con `roles={["ADMIN", "PEDIDOS"]}`. Si un usuario con rol CLIENT intenta acceder, SHALL redirigir a `/` con toast de error de autorización.

#### Scenario: CLIENT intenta acceder
- **WHEN** un CLIENT navega a `/admin/pedidos`
- **THEN** es redirigido a `/` con un toast de error

#### Scenario: ADMIN accede correctamente
- **WHEN** un ADMIN navega a `/admin/pedidos`
- **THEN** puede ver y operar la tabla de gestión de pedidos
