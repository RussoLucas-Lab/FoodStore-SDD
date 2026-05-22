# DATA_MODEL.md — Food Store ERD v5

El esquema aplica **Tercera Forma Normal (3FN)**, **Soft Delete** (`deleted_at TIMESTAMPTZ`), **Snapshot Pattern** en pedidos y **Audit Trail append-only** en `HistorialEstadoPedido`.

---

## Dominio 1 — Identidad y Acceso

### Usuario
| Campo | Tipo | Restricción | Notas |
|---|---|---|---|
| `id` | BIGSERIAL | PK | Soft-delete vía `deleted_at` |
| `nombre` | VARCHAR(80) | NN | |
| `apellido` | VARCHAR(80) | NN | |
| `email` | VARCHAR(254) | UQ, NN | `EmailStr` Pydantic v2 |
| `password_hash` | CHAR(60) | NN | bcrypt cost≥12. **NUNCA texto plano.** |
| `activo` | BOOLEAN | NN, default true | Toggle sin borrar |
| `deleted_at` | TIMESTAMPTZ | NULL | Soft delete |
| `created_at` | TIMESTAMPTZ | NN, default now() | |

### Rol
| Campo | Tipo | Restricción | Notas |
|---|---|---|---|
| `codigo` | VARCHAR(20) | PK semántica | `ADMIN` \| `STOCK` \| `PEDIDOS` \| `CLIENT` |
| `descripcion` | TEXT | NULL | |

### UsuarioRol (pivot N:M)
| Campo | Tipo | Restricción | Notas |
|---|---|---|---|
| `usuario_id` | BIGINT | FK → Usuario, PK compuesta | |
| `rol_codigo` | VARCHAR(20) | FK → Rol, PK compuesta | |
| `asignado_por_id` | BIGINT | FK → Usuario, NULL | Trazabilidad |
| `created_at` | TIMESTAMPTZ | NN, default now() | |

### RefreshToken ★
| Campo | Tipo | Restricción | Notas |
|---|---|---|---|
| `id` | BIGSERIAL | PK | |
| `usuario_id` | BIGINT | FK → Usuario | |
| `token_hash` | CHAR(64) | UQ, NN | SHA-256 del token |
| `expires_at` | TIMESTAMPTZ | NN | 7 días desde emisión |
| `revoked_at` | TIMESTAMPTZ | NULL | NULL = activo. Se llena en logout o replay attack. |
| `created_at` | TIMESTAMPTZ | NN, default now() | |

### DireccionEntrega ★
| Campo | Tipo | Restricción | Notas |
|---|---|---|---|
| `id` | BIGSERIAL | PK | Soft delete |
| `usuario_id` | BIGINT | FK → Usuario, NN | Ownership |
| `alias` | VARCHAR(50) | NULL | Ej: 'Casa', 'Trabajo' |
| `linea1` | TEXT | NN | Calle y número |
| `linea2` | TEXT | NULL | Piso, depto |
| `ciudad` | VARCHAR(100) | NN | |
| `provincia` | VARCHAR(100) | NN | |
| `codigo_postal` | VARCHAR(20) | NN | |
| `es_principal` | BOOLEAN | NN, default false | Solo una por usuario |
| `deleted_at` | TIMESTAMPTZ | NULL | |

---

## Dominio 2 — Catálogo de Productos

### Categoria
| Campo | Tipo | Restricción | Notas |
|---|---|---|---|
| `id` | BIGSERIAL | PK | Soft delete |
| `nombre` | VARCHAR(100) | NN | |
| `slug` | VARCHAR(120) | UQ, NN | URL-friendly |
| `parent_id` | BIGINT | FK self-ref, NULL | Jerarquía recursiva. ON DELETE SET NULL. CTE. |
| `deleted_at` | TIMESTAMPTZ | NULL | No eliminar con productos activos |

### Ingrediente ★
| Campo | Tipo | Restricción | Notas |
|---|---|---|---|
| `id` | BIGSERIAL | PK | Soft delete |
| `nombre` | VARCHAR(100) | UQ, NN | |
| `es_alergeno` | BOOLEAN | NN, default false | Badge de alérgenos en UI |
| `deleted_at` | TIMESTAMPTZ | NULL | |

### Producto
| Campo | Tipo | Restricción | Notas |
|---|---|---|---|
| `id` | BIGSERIAL | PK | Soft delete |
| `nombre` | VARCHAR(200) | NN | |
| `descripcion` | TEXT | NULL | |
| `precio_base` | DECIMAL(10,2) | CHECK ≥ 0, NN | **Snapshot al crear pedido** |
| `imagen_url` | TEXT | NULL | |
| `stock_cantidad` | INTEGER | CHECK ≥ 0, NN, default 0 | Gestionado por rol STOCK |
| `disponible` | BOOLEAN | NN, default true | Toggle manual independiente del stock |
| `deleted_at` | TIMESTAMPTZ | NULL | Soft delete |
| `created_at` | TIMESTAMPTZ | NN | |

### ProductoCategoria (pivot N:M)
| Campo | Tipo | Restricción |
|---|---|---|
| `producto_id` | BIGINT | FK, PK compuesta |
| `categoria_id` | BIGINT | FK, PK compuesta |
| `es_principal` | BOOLEAN | NN, default false |

