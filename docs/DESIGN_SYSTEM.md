# DESIGN_SYSTEM.md — Food Store

Sistema de diseño inspirado en Apple: minimalismo premium, blanco dominante, un solo color interactivo (azul), fotografía de producto como elemento principal.

---

## Paleta de Colores

| Nombre | Hex | Uso |
|---|---|---|
| `blue` | `#0071E3` | Links, botones CTA, estados interactivos — **único color interactivo** |
| `blue-dark` | `#0055C6` | Hover state de elementos interactivos |
| `text-primary` | `#1D1D1F` | Headings y body — todo el texto principal |
| `text-secondary` | `#6E6E73` | Captions, footnotes, labels secundarios |
| `text-tertiary` | `#AEAEB2` | Placeholders, disabled |
| `bg-white` | `#FFFFFF` | Background principal de página |
| `bg-surface` | `#F5F5F7` | Secciones alternas, fondos de cards |
| `border` | `#D2D2D7` | Divisores, bordes de inputs |
| `bg-dark` | `#000000` | Hero sections de producto |
| `success` | `#34C759` | iOS-style. Uso muy limitado. |
| `error` | `#FF3B30` | iOS-style. Mensajes de error. |

> ⛔ **No usar ningún otro color** para elementos interactivos. Solo `#0071E3`.

---

## Tipografía

**Font stack:** `SF Pro Display`, `SF Pro Text`, `-apple-system`, `BlinkMacSystemFont`, `sans-serif`

| Rol | Size | Weight | Line Height | Letter Spacing | Uso |
|---|---|---|---|---|---|
| Hero | 80px | 700 | 1.05 | -0.02em | Product hero sections |
| H1 | 56px | 600 | 1.1 | -0.01em | Feature headlines |
| H2 | 40px | 500 | 1.15 | 0 | Section headings |
| H3 | 28px | 500 | 1.2 | 0 | Sub-sections |
| Body | 17px | 400 | 1.6 | 0 | Texto general |
| Caption | 12px | 400 | 1.4 | 0 | Footnotes, legales |
| Price | 22px | 500 | 1.2 | 0 | Precios de producto |

**Regla:** SF Pro Display para headings ≥ 20px. SF Pro Text para body. **Nunca más de dos pesos en una página.**

---

## Componentes

### Botones

```css
/* Primary */
background: #0071E3;
color: #FFFFFF;
padding: 12px 24px;
border-radius: 980px; /* pill */
font-size: 17px;
font-weight: 500;
border: none;

/* Primary hover */
background: #0055C6;

/* Secondary — solo texto, sin borde */
background: transparent;
color: #0071E3;
border: none;
```

> ⛔ No usar bordes en botones. Son filled o plain text.

### Cards / Containers

```css
background: #F5F5F7;
border: none;          /* sin bordes — contraste de superficie */
border-radius: 18px;
padding: 40px;
/* sin box-shadow */
```

### Inputs / Formularios

```css
border: 1px solid #D2D2D7;
border-radius: 10px;
padding: 12px 16px;
font-family: SF Pro Text;
font-size: 17px;

/* Focus */
border-color: #0071E3;
outline: none;
```

### Navigation

```css
position: sticky;
top: 0;
background: rgba(255, 255, 255, 0.85);
backdrop-filter: blur(20px);
height: 44px;
z-index: 100;
```

---

## Sistema de Espaciado

| Valor | Uso |
|---|---|
| 8px | Gaps icon-label |
| 16px | Padding compacto |
| 24px | Content blocks |
| 40px | Card padding |
| 64px | Section gaps |
| 96px | Major sections |
| 128px | Hero areas |

---

## Grid y Layout

- **Max-width producto:** 980px
- **Max-width grid:** 1200px
- **Columnas:** 12, gutters 20px

---

## Border Radius

| Nombre | Valor | Uso |
|---|---|---|
| None | 0px | Full-bleed images |
| Sm | 10px | Inputs, small cards |
| Md | 18px | Feature cards, product tiles |
| Lg | 28px | Large feature sections |
| Full | 9999px | CTA buttons (pill shape) |

---

## Breakpoints

| Nombre | Ancho | Cambios clave |
|---|---|---|
| Mobile | 0–767px | Single column, headlines menores |
| Tablet | 768–1023px | Grid 2 columnas |
| Desktop | 1024px+ | Full layout, 3 columnas |

**Touch targets:** mínimo 44×44px. Nav items tienen 44px de altura.

**Responsive headlines:** usar `clamp()` para scaling fluido.

---

## Profundidad / Elevation

| Nivel | Tratamiento | Uso |
|---|---|---|
| Flat | `none` | Superficie de página |
| Nav | `backdrop-filter: blur(20px)` | Sticky nav en scroll |
| Card | Inner shadow sutil | Product tiles |
| Modal | `0 40px 80px rgba(0,0,0,0.2)` | Diálogos |

> Apple raramente usa drop shadows. El blur y el contraste de superficie los reemplazan.

---

## Configuración Tailwind (`tailwind.config.js`)

```js
module.exports = {
  theme: {
    extend: {
      colors: {
        blue: {
          DEFAULT: '#0071E3',
          dark: '#0055C6',
        },
        surface: '#F5F5F7',
        border: '#D2D2D7',
        'text-primary': '#1D1D1F',
        'text-secondary': '#6E6E73',
        'text-tertiary': '#AEAEB2',
        success: '#34C759',
        error: '#FF3B30',
      },
      fontFamily: {
        sans: [
          'SF Pro Display',
          'SF Pro Text',
          '-apple-system',
          'BlinkMacSystemFont',
          'sans-serif',
        ],
      },
      borderRadius: {
        sm: '10px',
        md: '18px',
        lg: '28px',
        full: '9999px',
      },
      maxWidth: {
        product: '980px',
        grid: '1200px',
      },
    },
  },
};
```

---

## Do's and Don'ts

### ✅ Do
- Usar whitespace agresivamente — comunica premium.
- Que la fotografía de producto domine cada página.
- Pill buttons (`border-radius: 980px`) para todos los CTAs primarios.
- Skeleton loaders mientras cargan los datos.
- Toasts para feedback de acciones (éxito/error).
- Modales de confirmación antes de acciones destructivas.

### ⛔ Don't
- No usar más de dos pesos de fuente en una página.
- No agregar bordes ni sombras a las cards — usar contraste de superficie.
- No usar ningún color que no sea azul para elementos interactivos.
- No usar colores de marca secundarios.
- No centrar el texto en bloques de body copy.
