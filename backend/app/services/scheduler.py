from datetime import datetime, date, timedelta
from sqlalchemy import select, update
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.models.maintenance import Maintenance
from app.models.contract import Contract
from app.models.iot import SensorDevice
from app.models.alert import Alert
from app.models.asset import Asset
from app.services.iot_engine import IoTEngine
from app.services.contracts import ContractService

class AurumBackgroundScheduler:
    """
    Periodic background jobs for operational health and compliance.
    """

    @classmethod
    async def run_pm_overdue_check(cls):
        """
        Marks SCHEDULED PMs whose scheduled_date < today as OVERDUE and generates alerts.
        """
        logger.info("Running scheduled job: PM overdue check...")
        today = date.today()
        async with AsyncSessionLocal() as session:
            try:
                stmt = select(Maintenance).where(
                    Maintenance.status == "SCHEDULED",
                    Maintenance.scheduled_date < today
                )
                res = await session.execute(stmt)
                overdue_pms = res.scalars().all()

                for pm in overdue_pms:
                    pm.status = "OVERDUE"
                    # Check existing alert
                    al_stmt = select(Alert).where(Alert.asset_id == pm.asset_id, Alert.type == "OVERDUE_PM", Alert.status == "ACTIVE")
                    al_res = await session.execute(al_stmt)
                    if not al_res.scalar_one_or_none():
                        session.add(Alert(
                            type="OVERDUE_PM",
                            severity="HIGH",
                            asset_id=pm.asset_id,
                            title="Overdue Maintenance Alert",
                            message=f"Scheduled PM '{pm.pm_type}' is past due date ({pm.scheduled_date}).",
                            reason="Preventive maintenance milestone missed",
                            recommended_action="Dispatch field technician immediately",
                            status="ACTIVE"
                        ))

                await session.commit()
                logger.info(f"PM overdue check complete. {len(overdue_pms)} records updated to OVERDUE.")
            except Exception as e:
                logger.error(f"Error in PM overdue check: {e}")
                await session.rollback()

    @classmethod
    async def run_contract_expiry_check(cls):
        """
        Checks for contracts expiring within 30 and 15 days, updating renewal risk and status.
        """
        logger.info("Running scheduled job: Contract expiry check...")
        today = date.today()
        async with AsyncSessionLocal() as session:
            try:
                stmt = select(Contract).where(Contract.status.in_(["ACTIVE", "EXPIRING_SOON"]))
                res = await session.execute(stmt)
                contracts = res.scalars().all()

                for c in contracts:
                    days_left = (c.end_date - today).days
                    if days_left <= 0:
                        c.status = "EXPIRED"
                    elif days_left <= 60:
                        c.status = "EXPIRING_SOON"
                        if days_left <= 15:
                            c.renewal_risk = "CRITICAL"
                        elif days_left <= 30:
                            c.renewal_risk = "HIGH"

                await session.commit()
            except Exception as e:
                logger.error(f"Error in contract expiry check: {e}")
                await session.rollback()

    @classmethod
    async def run_sensor_freshness_check(cls):
        """
        Evaluates sensor last_seen timestamps and marks sensors as DELAYED, STALE, or OFFLINE.
        """
        logger.info("Running scheduled job: Sensor freshness check...")
        async with AsyncSessionLocal() as session:
            try:
                stmt = select(SensorDevice)
                res = await session.execute(stmt)
                sensors = res.scalars().all()

                for s in sensors:
                    new_status = IoTEngine.determine_sensor_status(s.last_seen)
                    if s.status != new_status:
                        s.status = new_status

                await session.commit()
            except Exception as e:
                logger.error(f"Error in sensor freshness check: {e}")
                await session.rollback()
