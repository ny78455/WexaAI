"""Celery Beat task: evaluate all active alert rules every 60s."""
import asyncio
from datetime import datetime, timedelta, timezone

from celery_app import celery_app
import structlog

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.alerts.evaluate_all_rules")
def evaluate_all_rules():
    asyncio.run(_evaluate())


async def _evaluate():
    from app.db.session import AsyncSessionLocal
    from app.repositories.alert import AlertRepository
    from app.repositories.event import EventRepository
    from app.db.models.alert import AlertStatus

    async with AsyncSessionLocal() as session:
        alert_repo = AlertRepository(session)
        event_repo = EventRepository(session)
        rules = await alert_repo.get_active_rules()

        for rule in rules:
            # Skip muted rules
            if rule.muted_until and rule.muted_until > datetime.now(timezone.utc):
                continue

            condition = rule.condition if isinstance(rule.condition, dict) else {}
            metric = condition.get("metric", "event_count")
            operator = condition.get("operator", ">")
            threshold = condition.get("threshold", 0)
            window_min = condition.get("window_minutes", 5)

            end = datetime.now(timezone.utc)
            start = end - timedelta(minutes=window_min)

            count = await event_repo.get_event_count(
                rule.organization_id, condition.get("event_name"), start, end
            )

            triggered = _evaluate_condition(count, operator, threshold)

            if triggered and rule.status != AlertStatus.TRIGGERED:
                await alert_repo.update(rule.id, status=AlertStatus.TRIGGERED)
                await alert_repo.add_history(rule.id, float(count), f"{metric} = {count} ({operator} {threshold})")
                await _send_notifications(rule, float(count))
                logger.info("alert.triggered", rule_id=str(rule.id), value=count)
            elif not triggered and rule.status == AlertStatus.TRIGGERED:
                await alert_repo.update(rule.id, status=AlertStatus.RESOLVED)
                logger.info("alert.resolved", rule_id=str(rule.id))

        await session.commit()


def _evaluate_condition(value: float, operator: str, threshold: float) -> bool:
    ops = {">": value > threshold, "<": value < threshold, ">=": value >= threshold, "<=": value <= threshold, "==": value == threshold}
    return ops.get(operator, False)


async def _send_notifications(rule, value: float):
    channels = rule.notification_channels if isinstance(rule.notification_channels, list) else []
    for channel in channels:
        ch_type = channel.get("type") if isinstance(channel, dict) else None
        if ch_type == "webhook":
            await _send_webhook(channel.get("config", {}), rule, value)
        elif ch_type == "email":
            logger.info("alert.email", rule_id=str(rule.id), email=channel.get("config", {}).get("email"))
        # in_app is handled via WebSocket


async def _send_webhook(config: dict, rule, value: float):
    import httpx
    url = config.get("url")
    if not url:
        return
    payload = {
        "alert": rule.name,
        "severity": rule.severity.value if hasattr(rule.severity, "value") else str(rule.severity),
        "value": value,
        "triggered_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(url, json=payload)
    except Exception as e:
        logger.error("webhook.failed", url=url, error=str(e))
