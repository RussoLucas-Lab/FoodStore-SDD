## Why

El proyecto Food Store no tiene código base aún. Este sprint establece toda la infraestructura técnica necesaria para que los sprints siguientes puedan construirse: backend FastAPI con PostgreSQL y el patrón de capas (UoW + Repository + Service), más el scaffold de frontend con Vite + React + TypeScript y los cuatro Zustand stores. Sin este foundation, ningún feature puede implementarse.

## What Changes

- Scaffold del proyecto FastAPI con estructura feature-first (`app/modules/`, `app/core/`, `app/db/`)
- `core/config.py` con Pydantic Settings (carga `.env`)
- `core/uow.py` — Unit of Work como context manager con commit/rollback automático
- `core/repository.py` — `BaseRepository[T]` genérico con los métodos estándar
- `core/security.py` — JWT HS256, bcrypt cost ≥ 12, dependencias `get_current_user` y `require_role`
- `app/db/database.py` — engine y SessionLocal con SQLModel
- 16 modelos SQLModel: `Usuario`, `Rol`, `UsuarioRol`, `RefreshToken`, `DireccionEntrega`, `Categoria`, `Ingrediente`, `Producto`, `ProductoCategoria`, `ProductoIngrediente`, `FormaPago`, `EstadoPedido`, `Pedido`, `DetallePedido`, `HistorialEstadoPedido`, `Pago`
- Alembic: migración inicial `alembic upgrade head`
- `app/db/seed.py` — roles, estados de pedido, formas de pago, usuario admin
- Manejo global de errores RFC 7807 en `app/main.py`
- `app/main.py` con CORS, slowapi rate limiter y registro de todos los routers
- `.env.example` con todas las variables documentadas
- Scaffold frontend Vite + React 18 + TypeScript 5 + Tailwind 3
- `tsconfig.json` con `strict: true`
- Tailwind configurado con los tokens de `DESIGN_SYSTEM.md`
- `api/client.ts` — Axios con interceptors JWT (attach token + refresh automático en 401)
- `store/authStore.ts` — persist solo `accessToken`
- `store/cartStore.ts` — persist completo de items
- `store/paymentStore.ts` — sin persist
- `store/uiStore.ts` — sin persist
- Estructura de carpetas `features/`, `pages/`, `components/`, `hooks/`, `types/`, `utils/`
- Componentes UI base: `Button`, `Input`, `Card`, `Modal`, `Toast`, `Spinner`, `Skeleton`
- React Router DOM con rutas placeholder

## Capabilities

### New Capabilities

- `infraestructura-backend`: Scaffold FastAPI, capas core (UoW, Repository, Security, Config), modelos SQLModel, migración Alembic inicial y seed data
- `infraestructura-frontend`: Scaffold Vite + React + TypeScript, Zustand stores, cliente Axios con JWT, tokens Tailwind del design system y componentes UI atómicos base

### Modified Capabilities

## Impact

- Crea la estructura de carpetas completa del proyecto en ambas capas
- Todos los sprints 1–8 dependen de este sprint; ninguno puede comenzar sin él
- Dependencias backend nuevas: `fastapi`, `sqlmodel`, `alembic`, `passlib[bcrypt]`, `python-jose`, `slowapi`, `psycopg2-binary`, `python-dotenv`, `pydantic-settings`, `mercadopago`
- Dependencias frontend nuevas: `react`, `react-dom`, `react-router-dom`, `axios`, `zustand`, `@tanstack/react-query`, `@tanstack/react-form`, `tailwindcss`, `recharts`, `@mercadopago/sdk-react`
- Requiere PostgreSQL 15+ local o en Docker; variable `DATABASE_URL` configurada
