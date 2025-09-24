from flask_restful import Resource
import os
from ...config import Config
from flask import request, send_file
import logging


logger = logging.getLogger(__name__)

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