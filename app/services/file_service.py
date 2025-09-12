import os
import hashlib
import logging
from ..config import Config

logger = logging.getLogger(__name__)

class FileService:
    @staticmethod
    def calculate_sha1(content) -> str:
        sha1_hash = hashlib.sha1()
        sha1_hash.update(content)
        return sha1_hash.hexdigest()

    @staticmethod
    def save_original_file(file, sha1, filename) -> str:
        try:
            os.makedirs(Config.ORIGINAL_FILE_DIR, exist_ok=True)
            file_path = os.path.join(Config.ORIGINAL_FILE_DIR, f"{sha1}_{filename}")

            if not os.path.isfile(file_path):
                content = file.read()  # IOError possible
                with open(file_path, "wb") as f:
                    f.write(content)  # IOError possible
                file.seek(0)  # IOError possible
                logger.info(f"File saved locally as {file_path}")
            else:
                logger.info(f"File already exists locally at {file_path}")
            return file_path
        except IOError as e:
            error_msg = f"IO error while saving file: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error saving original file: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    @staticmethod
    def delete_file(file_path: str):
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                logger.info(f"File deleted successfully: {file_path}")
            else:
                logger.warning(f"File not found for deletion: {file_path}")
        except OSError as e:
            error_msg = f"OS error while deleting file: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error deleting file: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    @staticmethod
    def save_metadata(sha1_file, filename, timestamp):
        metadata_path = os.path.join(Config.FILE_DIR, f"{sha1_file}_{timestamp}_scanned.meta")
        with open(metadata_path, "w", encoding='utf-8') as f:
            f.write(filename)
        logger.debug(f"Metadata file created: {metadata_path}")