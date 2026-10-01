from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.schemas.common import ApiResponse
import datetime

router = APIRouter()

@router.get("/health", summary="Service Liveness Probe")
async def health_check():
    """
    Returns immediate status 200 when application server process is running.
    """
    return {
        "status": "healthy",
        "service": "AURUM Service Intelligence Backend",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@router.get("/ready", summary="Service Readiness Probe")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Checks database connectivity and readiness for live traffic.
    """
    try:
        await db.execute(text("SELECT 1"))
        db_status = "CONNECTED"
    except Exception as e:
        db_status = f"DISCONNECTED: {str(e)}"

    return {
        "ready": db_status == "CONNECTED",
        "database": db_status,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
