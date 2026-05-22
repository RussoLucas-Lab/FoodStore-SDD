## ADDED Requirements

### Requirement: Formulario de login

El frontend SHALL ofrecer un `LoginForm` construido con TanStack Form que valida `email` (formato) y `password` (≥ 8 caracteres) en el cliente antes de enviar `POST /api/v1/auth/login`.

#### Scenario: Login exitoso como CLIENT

- **WHEN** el usuario envía credenciales válidas de un usuario con rol `CLIENT`
- **THEN** el frontend guarda el `access_token` en `authStore` (vía `zustand/persist`), guarda el refresh token según la estrategia configurada, hace `GET /auth/me` para reconstruir `usuario` y redirige a `/`

#### Scenario: Login exitoso como ADMIN/STOCK/PEDIDOS

- **WHEN** el usuario envía credenciales válidas de un usuario con rol administrativo
- **THEN** el frontend redirige a `/admin` luego de obtener el usuario

#### Scenario: Login con credenciales inválidas

- **WHEN** la API responde `401 INVALID_CREDENTIALS`
- **THEN** el formulario muestra un mensaje genérico ("Email o contraseña incorrectos") y NO indica cuál campo es el incorrecto

#### Scenario: Login con rate limit

- **WHEN** la API responde `429 RATE_LIMIT_EXCEEDED`
- **THEN** el formulario muestra un toast con el tiempo de espera y deshabilita el botón "Iniciar sesión" hasta que pase la ventana

### Requirement: Formulario de registro

El frontend SHALL ofrecer un `RegisterForm` con TanStack Form que valida `email`, `password`, `confirmPassword` (deben coincidir), `nombre` y `apellido`, y envía `POST /api/v1/auth/register`.

#### Scenario: Registro exitoso

- **WHEN** el usuario completa el formulario con datos válidos y presiona "Crear cuenta"
- **THEN** el frontend recibe `201`, ejecuta automáticamente un login con las mismas credenciales y redirige a `/`

#### Scenario: Email duplicado

- **WHEN** la API responde `409 EMAIL_ALREADY_EXISTS`
- **THEN** el frontend marca el campo `email` con el error "Este email ya está registrado" usando el `field` del body RFC 7807

#### Scenario: Confirmación de password no coincide

- **WHEN** `password` y `confirmPassword` difieren
- **THEN** el formulario muestra error en el campo `confirmPassword` y NO envía el request

### Requirement: Persistencia de sesión

`authStore` SHALL persistir SOLO el `accessToken` en `localStorage` mediante `zustand/persist`. El objeto `usuario` SHALL reconstruirse llamando a `GET /api/v1/auth/me` al iniciar la app (bootstrap).

#### Scenario: Recarga con token válido

- **WHEN** el usuario recarga la página y `authStore.accessToken` está presente y válido
- **THEN** la app dispara `GET /auth/me`, popula `authStore.usuario` y queda autenticado sin requerir login

#### Scenario: Recarga con token expirado

- **WHEN** `accessToken` está expirado pero existe refresh token vigente
- **THEN** el interceptor 401 dispara `/auth/refresh`, reintenta `/auth/me` y la sesión queda restablecida

#### Scenario: Recarga sin token

- **WHEN** `authStore.accessToken` está vacío al cargar la app
- **THEN** la app NO llama a `/auth/me` y muestra el estado público (navbar con "Iniciar sesión")

### Requirement: Interceptor 401 con refresh automático

El cliente Axios SHALL tener un interceptor de response que, ante un `401` con `code` `ACCESS_TOKEN_EXPIRED`, dispare `POST /auth/refresh` una sola vez por request, actualice el `accessToken` en `authStore` y reintente la request original.

#### Scenario: Refresh exitoso transparente

- **WHEN** un endpoint protegido devuelve `401 ACCESS_TOKEN_EXPIRED`
- **THEN** el interceptor llama `/auth/refresh`, recibe nuevos tokens, actualiza `authStore` y reintenta la request original con el nuevo access token; el componente recibe la respuesta como si nunca hubiera fallado

#### Scenario: Refresh fallido

- **WHEN** el `/auth/refresh` devuelve `401 REFRESH_TOKEN_EXPIRED` o `REFRESH_TOKEN_REUSED`
- **THEN** el interceptor limpia `authStore`, muestra un toast "Sesión expirada" y redirige a `/login`

#### Scenario: Loop de refresh evitado

- **WHEN** llegan múltiples requests `401` en paralelo
- **THEN** el interceptor encola las requests pendientes, dispara UN único `/auth/refresh`, y al resolverse las reintenta todas con el nuevo token

### Requirement: Rutas protegidas

El frontend SHALL proveer un componente `ProtectedRoute` con props `roles?: string[]` que verifica `isAuthenticated` y, si se pasan `roles`, que el rol del usuario esté incluido. Si la verificación falla, redirige a `/login` (sin sesión) o a `/` (con sesión pero sin rol).

#### Scenario: Acceso permitido

- **WHEN** un usuario autenticado con rol incluido en `roles` entra a una ruta envuelta en `ProtectedRoute`
- **THEN** la ruta renderiza normalmente

#### Scenario: Acceso sin sesión

- **WHEN** un visitante sin `accessToken` intenta entrar a `/pedidos`
- **THEN** es redirigido a `/login?next=/pedidos`

#### Scenario: Acceso con rol insuficiente

- **WHEN** un usuario con rol `CLIENT` intenta entrar a `/admin`
- **THEN** es redirigido a `/` y se muestra un toast `code: INSUFFICIENT_ROLE`

### Requirement: Logout en el cliente

El frontend SHALL exponer una acción `logout()` que llama `POST /auth/logout`, limpia `authStore` y `cartStore` (si corresponde según política) y redirige a `/`.

#### Scenario: Logout desde el menú de usuario

- **WHEN** un usuario autenticado hace click en "Cerrar sesión" en el navbar
- **THEN** el cliente llama `/auth/logout`, limpia el store de auth, y redirige a `/` mostrando el navbar público
