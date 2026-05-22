# BUSINESS_RULES.md — Food Store

## Dominio: Autenticación y Seguridad

| ID | Regla |
|---|---|
| RN-AU01 | La contraseña **NUNCA** se almacena en texto plano. Hashear con bcrypt (cost ≥ 12) con salt automático. |
| RN-AU02 | Access token JWT: duración 30 min, contiene `userId`, `email` y `roles`, firmado con HS256. |
| RN-AU03 | Refresh token: duración 7 días, UUID v4 opaco almacenado en BD (hash SHA-256). |
| RN-AU04 | Al usar un refresh token se aplica **rotación**: el anterior se revoca y se emite uno nuevo. |
| RN-AU05 | Si se detecta reuso de un refresh token ya utilizado (replay attack), se revocan **TODOS** los tokens del usuario. |
| RN-AU06 | Rate limiting en login: máximo 5 intentos por IP en 15 minutos → HTTP 429. |
| RN-AU07 | Al registrarse se asigna automáticamente el rol `CLIENT`. El rol **no viene del request**. |
| RN-AU08 | La respuesta de login **NO diferencia** "email no existe" de "contraseña incorrecta". |
| RN-AU09 | Datos sensibles de tarjetas **NUNCA pasan por el servidor** de Food Store (PCI DSS SAQ-A). |
| RN-AU10 | El archivo `.env` con secrets **NUNCA** se commitea al repositorio. |

---

## Dominio: Autorización y Roles (RBAC)

| ID | Regla |
|---|---|
| RN-RB01 | Existen 4 roles fijos con IDs estables: `ADMIN`, `STOCK`, `PEDIDOS`, `CLIENT`. |
| RN-RB02 | Un usuario puede tener **múltiples roles** simultáneamente (M:M con UNIQUE compuesta). |
| RN-RB03 | Solo `ADMIN` puede asignar/modificar roles de otros usuarios. |
| RN-RB04 | Un ADMIN no puede quitarse el rol ADMIN a sí mismo si es el **último administrador** del sistema. |
| RN-RB05 | Un `CLIENT` solo puede ver y operar sobre sus **propios datos**. Nunca los de otros usuarios. |
| RN-RB06 | `STOCK` no tiene acceso a pedidos, usuarios ni métricas. |
| RN-RB07 | `PEDIDOS` no tiene acceso a catálogo ni gestión de usuarios. |
| RN-RB08 | Solo `ADMIN` puede cancelar pedidos en estado `EN_PREP`. |
| RN-RB09 | Rol insuficiente → HTTP 403 Forbidden. |
| RN-RB10 | Sin token válido → HTTP 401. Rutas públicas (catálogo, login, registro) no requieren auth. |

---

## Dominio: Catálogo de Productos

| ID | Regla |
|---|---|
| RN-CA01 | Las categorías soportan jerarquía de profundidad arbitraria mediante FK autoreferencial (`parent_id`). |
| RN-CA02 | No se permite asignar una categoría como padre de sí misma ni generar ciclos. |
| RN-CA03 | No se puede eliminar una categoría que tenga **productos activos** asociados. |
| RN-CA04 | El precio se almacena como `DECIMAL(10,2)`. **Nunca `float` o `double`.** |
| RN-CA05 | El stock es un entero `≥ 0`. Nunca puede ser negativo. |
| RN-CA06 | Un producto puede pertenecer a **múltiples categorías** (M:M). |
| RN-CA07 | Un producto puede tener múltiples ingredientes (M:M). Cada ingrediente tiene flag `es_alergeno`. |
| RN-CA08 | El catálogo público muestra solo productos con `disponible=true AND deleted_at IS NULL`. |
| RN-CA09 | Soft delete: marca `deleted_at`. **Nunca `DELETE` físico** (preserva integridad referencial). |
| RN-CA10 | Los endpoints de admin pueden incluir `incluir_eliminados=true` para ver registros borrados. |

---

## Dominio: Direcciones de Entrega

| ID | Regla |
|---|---|
| RN-DI01 | Un cliente puede tener múltiples direcciones. La **primera** se marca como principal automáticamente. |
| RN-DI02 | **Solo una** dirección puede ser principal a la vez por usuario. |
| RN-DI03 | Un cliente solo puede ver/editar/eliminar **sus propias** direcciones (ownership por `userId` del JWT). |

---

## Dominio: Carrito de Compras

| ID | Regla |
|---|---|
| RN-CR01 | El carrito es **client-side only** (Zustand + localStorage). No existe en el backend. |
| RN-CR02 | El carrito persiste al cerrar el navegador, refresh de página y logout/login. |
| RN-CR03 | Si un producto ya está en el carrito y se agrega de nuevo, se **incrementa la cantidad** (no se duplica). |
| RN-CR04 | Solo se pueden excluir ingredientes que el producto **efectivamente tiene** asociados. |
| RN-CR05 | La personalización (exclusión de ingredientes) se almacena como array de IDs de ingredientes. |

