from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import logger
from app.api.v1.router import api_router
from app.db.session import async_engine, Base
import app.models  # Ensure all SQLAlchemy models are registered

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AURUM Service Intelligence backend...")
    # Auto-initialize database tables if not existing
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema verification and table initialization complete.")
    except Exception as e:
        logger.warning(f"Database table auto-init skipped or deferred: {e}")

    yield

    logger.info("Shutting down AURUM Service Intelligence backend...")
    await async_engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Service Operations Command Center Backend — High-performance intelligence API covering Assets, Fault Analytics, IoT Monitoring, PM Compliance, AMC/CMC Contracts, Alerts, and Grounded AI Assistant.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handlers ensuring unified API response format
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "data": None,
            "message": "Input validation error",
            "error_code": "VALIDATION_ERROR",
            "meta": {"errors": exc.errors()}
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "message": exc.detail,
            "error_code": f"HTTP_{exc.status_code}"
        }
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled server exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "message": "Internal server error occurred",
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    )

# Include primary API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["System Information"])
async def root():
    return {
        "service": "AURUM Service Intelligence API",
        "status": "OPERATIONAL",
        "version": settings.VERSION,
        "docs": "/docs",
        "api_v1_prefix": settings.API_V1_STR
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
