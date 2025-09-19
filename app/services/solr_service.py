import re
import requests
import logging
from ..config import Config

logger = logging.getLogger(__name__)


class SolrService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SolrService, cls).__new__(cls)
            cls._instance.base_url = Config.SOLR_URL
        return cls._instance

    @staticmethod
    def escape_solr_text(text):
        return re.sub(r'([+\-&|!(){}\[\]^"\'~*?:/])', r'\\\1', text)

    def extract_text(self, filename, content, mimetype) -> requests.Response:
        try:
            data = {
                "extractOnly": "true",
                "extractFormat": "text",
                "literal.resource_name": filename
            }
            files_data = {"file": (filename, content, mimetype)}

            response = requests.post(f"{self.base_url}/update/extract", data=data, files=files_data)
            return response
        except requests.RequestException as e:
            logger.error(f"Failed to extract text from file: {str(e)}")
            raise Exception(e)

    def upload_file(self, sha1_file, filename, content, mimetype, description, overwrite) -> requests.Response:
        try:
            data = {
                "literal.id": sha1_file,
                "commitWithin": 5000,
                "literal.description": description,
                "literal.resource_name": filename,
                "overwrite": overwrite
            }
            files_data = {"file": (filename, content, mimetype)}

            response = requests.post(f"{self.base_url}/update/extract", data=data, files=files_data)
            return response
        except requests.RequestException as e:
            raise Exception(e)

    def search_text(self, sample, rows=1):
        data = {
            "q": f'"{self.escape_solr_text(sample)}"',
            "fl": "id,resource_name,description",
            "rows": rows
        }
        response = requests.post(f"{self.base_url}/query", data=data)
        return response.json() if response.status_code == 200 else None


    # Commit changes to Solr
    #commit_status: str = "true" or "false"
    def commit_changes(self, commit_status: str = "true") -> bool:
        try:
            response = requests.post(f"{self.base_url}/update", data={"commit": commit_status})
            return response.status_code == 200
        except requests.RequestException as e:
            logger.error(f"Failed to commit changes to Solr: {str(e)}")
            raise Exception(e)

    def delete_file(self, sha1_file: str) -> bool:
        try:
            # Format the delete request properly
            data = '<delete><id>' + sha1_file + '</id></delete>'
            headers = {'Content-type': 'text/xml; charset=utf-8'}

            response = requests.post(
                f"{self.base_url}/update",
                data=data,
                headers=headers
            )

            if response.status_code == 200:
                logger.info(f"Successfully deleted file with id {sha1_file} from Solr")
                return True
            else:
                logger.error(f"Failed to delete file from Solr. Status code: {response.status_code}")
                return False

        except requests.RequestException as e:
            logger.error(f"Failed to delete file from Solr: {str(e)}")
            raise Exception(f"Error deleting file from Solr: {str(e)}")