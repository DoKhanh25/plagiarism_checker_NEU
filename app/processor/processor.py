from ..models import OutboxEvent
from ..database import db
from ..services import SolrService, FileService
import json
import logging
import base64
logger = logging.getLogger(__name__)

"""
Author: Khanh Trong Do
Created: 24-09-2025
Description: Processes outbox events related to file uploads and interacts with Solr and file storage services.
"""
class OutboxEventUploadFileProcessor:
    def __init__(self):
        self.solr_service = SolrService()

    def process_pending_events(self):
        events = OutboxEvent.query.filter_by(processed=False, failed=False).limit(100).all()

        for event in events:
            try:
                self._handle_event(event)
                event.processed = True
                event.failed = False
                event.error_message = None
                db.session.commit()
            except Exception as e:
                event.retry_count += 1
                if event.retry_count >= event.max_retries:
                    logger.error(f"Max retries exceeded for event {event.id}: {e}")
                    event.processed = True
                    event.failed = True
                    event.error_message = str(e)
                else:
                    event.error_message = str(e)
                db.session.commit()

    def _handle_event(self, event: OutboxEvent):
        payload = json.loads(event.payload)

        if event.aggregate_type == "FILE" and event.event_type == "UPLOADED":
            self._handle_file_upload(payload)


    def _handle_file_upload(self, data):
        file_path = data["file_path"]
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
        except FileNotFoundError:
            raise Exception(f"File not found: {file_path}")

        # Upload to Solr
        response = self.solr_service.upload_file(
            filename=data["filename"],
            sha1_file=data["sha1_file"],
            content=content,
            mimetype=data["mimetype"],
            description=data["description"]
        )

        if response.status_code != 200:
            raise Exception("Solr upload failed")

    def _handle_cleanup(self, data):
        # Cleanup operations
        if data.get('cleanup_solr'):
            self.solr_service.delete_file(data['sha1_file'])
        if data.get('cleanup_file'):
            FileService.delete_file(data['file_path'])


