import logging


from app.extensions import celery
from app.processor.processor import OutboxEventUploadFileProcessor

logger = logging.getLogger(__name__)


@celery.task
def process_outbox_events(self) -> str:
    try:
        processor = OutboxEventUploadFileProcessor()
        processor.process_pending_events()
        return "Events processed"
    except Exception as e:
        logger.error(f"Failed to process outbox events: {e}")
        raise self.retry(countdown=60, exc=e)