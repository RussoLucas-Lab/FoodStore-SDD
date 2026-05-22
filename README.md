# 🍔 Food Store

Sistema de e-commerce de alimentos — React + TypeScript + FastAPI + PostgreSQL

---

## Setup Rápido

### Requisitos previos
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Completar variables
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload
```

API disponible en `http://localhost:8000` — Swagger en `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
cp .env.example .env      # Completar VITE_API_URL y VITE_MP_PUBLIC_KEY
npm run dev
```

App disponible en `http://localhost:5173`

---

## Documentación

| Archivo | Contenido |
|---|---|
| `docs/ARCHITECTURE.md` | Capas del sistema, patrones, UoW, Feature-Sliced Design |
| `docs/DATA_MODEL.md` | ERD completo v5, constraints, snapshots |
| `docs/API_SPEC.md` | Endpoints, schemas Pydantic, convenciones REST |
| `docs/BUSINESS_RULES.md` | Reglas de negocio y FSM del pedido |
| `docs/SPRINTS.md` | Plan de implementación por sprints |
| `docs/DESIGN_SYSTEM.md` | Sistema de diseño Apple-inspired |
| `CLAUDE.md` | Guía principal para Claude Code |

---

## Credenciales de Prueba

| Rol | Email | Contraseña |
|---|---|---|
| Admin | `admin@foodstore.com` | `Admin1234!` |

**Tarjetas MercadoPago Sandbox:**
- Visa aprobada: `4509 9535 6623 3704` — CVV: 123 — Venc: 11/25
- Visa rechazada: `4000 0000 0000 0002` — CVV: 123 — Venc: 11/25

---

## Demo

> 🎬 [Link al video de demostración](#) ← completar antes de entregar
