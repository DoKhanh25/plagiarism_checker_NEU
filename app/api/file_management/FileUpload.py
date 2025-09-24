import re
import logging
import requests
from flask import request
from flask_restful import Resource
from ...config import Config
from ...models import OutboxEvent
from ...services.file_service import FileService
from ...services.solr_service import SolrService
from ...services.database_service import DatabaseService

import pysolr

logger = logging.getLogger(__name__)

"""
Author: Khanh Trong Do
Created: 20-06-2025
Description: Provides API endpoints for file upload functionality.
"""
class SingleFileUpload(Resource):
    def __init__(self):
        self.solr_service = SolrService()
        self.db_service = DatabaseService()

    def post(self):
        description = request.form.get('description', '')
        research_name = request.form.get('researchName', '')
        author = request.form.get('author', '')
        file = request.files.get('file')


        if not file:
            return {
                "status": 0,
                "data": None,
                "message": "Không có tệp nào được cung cấp"
            }, 400

        if not file.filename or research_name == '' or description == '':
            return {
                "status": 0,
                "data": None,
                "message": "Nhập thiếu dữ liệu: tên nghiên cứu, mô tả hoặc tên tệp"
            }, 400


        content = file.read()
        sha1_file = FileService.calculate_sha1(content)
        file.seek(0)

        # Check if document already exists in database
        existing_document = self.db_service.get_document_by_hash(sha1_file)

        if existing_document:
            msg = f"Tài liệu {file.filename} đã tồn tại trong cơ sở dữ liệu"
            return {"status": 0, "data": None, "message": msg}, 400

        file_path = None

        try:
            file_path = FileService.save_original_file(file, sha1_file, file.filename)

            db = self.db_service.db
            with db.session.begin():
                document = self.db_service.create_document(
                    research_name=research_name,
                    file_name=file.filename,
                    file_hash=sha1_file,
                    description=description,
                    mimetype=file.mimetype,
                    file_size=len(content),
                    author=author,
                    file_path=file_path
                )

                outbox_payload = {
                    "event": "FILE_UPLOADED",
                    "document_id": document.id,
                    "file_hash": sha1_file,
                    "file_path": file_path,
                    "filename": file.filename,
                    "mimetype": file.mimetype,
                    "description": description,
                    "research_name": research_name,
                    "author": author,
                    "size": len(content),
                    "content": content
                }

                outbox_event = OutboxEvent(
                    aggregate_type="FILE",
                    aggregate_id=document.id,
                    event_type="UPLOADED",
                    payload=json.dumps(outbox_payload),
                    processed=False,
                    failed=False,
                    error_message=None
                )

                db.session.add(outbox_event)

            logger.info(f"Queued file {file.filename} (hash={sha1_file}) for async processing via outbox event {outbox_event.id}")

            return {
                "status": 1,
                "data": {
                    "fileName": file.filename,
                    "hash": sha1_file,
                    "outboxEventId": outbox_event.id
                },
                "message": "Đã nhận tệp. Sẽ xử lý bất đồng bộ."
            }, 202

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            # Rollback handled by context manager; cleanup file if DB failed
            if file_path:
                try:
                    FileService.delete_file(file_path)
                except Exception as cleanup_err:
                    logger.error(f"Cleanup failed: {cleanup_err}")
            return {
                "status": 0,
                "data": None,
                "message": "Lỗi trong khi xử lý tệp"
            }, 500
