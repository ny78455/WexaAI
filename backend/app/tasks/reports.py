# Placeholder for scheduled report generation tasks
from celery_app import celery_app
import structlog

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.reports.generate_report")
def generate_report(org_id: str, dashboard_id: str, recipients: list[str]):
    logger.info("report.scheduled", org_id=org_id, dashboard_id=dashboard_id, recipients=recipients)
    # TODO: Render dashboard as PDF/PNG and email
