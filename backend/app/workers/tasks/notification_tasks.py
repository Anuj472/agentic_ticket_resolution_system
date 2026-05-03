from app.workers.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="notification_tasks.send_ticket_created")
def send_ticket_created(ticket_id: str, recipient_email: str):
    logger.info(f"[NOTIFY] Created: {ticket_id} → {recipient_email}")
    return {"sent": False, "note": "Phase 5 pending"}


@celery_app.task(name="notification_tasks.send_sla_breach_alert")
def send_sla_breach_alert(ticket_id: str, agent_email: str):
    logger.info(f"[ALERT] SLA breach: {ticket_id} → {agent_email}")
    return {"sent": False}


@celery_app.task(name="notification_tasks.send_email")
def send_email(to: str, subject: str, body: str):
    logger.info(f"[EMAIL] To: {to} | {subject}")
    return {"sent": False}
