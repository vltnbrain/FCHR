"""
Audit service for logging system events
"""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import structlog

from app.models import AuditEvent

logger = structlog.get_logger(__name__)


class AuditService:
    """Service for audit logging and history tracking"""

    @staticmethod
    async def log_event(
        db: AsyncSession,
        entity_type: str,
        entity_id: int,
        action: str,
        actor_user_id: int = None,
        payload: Dict[str, Any] = None
    ) -> int:
        """Log an audit event"""
        audit_event = AuditEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_user_id=actor_user_id,
            payload_json=payload or {}
        )

        db.add(audit_event)
        await db.commit()
        await db.refresh(audit_event)

        logger.info(
            "Audit event logged",
            event_id=audit_event.id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_user_id=actor_user_id
        )

        return audit_event.id

    @staticmethod
    async def get_entity_history(
        db: AsyncSession,
        entity_type: str,
        entity_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get audit history for an entity"""
        query = select(AuditEvent).where(
            AuditEvent.entity_type == entity_type,
            AuditEvent.entity_id == entity_id
        ).order_by(desc(AuditEvent.created_at)).limit(limit)

        result = await db.execute(query)
        events = result.scalars().all()

        history = []
        for event in events:
            history.append({
                "id": event.id,
                "action": event.action,
                "actor_user_id": event.actor_user_id,
                "payload": event.payload_json,
                "created_at": event.created_at.isoformat(),
                "entity_type": event.entity_type,
                "entity_id": event.entity_id
            })

        return history

    @staticmethod
    async def get_recent_activity(
        db: AsyncSession,
        limit: int = 100,
        entity_type: str = None
    ) -> List[Dict[str, Any]]:
        """Get recent audit activity across the system"""
        query = select(AuditEvent)

        if entity_type:
            query = query.where(AuditEvent.entity_type == entity_type)

        query = query.order_by(desc(AuditEvent.created_at)).limit(limit)

        result = await db.execute(query)
        events = result.scalars().all()

        activity = []
        for event in events:
            activity.append({
                "id": event.id,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "action": event.action,
                "actor_user_id": event.actor_user_id,
                "payload": event.payload_json,
                "created_at": event.created_at.isoformat()
            })

        return activity

    @staticmethod
    async def get_user_activity(
        db: AsyncSession,
        user_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get audit activity for a specific user"""
        query = select(AuditEvent).where(
            AuditEvent.actor_user_id == user_id
        ).order_by(desc(AuditEvent.created_at)).limit(limit)

        result = await db.execute(query)
        events = result.scalars().all()

        activity = []
        for event in events:
            activity.append({
                "id": event.id,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "action": event.action,
                "payload": event.payload_json,
                "created_at": event.created_at.isoformat()
            })

        return activity
