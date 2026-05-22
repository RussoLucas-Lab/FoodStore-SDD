"""Punto de entrada de la aplicación FastAPI — Food Store API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.limiter import limiter


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


# ---------------------------------------------------------------------------
# Aplicación FastAPI
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Food Store API",
    description="API REST para el e-commerce de alimentos Food Store.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Attach rate limiter
app.state.limiter = limiter

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "*"],
)


# ---------------------------------------------------------------------------
# Exception Handlers — RFC 7807
# ---------------------------------------------------------------------------

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Retorna RFC 7807 con code RATE_LIMIT_EXCEEDED y header Retry-After."""
    retry_after = getattr(exc, "retry_after", 900)
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Demasiados intentos. Intente nuevamente más tarde.",
            "code": "RATE_LIMIT_EXCEEDED",
            "status": status.HTTP_429_TOO_MANY_REQUESTS,
        },
        headers={"Retry-After": str(retry_after)},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Manejador de HTTPException en formato RFC 7807."""
    detail = exc.detail
    if isinstance(detail, dict):
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": str(detail),
            "code": _status_to_code(exc.status_code),
            "status": exc.status_code,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Manejador de errores de validación Pydantic — RFC 7807 con field."""
    first_error = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(loc) for loc in first_error.get("loc", []) if loc != "body")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": first_error.get("msg", "Error de validación"),
            "code": "VALIDATION_ERROR",
            "field": field or None,
            "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Error interno del servidor.",
            "code": "INTERNAL_SERVER_ERROR",
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )


def _status_to_code(status_code: int) -> str:
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
    }
    return mapping.get(status_code, f"HTTP_{status_code}")


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

try:
    from app.modules.auth.router import router as auth_router
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
except ImportError:
    pass

try:
    from app.modules.usuarios.router import router as usuarios_router
    app.include_router(usuarios_router, prefix="/api/v1/usuarios", tags=["Usuarios"])
except ImportError:
    pass

try:
    from app.modules.categorias.router import router as categorias_router
    app.include_router(categorias_router, prefix="/api/v1/categorias", tags=["Categorias"])
except ImportError:
    pass

try:
    from app.modules.ingredientes.router import router as ingredientes_router
    app.include_router(ingredientes_router, prefix="/api/v1/ingredientes", tags=["Ingredientes"])
except ImportError:
    pass

try:
    from app.modules.productos.router import router as productos_router
    app.include_router(productos_router, prefix="/api/v1/productos", tags=["Productos"])
except ImportError:
    pass

try:
    from app.modules.direcciones.router import router as direcciones_router
    app.include_router(direcciones_router, prefix="/api/v1/direcciones", tags=["Direcciones"])
except ImportError:
    pass

try:
    from app.modules.pedidos.router import router as pedidos_router
    app.include_router(pedidos_router, prefix="/api/v1/pedidos", tags=["Pedidos"])
except ImportError:
    pass

try:
    from app.modules.pagos.router import router as pagos_router
    app.include_router(pagos_router, prefix="/api/v1/pagos", tags=["Pagos"])
except ImportError:
    pass

try:
    from app.modules.admin.router import router as admin_router
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    return {"status": "ok", "service": "food-store-api"}
