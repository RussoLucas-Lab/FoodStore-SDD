# API_SPEC.md — Food Store

Todos los endpoints usan prefijo `/api/v1`. Errores según **RFC 7807**. Documentación automática en `/docs` y `/redoc`.

## Convenciones Globales

**Error estándar RFC 7807:**
```json
{ "detail": "mensaje", "code": "ERROR_CODE", "field": "campo_opcional" }
```

**Paginación:**
```
GET /recursos?page=1&size=20
→ { "items": [...], "total": N, "page": 1, "size": 20, "pages": P }
```

**Soft delete:** todos los `GET` filtran `WHERE deleted_at IS NULL`.

**Status codes:**
- `200` OK, `201` Created, `204` No Content
- `400` Bad Request, `401` Unauthorized, `403` Forbidden, `404` Not Found
- `409` Conflict, `422` Unprocessable Entity, `429` Too Many Requests

---

## 5.1 Módulo Auth

| Método | Endpoint | Body | Response | Auth |
|---|---|---|---|---|
| POST | `/auth/register` | `{ nombre, apellido, email, password }` | 201 `UserResponse` | No |
| POST | `/auth/login` | `{ email, password }` | 200 `TokenResponse` | No — rate limited 5/15min |
| POST | `/auth/refresh` | `{ refresh_token }` | 200 `TokenResponse` | No |
| POST | `/auth/logout` | `{ refresh_token }` | 204 No Content | Bearer |
| GET | `/auth/me` | — | 200 `UserResponse` | Bearer |

---

## 5.2 Módulo Categorías

| Método | Endpoint | Descripción | Rol | Response |
|---|---|---|---|---|
| GET | `/categorias` | Listar árbol completo con CTE recursiva | Público | 200 `List[CategoriaTree]` |
| GET | `/categorias/{id}` | Detalle con subcategorías | Público | 200 `CategoriaDetail` |
| POST | `/categorias` | Crear categoría | ADMIN | 201 `CategoriaRead` |
| PUT | `/categorias/{id}` | Actualizar | ADMIN | 200 `CategoriaRead` |
| DELETE | `/categorias/{id}` | Soft delete (falla si tiene productos activos) | ADMIN | 204 |

---

## 5.3 Módulo Ingredientes

| Método | Endpoint | Descripción | Rol | Response |
|---|---|---|---|---|
| GET | `/ingredientes` | Listar (filtro: `es_alergeno`) | ADMIN, STOCK | 200 `List[IngredienteRead]` |
| GET | `/ingredientes/{id}` | Detalle | ADMIN, STOCK | 200 `IngredienteRead` |
| POST | `/ingredientes` | Crear | ADMIN | 201 `IngredienteRead` |
| PUT | `/ingredientes/{id}` | Actualizar | ADMIN | 200 `IngredienteRead` |
| DELETE | `/ingredientes/{id}` | Soft delete | ADMIN | 204 |

---

## 5.4 Módulo Productos

| Método | Endpoint | Descripción | Rol | Response |
|---|---|---|---|---|
| GET | `/productos` | Listar (filtros: `categoria`, `disponible`, `search`, `page`, `size`, `excluir_alergenos`) | Público | 200 `PaginatedProductos` |
| GET | `/productos/{id}` | Detalle con ingredientes, categorías y stock | Público | 200 `ProductoDetail` |
| POST | `/productos` | Crear con ingredientes y categorías | ADMIN | 201 `ProductoRead` |
| PUT | `/productos/{id}` | Actualizar | ADMIN | 200 `ProductoRead` |
| PATCH | `/productos/{id}/disponibilidad` | Toggle disponible | ADMIN, STOCK | 200 `ProductoRead` |
| PATCH | `/productos/{id}/stock` | Actualizar stock | ADMIN, STOCK | 200 `ProductoRead` |
| DELETE | `/productos/{id}` | Soft delete | ADMIN | 204 |
| GET | `/productos/{id}/ingredientes` | Listar ingredientes del producto | Público | 200 `List[IngredienteRead]` |
| POST | `/productos/{id}/ingredientes` | Asociar ingrediente | ADMIN | 201 `ProductoIngredienteRead` |
| DELETE | `/productos/{id}/ingredientes/{ing_id}` | Quitar ingrediente | ADMIN | 204 |

---

## 5.5 Módulo Direcciones

| Método | Endpoint | Descripción | Rol | Response |
|---|---|---|---|---|
| GET | `/direcciones` | Listar propias | CLIENT (owner) | 200 `List[DireccionRead]` |
| POST | `/direcciones` | Crear nueva dirección | CLIENT | 201 `DireccionRead` |
| PUT | `/direcciones/{id}` | Actualizar | CLIENT (owner) | 200 `DireccionRead` |
| PATCH | `/direcciones/{id}/principal` | Marcar como principal | CLIENT (owner) | 200 `DireccionRead` |
| DELETE | `/direcciones/{id}` | Soft delete | CLIENT (owner) | 204 |

---

## 5.6 Módulo Pedidos

