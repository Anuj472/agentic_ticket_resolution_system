from app.workers.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="analytics_tasks.monitor_sla_breaches")
def monitor_sla_breaches():
    logger.info("[ANALYTICS] Checking SLA breaches")
    return {"checked": True}


@celery_app.task(name="analytics_tasks.generate_daily_report")
def generate_daily_report():
    logger.info("[ANALYTICS] Generating daily report")
    return {"generated": True}


@celery_app.task(name="analytics_tasks.cleanup_old_logs")
def cleanup_old_logs(days: int = 90):
    logger.info(f"[ANALYTICS] Cleaning logs older than {days} days")
    return {"cleaned": True}