---

## Dominio: Pedidos — Creación

| ID | Regla |
|---|---|
| RN-PE01 | La creación de un pedido es **ATÓMICA** (Unit of Work): si falla cualquier parte, no se persiste nada. |
| RN-PE02 | Al crear un pedido se genera **snapshot del precio** de cada producto (`precio_snapshot` en `DetallePedido`). |
| RN-PE03 | Al crear un pedido se genera **snapshot de la dirección** (`direccion_snapshot` en `Pedido`). |
| RN-PE04 | Se debe validar stock suficiente **DENTRO de la transacción** (`SELECT FOR UPDATE`) antes de crear. |
| RN-PE05 | Si algún producto no tiene stock suficiente, no se crea **ningún** ítem del pedido (todo o nada). |
| RN-PE06 | Todo pedido nace en estado `PENDIENTE` con registro inicial en `HistorialEstadoPedido`. |
| RN-PE07 | La personalización se almacena como `INTEGER[]` (array PostgreSQL) en `DetallePedido`. |
| RN-PE08 | Total del pedido = suma de subtotales (`cantidad × precio_snapshot`) + `costo_envio`. |

---

## Dominio: Pedidos — Máquina de Estados (FSM)

### Mapa de Transiciones

```
PENDIENTE   → CONFIRMADO   (solo automático: webhook IPN aprobado)
PENDIENTE   → CANCELADO    (Cliente / Gestor / Admin)
CONFIRMADO  → EN_PREP      (Gestor de Pedidos / Admin)
CONFIRMADO  → CANCELADO    (Gestor / Admin)
EN_PREP     → EN_CAMINO    (Gestor de Pedidos / Admin)
EN_PREP     → CANCELADO    (solo Admin)
EN_CAMINO   → ENTREGADO    (Gestor de Pedidos / Admin)

ENTREGADO   → (ninguna)    ← estado terminal
CANCELADO   → (ninguna)    ← estado terminal
```

### Reglas de la FSM

| ID | Regla |
|---|---|
| RN-FS01 | Un pedido **solo puede avanzar** al siguiente estado en la secuencia. No se permiten saltos ni retrocesos. |
| RN-FS02 | `PENDIENTE → CONFIRMADO` es **exclusivamente automática** (pago aprobado). Nadie la ejecuta manualmente. |
| RN-FS03 | Al confirmar (`PENDIENTE → CONFIRMADO`), se **decrementa atómicamente** el stock de cada producto. |
| RN-FS04 | Si el decremento de stock falla para cualquier producto, **toda la operación se revierte** (rollback). |
| RN-FS05 | Al cancelar un pedido ya `CONFIRMADO`, se **restaura el stock** atómicamente. |
| RN-FS06 | `ENTREGADO` y `CANCELADO` son **estados terminales**. Sin transiciones salientes. |
| RN-FS07 | Todo cambio de estado se registra en `HistorialEstadoPedido` (**append-only: solo INSERT**). |
| RN-FS08 | Cancelación posible desde: `PENDIENTE` (Cliente/Gestor/Admin), `CONFIRMADO` (Gestor/Admin), `EN_PREP` (solo Admin). |
| RN-FS09 | Cada historial incluye: estado anterior, estado nuevo, timestamp, usuario o SISTEMA, observación. |
| RN-FS10 | El **motivo es obligatorio** si `nuevo_estado = CANCELADO`. |

---

## Dominio: Pagos MercadoPago

| ID | Regla |
|---|---|
| RN-MP01 | Se genera un `idempotency_key` (UUID) por cada pago para evitar cobros duplicados por reintentos. |
| RN-MP02 | El webhook IPN procesa **solo** `topic=payment`. Otros topics son ignorados. |
| RN-MP03 | El procesamiento del webhook es **idempotente**: si llega duplicado, no duplica la transición. |
| RN-MP04 | Solo un pago `approved` dispara la transición automática `PENDIENTE → CONFIRMADO`. |
| RN-MP05 | El `external_reference` del pago en MercadoPago es el UUID del Pedido. |

---

## Snapshots — Invariantes de Negocio

Los snapshots garantizan que los datos históricos sean inmutables:

- `DetallePedido.precio_snapshot`: precio del producto **al momento de crear el pedido**.
- `DetallePedido.nombre_snapshot`: nombre del producto al momento de crear el pedido.
- `Pedido.direccion_snapshot`: dirección completa al momento de crear el pedido (JSONB).
- `Pedido.total`: total calculado y fijado al momento de crear el pedido.

**Modificar un producto o dirección DESPUÉS de crear un pedido NO debe alterar los datos del pedido existente.**