| Método | Endpoint | Descripción | Rol | Response |
|---|---|---|---|---|
| GET | `/pedidos` | Listar propios (CLIENT) o todos (ADMIN/PEDIDOS) | CLIENT/ADMIN/PEDIDOS | 200 `PaginatedPedidos` |
| GET | `/pedidos/{id}` | Detalle completo con líneas, historial y pago | Owner/ADMIN | 200 `PedidoDetail` |
| POST | `/pedidos` | Crear pedido desde carrito. Atómico (UoW). | CLIENT | 201 `PedidoRead` |
| PATCH | `/pedidos/{id}/estado` | Avanzar estado. Valida FSM. UoW atómico. | ADMIN/PEDIDOS | 200 `PedidoRead` |
| GET | `/pedidos/{id}/historial` | Historial completo, ORDER BY `created_at` ASC | Owner/ADMIN | 200 `List[HistorialRead]` |
| DELETE | `/pedidos/{id}` | Cancelar propio (solo PENDIENTE) | CLIENT owner | 200 `PedidoRead` |

---

## 5.7 Módulo Pagos (MercadoPago)

| Método | Endpoint | Descripción | Rol | Response |
|---|---|---|---|---|
| POST | `/pagos/crear` | Crea pago con token de tarjeta. Registra en tabla `Pago`. | CLIENT | 201 `PagoResponse` |
| POST | `/pagos/webhook` | Endpoint IPN de MercadoPago. Valida firma. Actualiza pago y pedido. | Público | 200 `{ status: ok }` |
| GET | `/pagos/{pedido_id}` | Consulta el pago de un pedido | Owner/ADMIN | 200 `PagoResponse` |

---

## 5.8 Módulo Usuarios (Admin)

| Método | Endpoint | Descripción | Rol | Response |
|---|---|---|---|---|
| GET | `/admin/usuarios` | Listar con filtros (página, activo, rol) | ADMIN | 200 `PaginatedUsuarios` |
| GET | `/admin/usuarios/{id}` | Detalle | ADMIN | 200 `UserResponse` |
| POST | `/admin/usuarios` | Crear usuario | ADMIN | 201 `UserResponse` |
| PUT | `/admin/usuarios/{id}` | Actualizar datos | ADMIN | 200 `UserResponse` |
| PATCH | `/admin/usuarios/{id}/roles` | Asignar/quitar roles | ADMIN | 200 `UserResponse` |
| PATCH | `/admin/usuarios/{id}/activar` | Activar / desactivar | ADMIN | 200 `UserResponse` |

---

## 5.9 Módulo Admin — Métricas

| Método | Endpoint | Descripción | Rol |
|---|---|---|---|
| GET | `/admin/metricas/resumen` | KPIs: ventas totales, pedidos del día, ingresos | ADMIN |
| GET | `/admin/metricas/ventas?desde=&hasta=` | Ventas por período con gráfico de línea | ADMIN |
| GET | `/admin/metricas/productos-top?top=10` | Ranking productos más vendidos | ADMIN |
| GET | `/admin/metricas/pedidos-por-estado` | Distribución de pedidos por estado | ADMIN |

---

## 6. Schemas Pydantic v2

### Auth

| Schema | Campos | Validaciones |
|---|---|---|
| `LoginRequest` | `email: EmailStr`, `password: str` | `password` mín 8 chars |
| `RegisterRequest` | `nombre`, `apellido`, `email: EmailStr`, `password: str` | nombre/apellido min 2 max 80. Unicidad de email en service. |
| `TokenResponse` | `access_token`, `refresh_token`, `token_type`, `expires_in: int` | `token_type = 'bearer'`. `expires_in` en segundos. |
| `UserResponse` | `id`, `nombre`, `apellido`, `email`, `roles: list[str]`, `created_at` | Nunca incluye `password_hash`. |

### Pedidos

| Schema | Campos | Validaciones |
|---|---|---|
| `CrearPedidoRequest` | `items: list[ItemPedidoRequest]`, `forma_pago_codigo: str`, `direccion_id: int\|None`, `notas: str\|None` | Mínimo 1 item. `forma_pago_codigo` debe existir en catálogo. |
| `ItemPedidoRequest` | `producto_id: int`, `cantidad: int`, `personalizacion: list[int]\|None` | `cantidad ≥ 1`. `personalizacion` = IDs de ingredientes removidos. |
| `AvanzarEstadoRequest` | `nuevo_estado: str`, `motivo: str\|None` | `motivo` obligatorio si `nuevo_estado = CANCELADO`. |
| `PedidoRead` | `id`, `estado_codigo`, `total`, `created_at` | Versión compacta para listados. |
| `PedidoDetail` | `id`, `estado_codigo`, `subtotal`, `costo_envio`, `total`, `items`, `historial`, `pago` | Versión completa. |
| `DetallePedidoRead` | `producto_id`, `nombre_snapshot`, `precio_snapshot`, `cantidad`, `personalizacion` | Snapshot: precio y nombre no reflejan cambios posteriores. |

### Productos

| Schema | Campos | Notas |
|---|---|---|
| `ProductoCreate` | `nombre`, `descripcion`, `precio_base`, `imagen_url`, `categoria_ids: list[int]`, `ingredientes: list[ProductoIngredienteCreate]` | |
| `ProductoUpdate` | Todos opcionales | PATCH semántico |
| `ProductoRead` | `id`, `nombre`, `precio_base`, `stock_cantidad`, `disponible`, `imagen_url`, `categorias`, `ingredientes` | |
| `ProductoDetail` | `ProductoRead` + descripción completa | |
