import requests
import logging
import os
from flask import request
from flask_restful import Resource
from flask import send_file
from ..config import Config
from ..services.database_service import DatabaseService
logger = logging.getLogger(__name__)
from ..utils import Utils



def get_files_in_directory(directory_path):
    try:
        files = os.listdir(directory_path)
        return [f for f in files if os.path.isfile(os.path.join(directory_path, f))]
    except Exception as e:
        logger.error(f"Error reading directory {directory_path}: {str(e)}")
        raise Exception(f"Error reading directory {directory_path}: {str(e)}")

class FileList(Resource):
    def get(self):
        try:
            search_term = request.args.get('search', '')
            search_type = request.args.get('type', 'name')

            if search_term != '':
                search_term = Utils.escape_solr_text(search_term)
                if search_type == 'name':
                    query = f'resource_name:*{search_term}*'
                else:
                    query = f'{search_term}'
            else:
                query = '*:*'

            logger.info(f"Executing Solr query: {query}")

            # Query Solr for files
            response = requests.get(f"{Config.SOLR_URL}/query?q={query}&fl=id,resource_name,description&rows=1000")

            if response.status_code != 200:
                error_msg = "Không thể kết nối đến máy chủ Solr"
                logger.error(f"{error_msg}. Status code: {response.status_code}")
                return {
                    "status": 0,
                    "data": None,
                    "message": error_msg
                }, 500

            result = response.json()

            docs = result.get("response", {}).get("docs", [])


            files = []
            seen_ids = set()  # Track IDs we've already processed

            for doc in docs:
                # Get the ID value, handling both string and array cases
                doc_id = doc.get("id", "")
                if isinstance(doc_id, list) and doc_id:
                    doc_id = doc_id[0]

                # Skip duplicate IDs
                if doc_id in seen_ids:
                    continue
                seen_ids.add(doc_id)

                # Get resource_name, ensuring we have a string value
                resource_name = doc.get("resource_name", ["Unknown"])
                if isinstance(resource_name, list) and resource_name:
                    resource_name = resource_name[0]
                elif not isinstance(resource_name, str):
                    resource_name = "Unknown"

                # Get description, ensuring we have a string value
                description = doc.get("description", [""])
                if isinstance(description, list) and description:
                    description = description[0]
                elif not isinstance(description, str):
                    description = ""

                files.append({
                    "id": doc_id,
                    "name": resource_name,
                    "description": description
                })

            return {
                "status": 1,
                "data": files,
                "message": "Danh sách tệp tin đã được lấy thành công"
            }, 200

        except requests.RequestException as e:
            logger.error(f"Error connecting to Solr: {str(e)}")
            return {
                "status": 0,
                "data": None,
                "message": "Không thể kết nối đến máy chủ Solr"
            }, 500
        except Exception as e:
            logger.error(e)
            return {
                "status": 0,
                "data": None,
                "message": e
            }, 500


class FileDownload(Resource):
    def get(self, file_id):
        try:
            file_path = None
            files = get_files_in_directory(Config.ORIGINAL_FILE_DIR)
            for f in files:
                if f.startswith(file_id):
                    file_path = os.path.join(Config.ORIGINAL_FILE_DIR, f)
                    file_path.encode('utf-8').decode('utf-8')
                    file_path = os.path.abspath(file_path)
                    logger.info(f"Found file: {f} for id: {file_id}")
                    logger.info(f"File path: {file_path}")
                    break

            if not os.path.isfile(file_path):
                error_msg = f"Không tìm thấy tệp với ID {file_id}"
                logger.error(error_msg)
                return {
                    "status": 0,
                    "data": None,
                    "message": error_msg
                }, 404

            file_name = file_path.split(file_id + "_")[-1]

            logger.info(f"Sending file: {file_name} from path: {file_path}")
            return send_file(file_path, as_attachment=True, download_name=file_name)

        except Exception as e:
            error_msg = f"Lỗi khi tải tệp: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": 0,
                "data": None,
                "message": error_msg
            }, 500



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
