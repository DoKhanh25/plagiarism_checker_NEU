import hashlib
from flask_restful import Resource
import os
import requests
from ..config import Config
from flask import request, send_file
import logging
from ..utils import Utils
from .file_upload_route import SingleFileUpload
from .file_upload_route import SingleFileSearch
from .file_upload_route import MultipleFileSearch
from .file_management_route import FileScanList
from .file_upload_route import DownloadExcelSample
from .file_management_route import FileScanResult
from .file_search_ai_route import FileSearchAI, MetadataSearchAI

# Configure logger for this module
logger = logging.getLogger(__name__)



class FileList(Resource):
    def get(self):
        logger.info("FileList GET request received")
        try:
            search_term = request.args.get('search', '')
            search_type = request.args.get('type', 'name')  # 'name' or 'fulltext'

            logger.info(f"Search parameters - term: {search_term}, type: {search_type}")

            # Build the Solr query
            if search_term:
                search_term = Utils.escape_solr_text(search_term)
                if search_type == 'name':
                    # Search only in resource_name field
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
                return {"error": error_msg}, 500

            result = response.json()
            docs = result.get("response", {}).get("docs", [])

            # Transform the response into a more client-friendly format
            # Handle cases where fields might be arrays
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

            logger.info(f"Successfully retrieved {len(files)} unique files from Solr matching search criteria")
            return files, 200

        except requests.RequestException as e:
            error_msg = f"Không thể kết nối đến Solr: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}, 500
        except Exception as e:
            error_msg = f"Lỗi không mong đợi: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}, 500

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
                return {"error": error_msg}, 404

            file_name = file_path.split(file_id + "_")[-1]

            logger.info(f"Sending file: {file_name} from path: {file_path}")
            return send_file(file_path, as_attachment=True, download_name=file_name)

        except Exception as e:
            error_msg = f"Lỗi khi tải tệp: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}, 500

def get_files_in_directory(directory_path):
    try:
        files = os.listdir(directory_path)
        return [f for f in files if os.path.isfile(os.path.join(directory_path, f))]
    except Exception as e:
        logger.error(f"Error reading directory {directory_path}: {str(e)}")
        return []



def initialize_routes(api):
    api.add_resource(FileList, '/api/files')
    api.add_resource(FileDownload, '/api/files/download/<string:file_id>')
    #Refactoring Route
    api.add_resource(SingleFileUpload, '/api/file-upload')
    api.add_resource(SingleFileSearch, '/api/file-search/single')
    api.add_resource(MultipleFileSearch, '/api/file-search/multiple')
    api.add_resource(FileScanList, '/api/file-scan-list')
    api.add_resource(DownloadExcelSample, '/api/download-excel-sample')
    api.add_resource(FileScanResult, '/api/file-scan-result')
    api.add_resource(FileSearchAI, '/api/file-search/ai/ask')
    api.add_resource(MetadataSearchAI, '/api/file-search/ai/metadata')


