## ADDED Requirements

### Requirement: Resumen KPIs del dashboard (ADMIN)
El sistema SHALL exponer `GET /api/v1/admin/metricas/resumen` que devuelve KPIs actuales: total de pedidos, total de ventas del mes corriente, cantidad de productos activos y cantidad de usuarios activos. Restringido a rol ADMIN.

#### Scenario: Respuesta con datos
- **WHEN** ADMIN llama `GET /api/v1/admin/metricas/resumen`
- **THEN** responde HTTP 200 con `{ "total_pedidos": int, "ventas_mes": float, "productos_activos": int, "usuarios_activos": int }`

#### Scenario: Sin pedidos ni ventas
- **WHEN** no hay pedidos en el sistema
- **THEN** responde HTTP 200 con `{ "total_pedidos": 0, "ventas_mes": 0.0, "productos_activos": N, "usuarios_activos": M }`

#### Scenario: Sin autenticación o rol insuficiente
- **WHEN** se llama sin token ADMIN
- **THEN** responde HTTP 403

### Requirement: Ventas por período (ADMIN)
El sistema SHALL exponer `GET /api/v1/admin/metricas/ventas?periodo=dia|semana|mes` que devuelve una serie temporal de ventas (suma de totales de pedidos en estado ENTREGADO). Valor por defecto `mes` (últimos 30 días). Restringido a rol ADMIN.

#### Scenario: Ventas del último mes (default)
- **WHEN** ADMIN llama `GET /api/v1/admin/metricas/ventas`
- **THEN** responde HTTP 200 con `{ "periodo": "mes", "series": [{ "fecha": "YYYY-MM-DD", "total": float }] }` con una entrada por día de los últimos 30 días

#### Scenario: Ventas de la última semana
- **WHEN** ADMIN llama con `?periodo=semana`
- **THEN** responde con series de los últimos 7 días

#### Scenario: Ventas del día
- **WHEN** ADMIN llama con `?periodo=dia`
- **THEN** responde con series de las últimas 24 horas agrupadas por hora

#### Scenario: Período inválido
- **WHEN** se envía `?periodo=año`
- **THEN** responde HTTP 422 (validación Pydantic — `Literal["dia", "semana", "mes"]`)

### Requirement: Ranking de productos más vendidos (ADMIN)
El sistema SHALL exponer `GET /api/v1/admin/metricas/productos-top?limit=10` que devuelve los N productos con mayor cantidad de unidades vendidas (sum de `DetallePedido.cantidad` para pedidos en ENTREGADO). Máximo `limit=50`. Restringido a rol ADMIN.

#### Scenario: Top 10 productos
- **WHEN** ADMIN llama `GET /api/v1/admin/metricas/productos-top`
- **THEN** responde HTTP 200 con lista de hasta 10 items: `[{ "producto_id": int, "nombre": str, "unidades_vendidas": int, "total_generado": float }]`

#### Scenario: Limit personalizado
- **WHEN** ADMIN llama con `?limit=5`
- **THEN** devuelve máximo 5 productos

#### Scenario: Limit excede máximo
- **WHEN** se envía `?limit=100`
- **THEN** responde HTTP 422

### Requirement: Distribución de pedidos por estado (ADMIN)
El sistema SHALL exponer `GET /api/v1/admin/metricas/pedidos-por-estado` que devuelve el conteo de pedidos agrupado por `EstadoPedido`. Restringido a rol ADMIN.

#### Scenario: Distribución con pedidos
- **WHEN** ADMIN llama `GET /api/v1/admin/metricas/pedidos-por-estado`
- **THEN** responde HTTP 200 con `[{ "estado": str, "cantidad": int }]` con una entrada por cada estado que tenga al menos un pedido

#### Scenario: Sin pedidos
- **WHEN** no hay pedidos en el sistema
- **THEN** responde HTTP 200 con lista vacía `[]`
