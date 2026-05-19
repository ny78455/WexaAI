import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import CurrentUser, get_org_from_api_key, require_min_role
from app.db.models.user import UserRole
from app.services.event import EventService, APIKeyService
from app.schemas.event import (
    EventIn, EventBatchIn, IngestionResponse,
    APIKeyCreate, APIKeyOut, APIKeyCreated, EventOut,
)

router = APIRouter(prefix="/events", tags=["Events"])
api_keys_router = APIRouter(prefix="/api-keys", tags=["API Keys"])


# ── Event Ingestion ────────────────────────────────────────────────────────────

@router.post("/", response_model=IngestionResponse, status_code=202)
async def ingest_event(
    event: EventIn,
    org_id: str = Depends(get_org_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    svc = EventService(db)
    count = await svc.ingest_single(org_id, event)
    return IngestionResponse(accepted=count, message="Event queued for processing")


@router.post("/batch", response_model=IngestionResponse, status_code=202)
async def ingest_batch(
    batch: EventBatchIn,
    org_id: str = Depends(get_org_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    svc = EventService(db)
    count = await svc.ingest_batch(org_id, batch)
    return IngestionResponse(accepted=count, message=f"{count} events queued for processing")


@router.post("/csv-upload", response_model=IngestionResponse, status_code=202)
async def ingest_csv(
    file: UploadFile = File(...),
    org_id: str = Depends(get_org_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith(".csv"):
        from app.core.exceptions import ValidationError
        raise ValidationError("Only CSV files are accepted")
    svc = EventService(db)
    count = await svc.ingest_csv(org_id, file)
    return IngestionResponse(accepted=count, message=f"{count} events queued from CSV")


@router.get("/recent", response_model=list[EventOut])
async def get_recent_events(
    limit: int = Query(default=100, le=1000),
    current_user = Depends(),
    db: AsyncSession = Depends(get_db),
):
    svc = EventService(db)
    events = await svc.get_recent(current_user.organization_id, limit)
    return [EventOut.model_validate(e) for e in events]


# ── API Key Management ────────────────────────────────────────────────────────

@api_keys_router.post("/", response_model=APIKeyCreated, status_code=201)
async def create_api_key(
    data: APIKeyCreate,
    current_user = Depends(require_min_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    svc = APIKeyService(db)
    key, raw = await svc.create_key(current_user.organization_id, data)
    return APIKeyCreated(**APIKeyOut.model_validate(key).model_dump(), raw_key=raw)


@api_keys_router.get("/", response_model=list[APIKeyOut])
async def list_api_keys(
    current_user = Depends(require_min_role(UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    svc = APIKeyService(db)
    return [APIKeyOut.model_validate(k) for k in await svc.list_keys(current_user.organization_id)]


@api_keys_router.delete("/{key_id}", status_code=204)
async def revoke_api_key(
    key_id: uuid.UUID,
    current_user = Depends(require_min_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    svc = APIKeyService(db)
    await svc.revoke(current_user.organization_id, key_id)
