import uuid
import csv
import io
from datetime import datetime, timezone
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_api_key
from app.core.exceptions import NotFoundError, AuthorizationError
from app.repositories.event import EventRepository, APIKeyRepository
from app.schemas.event import EventIn, EventBatchIn, APIKeyCreate
from app.tasks.ingestion import process_events_task
import structlog

logger = structlog.get_logger()


class EventService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.event_repo = EventRepository(db)

    async def ingest_single(self, org_id: str, event: EventIn) -> int:
        return await self._queue_events(org_id, [event])

    async def ingest_batch(self, org_id: str, batch: EventBatchIn) -> int:
        return await self._queue_events(org_id, batch.events)

    async def _queue_events(self, org_id: str, events: list[EventIn]) -> int:
        events_data = []
        for e in events:
            events_data.append({
                "org_id": org_id,
                "event_name": e.event_name,
                "user_id": e.user_id,
                "session_id": e.session_id,
                "properties": e.properties,
                "timestamp": (e.timestamp or datetime.now(timezone.utc)).isoformat(),
                "source": "api",
            })
        # Enqueue to Celery
        process_events_task.delay(events_data)
        logger.info("events.queued", org_id=org_id, count=len(events_data))
        return len(events_data)

    async def ingest_csv(self, org_id: str, file: UploadFile) -> int:
        content = await file.read()
        reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
        events = []
        for row in reader:
            events.append({
                "org_id": org_id,
                "event_name": row.get("event_name", "csv_import"),
                "user_id": row.get("user_id"),
                "session_id": row.get("session_id"),
                "properties": {k: v for k, v in row.items() if k not in ("event_name", "user_id", "session_id", "timestamp")},
                "timestamp": row.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                "source": "csv",
            })
            if len(events) >= 1000:
                process_events_task.delay(events)
                events = []
        if events:
            process_events_task.delay(events)
        return len(events)

    async def get_recent(self, org_id: uuid.UUID, limit: int = 100):
        return await self.event_repo.get_recent_events(org_id, limit)


class APIKeyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = APIKeyRepository(db)

    async def create_key(self, org_id: uuid.UUID, data: APIKeyCreate):
        raw_key, key_hash = generate_api_key()
        key_prefix = raw_key[:12]
        key = await self.repo.create(org_id, data.name, key_hash, key_prefix)
        return key, raw_key

    async def list_keys(self, org_id: uuid.UUID):
        return await self.repo.get_org_keys(org_id)

    async def revoke(self, org_id: uuid.UUID, key_id: uuid.UUID):
        keys = await self.repo.get_org_keys(org_id)
        if not any(str(k.id) == str(key_id) for k in keys):
            raise NotFoundError("API key not found")
        await self.repo.revoke(key_id)
