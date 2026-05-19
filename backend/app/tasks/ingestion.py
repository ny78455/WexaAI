"""Async event ingestion task — processes events from queue into PostgreSQL."""
import asyncio
from datetime import datetime, timezone
import uuid

from celery_app import celery_app
import structlog

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.ingestion.process_events_task", bind=True, max_retries=3, default_retry_delay=5)
def process_events_task(self, events_data: list[dict]):
    try:
        asyncio.run(_insert_events(events_data))
    except Exception as exc:
        logger.error("ingestion.failed", error=str(exc), count=len(events_data))
        raise self.retry(exc=exc)


async def _insert_events(events_data: list[dict]):
    from app.db.session import AsyncSessionLocal
    from app.db.models.event import Event

    async with AsyncSessionLocal() as session:
        objs = []
        for e in events_data:
            ts = e.get("timestamp")
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            objs.append(Event(
                organization_id=uuid.UUID(e["org_id"]),
                event_name=e["event_name"],
                user_id=e.get("user_id"),
                session_id=e.get("session_id"),
                properties=e.get("properties", {}),
                timestamp=ts or datetime.now(timezone.utc),
                source=e.get("source", "api"),
            ))
        session.add_all(objs)
        await session.commit()
        logger.info("ingestion.complete", count=len(objs))
