import json
from typing import Dict, Any
from ..models import OutboxEvent
from datetime import datetime


class OutboxEventPublisher:
    def __init__(self, db_service):
        self.db_service = db_service

    def publish_event(self, event_type: str, aggregate_type: str, aggregate_id: str, payload: Dict[str, Any]):
        event = OutboxEvent(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=json.dumps(payload),
            timestamp=datetime.now()
        )
        self.db_service.db.session.add(event)
        self.db_service.db.session.commit()
