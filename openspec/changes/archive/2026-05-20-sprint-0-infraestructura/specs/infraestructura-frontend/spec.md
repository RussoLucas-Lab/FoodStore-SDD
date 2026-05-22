## ADDED Requirements

### Requirement: Scaffold Vite + React + TypeScript con strict mode
El sistema SHALL usar Vite 5 + React 18 + TypeScript 5 con `strict: true` en `tsconfig.json`. Está prohibido usar `any` en cualquier archivo del proyecto.

#### Scenario: Build sin errores de tipo
- **WHEN** se ejecuta `npm run build`
- **THEN** TypeScript no reporta ningún error de tipo con `strict: true` activo

#### Scenario: Intento de usar any
- **WHEN** se escribe `: any` en cualquier archivo TypeScript
- **THEN** el linter o el type-check reporta un error

---

### Requirement: Tailwind configurado con tokens del design system
El sistema SHALL extender `tailwind.config.js` con los colores, fuentes, border-radius y maxWidth exactos del `DESIGN_SYSTEM.md`. No se usarán clases Tailwind fuera de estos tokens para elementos interactivos.

#### Scenario: Color interactivo correcto
- **WHEN** se aplica la clase `bg-blue` a un elemento
- **THEN** el color resultante es exactamente `#0071E3`

#### Scenario: Border radius pill disponible
- **WHEN** se aplica la clase `rounded-full` a un botón CTA
- **THEN** el border-radius resultante es `9999px`

---

### Requirement: Cliente Axios con interceptors JWT
El sistema SHALL proveer `api/client.ts` con un instancia Axios que adjunte automáticamente el `accessToken` a cada request y gestione el refresh en caso de 401.

#### Scenario: Request con token válido
- **WHEN** `authStore` tiene un `accessToken` y se hace cualquier llamada con el cliente
- **THEN** el header `Authorization: Bearer <token>` se incluye automáticamente

#### Scenario: Response 401 y refresh exitoso
- **WHEN** el servidor responde 401 y existe un refresh token válido en el store
- **THEN** el cliente llama a `POST /api/v1/auth/refresh` automáticamente, actualiza el token en el store y reintenta el request original una vez

#### Scenario: Response 401 y refresh fallido
- **WHEN** el refresh también falla con 401
- **THEN** el cliente limpia el store (logout), redirige a `/login` y rechaza el request original

#### Scenario: No loop infinito en /auth/refresh
- **WHEN** el endpoint `/api/v1/auth/refresh` responde 401
- **THEN** el interceptor no reintenta ese request específico (evita loop)

---

### Requirement: authStore con persist selectivo
El sistema SHALL implementar `store/authStore.ts` usando Zustand con persist middleware que solo persista `accessToken`.

#### Scenario: Persistencia de accessToken
- **WHEN** el usuario hace login y `accessToken` se guarda en el store
- **THEN** al refrescar la página, `accessToken` sigue disponible en el store desde localStorage

#### Scenario: Usuario reconstruido desde API
- **WHEN** la app carga y encuentra `accessToken` en localStorage
- **THEN** llama a `GET /api/v1/auth/me` para reconstruir el objeto `usuario` (no se persiste en localStorage)

#### Scenario: Logout limpia el store
- **WHEN** se llama a `authStore.logout()`
- **THEN** `accessToken` se elimina del store y de localStorage, y `usuario` queda en `null`

---

### Requirement: cartStore persistido completamente
El sistema SHALL implementar `store/cartStore.ts` usando Zustand con persist completo de `items`.

#### Scenario: Items persisten entre recargas
- **WHEN** el usuario agrega productos al carrito y recarga la página
- **THEN** los mismos items siguen en el carrito desde localStorage

#### Scenario: addItem incrementa cantidad si ya existe
- **WHEN** se llama `addItem` con un producto que ya está en el carrito
- **THEN** la cantidad del item existente se incrementa en lugar de duplicar el entry (RN-CR03)

#### Scenario: clearCart vacía el carrito
- **WHEN** se llama `clearCart()`
- **THEN** `items` queda como array vacío y localStorage se actualiza

---

### Requirement: paymentStore sin persist
El sistema SHALL implementar `store/paymentStore.ts` con estado `idle | processing | approved | rejected | error` sin persistencia. El estado se pierde al recargar.

#### Scenario: Estado inicial idle
- **WHEN** se instancia la app o se recarga la página
- **THEN** `paymentStore.status` es `idle`

#### Scenario: Transición de estado
- **WHEN** se llama `paymentStore.setStatus("processing")`
- **THEN** el estado cambia a `processing` y los componentes suscritos se re-renderizan

---

### Requirement: uiStore sin persist
El sistema SHALL implementar `store/uiStore.ts` con estado de UI efímero: `cartOpen`, `sidebarOpen`, `confirmModal`. Sin persistencia.

#### Scenario: Toggle del carrito
- **WHEN** se llama `uiStore.toggleCart()`
- **THEN** `cartOpen` alterna entre `true` y `false`

#### Scenario: Estado UI se resetea al recargar
- **WHEN** el usuario recarga la página con el carrito abierto
- **THEN** `cartOpen` vuelve a `false`

---

### Requirement: Componentes UI base alineados al design system
El sistema SHALL proveer los componentes `Button`, `Input`, `Card`, `Modal`, `Toast`, `Spinner` y `Skeleton` en `components/` usando los tokens Tailwind del design system.

#### Scenario: Button primario con forma pill
- **WHEN** se renderiza `<Button variant="primary">Comprar</Button>`
- **THEN** el botón tiene `background: #0071E3`, `border-radius: 9999px` y sin borde visible

#### Scenario: Input con focus azul
- **WHEN** el usuario hace foco en un `<Input />`
- **THEN** el borde cambia a `#0071E3` sin outline adicional

#### Scenario: Card sin borde ni sombra
- **WHEN** se renderiza `<Card>`
- **THEN** el fondo es `#F5F5F7`, sin `border` y sin `box-shadow`

#### Scenario: Skeleton durante carga
- **WHEN** se renderiza `<Skeleton />` mientras los datos cargan
- **THEN** se muestra una animación de pulso en el espacio del contenido que aún no llegó

---

### Requirement: React Router con rutas base
El sistema SHALL configurar React Router DOM con rutas placeholder para `/`, `/login`, `/register`, `/pedidos`, `/checkout` y `/admin`.

#### Scenario: Navegación a ruta conocida
- **WHEN** el usuario navega a `/login`
- **THEN** se renderiza el componente asociado sin recargar la página (SPA routing)

#### Scenario: Ruta desconocida
- **WHEN** el usuario navega a una URL no definida
- **THEN** se renderiza una página 404 o redirige a `/`
