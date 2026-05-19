import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import CurrentUser, require_min_role
from app.db.models.user import UserRole
from app.repositories.alert import AlertRepository
from app.schemas.alert import AlertRuleCreate, AlertRuleUpdate, AlertRuleOut, AlertHistoryOut
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.post("/", response_model=AlertRuleOut, status_code=201)
async def create_alert(
    data: AlertRuleCreate,
    current_user = Depends(require_min_role(UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    repo = AlertRepository(db)
    rule = await repo.create(
        org_id=current_user.organization_id,
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        condition=data.condition.model_dump(),
        notification_channels=[c.model_dump() for c in data.notification_channels],
        severity=data.severity,
    )
    return AlertRuleOut.model_validate(rule)


@router.get("/", response_model=list[AlertRuleOut])
async def list_alerts(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    repo = AlertRepository(db)
    return [AlertRuleOut.model_validate(r) for r in await repo.list_org_rules(current_user.organization_id)]


@router.get("/{rule_id}", response_model=AlertRuleOut)
async def get_alert(rule_id: uuid.UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    repo = AlertRepository(db)
    rule = await repo.get_by_id(rule_id, current_user.organization_id)
    if not rule:
        raise NotFoundError("Alert rule not found")
    return AlertRuleOut.model_validate(rule)


@router.patch("/{rule_id}", response_model=AlertRuleOut)
async def update_alert(
    rule_id: uuid.UUID,
    data: AlertRuleUpdate,
    current_user = Depends(require_min_role(UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    repo = AlertRepository(db)
    rule = await repo.get_by_id(rule_id, current_user.organization_id)
    if not rule:
        raise NotFoundError("Alert rule not found")
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if "condition" in updates and hasattr(updates["condition"], "model_dump"):
        updates["condition"] = updates["condition"].model_dump()
    if "notification_channels" in updates:
        updates["notification_channels"] = [
            c.model_dump() if hasattr(c, "model_dump") else c for c in updates["notification_channels"]
        ]
    await repo.update(rule_id, **updates)
    updated = await repo.get_by_id(rule_id, current_user.organization_id)
    return AlertRuleOut.model_validate(updated)


@router.delete("/{rule_id}", status_code=204)
async def delete_alert(
    rule_id: uuid.UUID,
    current_user = Depends(require_min_role(UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    repo = AlertRepository(db)
    rule = await repo.get_by_id(rule_id, current_user.organization_id)
    if not rule:
        raise NotFoundError("Alert rule not found")
    await repo.delete(rule_id)


@router.get("/{rule_id}/history", response_model=list[AlertHistoryOut])
async def get_alert_history(
    rule_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    repo = AlertRepository(db)
    rule = await repo.get_by_id(rule_id, current_user.organization_id)
    if not rule:
        raise NotFoundError("Alert rule not found")
    history = await repo.get_history(rule_id)
    return [AlertHistoryOut.model_validate(h) for h in history]
