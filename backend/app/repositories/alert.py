import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.alert import AlertRule, AlertHistory, AlertStatus


class AlertRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, rule_id: uuid.UUID, org_id: uuid.UUID) -> AlertRule | None:
        result = await self.db.execute(
            select(AlertRule).where(
                AlertRule.id == rule_id,
                AlertRule.organization_id == org_id,
                AlertRule.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def list_org_rules(self, org_id: uuid.UUID) -> list[AlertRule]:
        result = await self.db.execute(
            select(AlertRule)
            .where(AlertRule.organization_id == org_id, AlertRule.is_deleted == False)
            .order_by(AlertRule.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_active_rules(self) -> list[AlertRule]:
        result = await self.db.execute(
            select(AlertRule).where(
                AlertRule.status.in_([AlertStatus.ACTIVE, AlertStatus.TRIGGERED]),
                AlertRule.is_deleted == False
            )
        )
        return list(result.scalars().all())

    async def create(self, org_id: uuid.UUID, user_id: uuid.UUID, **kwargs) -> AlertRule:
        rule = AlertRule(organization_id=org_id, created_by=user_id, **kwargs)
        self.db.add(rule)
        await self.db.flush()
        await self.db.refresh(rule)
        return rule

    async def update(self, rule_id: uuid.UUID, **kwargs) -> None:
        await self.db.execute(update(AlertRule).where(AlertRule.id == rule_id).values(**kwargs))

    async def delete(self, rule_id: uuid.UUID) -> None:
        await self.db.execute(update(AlertRule).where(AlertRule.id == rule_id).values(is_deleted=True))

    async def add_history(self, rule_id: uuid.UUID, triggered_value: float, message: str) -> AlertHistory:
        entry = AlertHistory(
            rule_id=rule_id,
            triggered_at=datetime.now(timezone.utc),
            triggered_value=triggered_value,
            message=message,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def get_history(self, rule_id: uuid.UUID, limit: int = 50) -> list[AlertHistory]:
        result = await self.db.execute(
            select(AlertHistory)
            .where(AlertHistory.rule_id == rule_id)
            .order_by(AlertHistory.triggered_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