### ProductoIngrediente ★ (pivot N:M)
| Campo | Tipo | Restricción | Notas |
|---|---|---|---|
| `producto_id` | BIGINT | FK, PK compuesta | |
| `ingrediente_id` | BIGINT | FK, PK compuesta | |
| `es_removible` | BOOLEAN | NN | Habilita personalización del pedido |

### FormaPago ★
| Campo | Tipo | Restricción | Notas |
|---|---|---|---|
| `codigo` | VARCHAR(20) | PK semántica | `MERCADOPAGO` \| `EFECTIVO` \| `TRANSFERENCIA` |
| `descripcion` | TEXT | NULL | |
| `habilitado` | BOOLEAN | NN, default true | Se puede deshabilitar sin eliminar |

---

## Dominio 3 — Ventas, Pagos y Trazabilidad

### EstadoPedido (catálogo)
| Campo | Tipo | Restricción | Notas |
|---|---|---|---|
| `codigo` | VARCHAR(20) | PK semántica | Ver FSM |
| `descripcion` | TEXT | NULL | |
| `orden` | INTEGER | NN | Orden de display |
| `es_terminal` | BOOLEAN | NN | `true` = no admite transiciones salientes |

### Pedido
| Campo | Tipo | Restricción | Notas |
|---|---|---|---|
| `id` | BIGSERIAL | PK | |
| `usuario_id` | BIGINT | FK → Usuario, NN | Propietario |
| `estado_codigo` | VARCHAR(20) | FK → EstadoPedido | Estado actual |
| `forma_pago_codigo` | VARCHAR(20) | FK → FormaPago | |
| `direccion_id` | BIGINT | FK → DireccionEntrega, NULL | NULL = retiro en local |
| `direccion_snapshot` | JSONB | NN | **Snapshot inmutable de la dirección al crear** |
| `subtotal` | DECIMAL(10,2) | CHECK ≥ 0, NN | Suma de subtotales de items |
| `costo_envio` | DECIMAL(10,2) | NN, default 50.00 | Fijo v1 |
| `total` | DECIMAL(10,2) | CHECK ≥ 0, NN | **Snapshot inmutable al crear** |
| `notas` | TEXT | NULL | Instrucciones del cliente |
| `created_at` | TIMESTAMPTZ | NN | |

### DetallePedido
| Campo | Tipo | Restricción | Notas |
|---|---|---|---|
| `id` | BIGSERIAL | PK | |
| `pedido_id` | BIGINT | FK → Pedido, NN | |
| `producto_id` | BIGINT | FK → Producto, NN | Referencia al producto original |
| `nombre_snapshot` | VARCHAR(200) | NN | **Snapshot: nombre al crear. Inmutable.** |
| `precio_snapshot` | DECIMAL(10,2) | NN | **Snapshot: precio al crear. Inmutable.** |
| `cantidad` | INTEGER | CHECK ≥ 1, NN | |
| `personalizacion` | INTEGER[] | NULL | IDs de ingredientes removidos |

### HistorialEstadoPedido (append-only)
| Campo | Tipo | Restricción | Notas |
|---|---|---|---|
| `id` | BIGSERIAL | PK | |
| `pedido_id` | BIGINT | FK → Pedido, NN | |
| `estado_desde` | VARCHAR(20) | FK → EstadoPedido, NULL | NULL = transición inicial |
| `estado_hasta` | VARCHAR(20) | FK → EstadoPedido, NN | |
| `usuario_id` | BIGINT | FK → Usuario, NULL | NULL = Sistema (webhook) |
| `observacion` | TEXT | NULL | Motivo obligatorio si CANCELADO |
| `created_at` | TIMESTAMPTZ | NN | **Solo INSERT. Nunca UPDATE ni DELETE.** |

### Pago ★
| Campo | Tipo | Restricción | Notas |
|---|---|---|---|
| `id` | BIGSERIAL | PK | |
| `pedido_id` | BIGINT | FK → Pedido, NN | |
| `mp_payment_id` | BIGINT | UQ, NULL | ID devuelto por MercadoPago |
| `mp_preference_id` | VARCHAR(100) | NULL | |
| `mp_status` | VARCHAR(30) | NN | `pending` / `approved` / `rejected` |
| `mp_status_detail` | VARCHAR(100) | NULL | Detalle del estado |
| `external_reference` | VARCHAR(100) | UQ, NN | UUID del Pedido como referencia MP |
| `idempotency_key` | VARCHAR(100) | UQ, NN | UUID generado por backend. Evita cobros duplicados. |
| `monto` | DECIMAL(10,2) | NN | |
| `created_at` | TIMESTAMPTZ | NN | |
| `updated_at` | TIMESTAMPTZ | NN | |

---

## Notas Globales del Esquema

- **Precios**: Siempre `DECIMAL(10,2)`. **Nunca `float` o `double`.**
- **Stock**: `INTEGER CHECK ≥ 0`. Nunca negativo.
- **Soft Delete**: `deleted_at TIMESTAMPTZ`. Los `GET` filtran `WHERE deleted_at IS NULL`. Nunca `DELETE` físico en entidades de negocio.
- **Catálogo público**: Solo `disponible = true AND deleted_at IS NULL`.
- **Categorías**: `parent_id` autoreferencial. CTE recursiva para obtener el árbol. No se permiten ciclos.
- **`INTEGER[]`**: Array nativo de PostgreSQL para `personalizacion` en `DetallePedido`.
