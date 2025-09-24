from app.processor.processor import OutboxEventUploadFileProcessor
import logging
from make_celery import celery

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=4)
def process_outbox_events(self) -> str:
    try:
        processor = OutboxEventUploadFileProcessor()
        processor.process_pending_events()
        return "Events processed"
    except Exception as e:
        logger.error(f"Failed to process outbox events: {e}")
        raise self.retry(countdown=60, exc=e)