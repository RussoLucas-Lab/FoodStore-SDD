## ADDED Requirements

### Requirement: Configuración centralizada con variables de entorno
El sistema SHALL cargar toda la configuración desde variables de entorno mediante Pydantic Settings en `core/config.py`. Nunca se deben hardcodear secrets en código.

#### Scenario: Variables presentes
- **WHEN** se instancia `Settings` con un archivo `.env` válido
- **THEN** los atributos `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `CORS_ORIGINS`, `MP_ACCESS_TOKEN` y `MP_PUBLIC_KEY` están disponibles como atributos tipados

#### Scenario: Variable obligatoria ausente
- **WHEN** falta `SECRET_KEY` o `DATABASE_URL` en el entorno
- **THEN** la aplicación lanza `ValidationError` de Pydantic al arrancar, antes de aceptar cualquier request

---

### Requirement: Unit of Work como context manager
El sistema SHALL proveer un `UnitOfWork` que gestione la transacción de BD de forma automática. Ningún Service SHALL hacer `session.commit()` ni `session.rollback()` directamente.

#### Scenario: Operación exitosa
- **WHEN** el bloque `with UnitOfWork() as uow:` se ejecuta sin excepción
- **THEN** `session.commit()` se invoca al salir del contexto y los cambios se persisten

#### Scenario: Excepción dentro del bloque
- **WHEN** se lanza cualquier excepción dentro del bloque `with UnitOfWork()`
- **THEN** `session.rollback()` se invoca, ningún cambio se persiste, y la excepción se propaga

#### Scenario: Acceso a repositorios
- **WHEN** se usa `uow` dentro del bloque `with`
- **THEN** `uow.usuarios`, `uow.productos`, `uow.pedidos`, `uow.pagos` y el resto de repositorios están disponibles como atributos con la sesión ya inyectada

---

### Requirement: BaseRepository genérico
El sistema SHALL proveer `BaseRepository[T]` con operaciones CRUD estándar reutilizables por todos los módulos.

#### Scenario: Obtener por ID existente
- **WHEN** se llama `repo.get_by_id(id)` con un ID que existe en la BD
- **THEN** retorna la instancia del modelo con ese ID

#### Scenario: Obtener por ID inexistente
- **WHEN** se llama `repo.get_by_id(id)` con un ID que no existe
- **THEN** retorna `None`

#### Scenario: Crear entidad
- **WHEN** se llama `repo.create(entity)` con una instancia válida
- **THEN** la entidad se agrega a la sesión, se hace `flush()` y `refresh()`, y se retorna con el ID asignado

#### Scenario: Soft delete
- **WHEN** se llama `repo.soft_delete(entity)` en una entidad con campo `deleted_at`
- **THEN** `entity.deleted_at` se asigna a la fecha/hora actual y la entidad queda excluida de los listados estándar

---

### Requirement: Seguridad JWT y bcrypt
El sistema SHALL implementar autenticación basada en JWT HS256 y hashing de contraseñas con bcrypt (cost ≥ 12) en `core/security.py`.

#### Scenario: Hashing de contraseña
- **WHEN** se llama `hash_password("miContraseña")` 
- **THEN** retorna un hash bcrypt de 60 caracteres. El texto plano nunca se almacena.

#### Scenario: Verificación de contraseña correcta
- **WHEN** se llama `verify_password("miContraseña", hash_almacenado)` con la contraseña original
- **THEN** retorna `True`

#### Scenario: Creación de access token
- **WHEN** se llama `create_access_token(data={"sub": str(user_id), "roles": ["CLIENT"]})`
- **THEN** retorna un JWT firmado con `SECRET_KEY` que expira en `ACCESS_TOKEN_EXPIRE_MINUTES`

#### Scenario: Dependencia get_current_user con token válido
- **WHEN** un endpoint usa `Depends(get_current_user)` y el request incluye `Authorization: Bearer <token_valido>`
- **THEN** la dependencia retorna el usuario autenticado sin lanzar excepción

#### Scenario: Dependencia get_current_user con token inválido
- **WHEN** el token está vencido, malformado o firmado con clave distinta
- **THEN** la dependencia lanza `HTTPException(401)`

#### Scenario: require_role con rol insuficiente
- **WHEN** un endpoint usa `Depends(require_role(["ADMIN"]))` y el usuario tiene solo rol `CLIENT`
- **THEN** la dependencia lanza `HTTPException(403)`

---

### Requirement: Modelos SQLModel completos con constraints
El sistema SHALL definir los 16 modelos SQLModel alineados al `DATA_MODEL.md` con todos los constraints (tipos, NN, UQ, CHECK, FK, soft delete).

#### Scenario: Precio nunca negativo
- **WHEN** se inserta un `Producto` con `precio_base < 0`
- **THEN** la BD rechaza la inserción por el constraint `CHECK >= 0`

#### Scenario: Stock nunca negativo
- **WHEN** se intenta asignar `stock_cantidad = -1` a un `Producto`
- **THEN** la BD rechaza la operación por el constraint `CHECK >= 0`

#### Scenario: Email único
- **WHEN** se intenta insertar un `Usuario` con un email que ya existe
- **THEN** la BD lanza `IntegrityError` por el constraint `UNIQUE` en `email`

---

### Requirement: Migración Alembic inicial
El sistema SHALL incluir una migración Alembic que cree todas las tablas al ejecutar `alembic upgrade head`.

#### Scenario: Migración en BD vacía
- **WHEN** se ejecuta `alembic upgrade head` con `DATABASE_URL` apuntando a una BD PostgreSQL vacía
- **THEN** se crean las 16 tablas sin errores y `alembic_version` registra la revisión actual

#### Scenario: Migración idempotente
- **WHEN** se ejecuta `alembic upgrade head` por segunda vez
- **THEN** no ocurre ningún cambio (ya está en la versión actual)

---

### Requirement: Seed data obligatorio
El sistema SHALL incluir `app/db/seed.py` que pueble los datos de catálogo fijos necesarios para operar.

#### Scenario: Seed en BD vacía
- **WHEN** se ejecuta `python -m app.db.seed` tras `alembic upgrade head`
- **THEN** existen en BD: roles `ADMIN`, `STOCK`, `PEDIDOS`, `CLIENT`; estados de pedido `PENDIENTE`, `CONFIRMADO`, `EN_PREP`, `EN_CAMINO`, `ENTREGADO`, `CANCELADO`; formas de pago `MERCADOPAGO`, `EFECTIVO`, `TRANSFERENCIA`; y el usuario `admin@foodstore.com` con contraseña `Admin1234!` y rol `ADMIN`

#### Scenario: Seed idempotente
- **WHEN** se ejecuta `python -m app.db.seed` más de una vez
- **THEN** no se duplican registros (usa `get_or_create` o `INSERT ... ON CONFLICT DO NOTHING`)

---

### Requirement: Manejo global de errores RFC 7807
El sistema SHALL formatear todas las respuestas de error como `{ "detail": "...", "code": "...", "field": "..." }` mediante un exception handler registrado en `main.py`.

#### Scenario: HTTPException capturada
- **WHEN** cualquier endpoint lanza `HTTPException(404, detail="No encontrado")`
- **THEN** la respuesta tiene status 404 y body `{ "detail": "No encontrado", "code": "NOT_FOUND" }`

#### Scenario: Error de validación Pydantic
- **WHEN** el body del request no cumple el schema Pydantic (422)
- **THEN** la respuesta incluye el campo `field` con el nombre del campo inválido

---

### Requirement: CORS y rate limiting configurados en main.py
El sistema SHALL registrar el middleware CORS con los orígenes de `CORS_ORIGINS` y el rate limiter slowapi antes de montar los routers.

#### Scenario: Request desde origen permitido
- **WHEN** el frontend en `http://localhost:5173` hace un request
- **THEN** la respuesta incluye el header `Access-Control-Allow-Origin: http://localhost:5173`

#### Scenario: Request desde origen no permitido
- **WHEN** un origen no listado en `CORS_ORIGINS` hace un request
- **THEN** el browser recibe respuesta sin el header CORS y bloquea la respuesta
