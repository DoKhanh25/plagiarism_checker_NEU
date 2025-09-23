import logging
from flask import request
from flask_restful import Resource
from ..services.database_service import DatabaseService
logger = logging.getLogger(__name__)

class FileScanResult(Resource):
    def __init__(self):
        self.db_service = DatabaseService()

    def get(self):
        try:
            scan_status_id = int(request.args.get('scan_status_id'))
            # Validate scan_status_id
            if not scan_status_id or scan_status_id <= 0:
                raise ValueError("ID quét không hợp lệ")

            scan_result = self.db_service.get_scan_result_by_scan_status_id(scan_status_id)

            if not scan_result:
                return {
                    "status": 0,
                    "data": None,
                    "message": "Không tìm thấy lịch sử quét cho tài liệu này"
                }, 404

            return {
                "status": 1,
                "data": scan_result,
                "message": "Lấy lịch sử quét thành công"
            }, 200

        except ValueError as e:
            return {
                "status": 0,
                "data": None,
                "message": str(e)
            }, 400
        except Exception as e:
            logger.error(f"Error getting scan history: {str(e)}")
            return {
                "status": 0,
                "data": None,
                "message": str(e)
            }, 500


class FileScanList(Resource):
    def __init__(self):
        self.db_service = DatabaseService()

    def get(self):
        try:
            # Get query parameters with default values
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))
            if page < 1 or per_page < 1:
                raise ValueError("Page and per_page must be greater than 0")

            # Calculate offset
            offset = (page - 1) * per_page

            # Get documents with pagination
            documents = self.db_service.get_documents_with_scan_status(
                limit=per_page,
                offset=offset
            )

            return {
                "status": 1,
                "data": {
                    "items": documents,
                    "page": page,
                    "per_page": per_page,
                    "total": len(documents)
                },
                "message": "Lấy danh sách tài liệu thành công"
            }, 200

        except ValueError as e:
            return {
                "status": 0,
                "data": None,
                "message": "Tham số không hợp lệ"
            }, 400
        except Exception as e:
            logger.error(f"Error getting document list: {str(e)}")
            return {
                "status": 0,
                "data": None,
                "message": str(e)
            }, 500
