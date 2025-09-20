import re
import pysolr
import requests
import logging
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

from requests.adapters import HTTPAdapter
from urllib3 import Retry
from ..utils import Utils
from ..config import Config

logger = logging.getLogger(__name__)


class SolrService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SolrService, cls).__new__(cls)
            cls._instance.base_url = Config.SOLR_URL
        return cls._instance

    def __init__(self):
        self.session = requests.Session()

        retry_strategy = Retry(
            total=3,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504]
        )

        adapter = HTTPAdapter(
            pool_connections=Config.POOL_CONNECTIONS,
            pool_maxsize=Config.POOL_MAXSIZE,
            max_retries=retry_strategy
        )

        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Enable keep-alive connections
        self.session.headers.update({
            'Connection': 'keep-alive',
            'Keep-Alive': f'timeout={getattr(Config, "CONNECTION_KEEP_ALIVE_TIMEOUT", 120)}, max=1000'
        })

        self.solr_client = pysolr.Solr(
            Config.SOLR_URL,
            session=self.session,
            timeout=getattr(Config, "SOLR_TIMEOUT", 60)
        )

    @staticmethod
    def escape_solr_text(text):
        return re.sub(r'([+\-&|!(){}\[\]^"\'~*?:/])', r'\\\1', text)



    def _extract_field_value(self, field_value):
        if isinstance(field_value, list):
            return field_value[0] if field_value else ""
        return field_value or ""

    def search_samples_optimized(self, samples):
        """Search samples individually with accurate results"""
        results = {}

        for idx, sample in samples:
            try:
                escaped_sample = Utils.escape_solr_text(sample)
                query = f'"{escaped_sample}"'
                # Use pysolr with session reuse for individual searches
                search_results = self.solr_client.search(
                    query,
                    fl="id,resource_name,description",
                    rows=1
                )
                if search_results:
                    results[idx] = [{
                        "id": doc["id"],
                        "resource_name": self._extract_field_value(doc.get("resource_name", "Unknown")),
                        "description": self._extract_field_value(doc.get("description", ""))
                    } for doc in search_results]

            except Exception as e:
                logger.warning(f"Search failed for sample {idx}: {e}")
                continue

        return results

    def extract_text(self, filename, content, mimetype) -> requests.Response:
        try:
            data = {
                "extractOnly": "true",
                "extractFormat": "text",
                "literal.resource_name": filename,
                "capture": "body"
            }
            files_data = {"file": (filename, content, mimetype)}

            return self.session.post(f"{self.base_url}/update/extract", data=data, files=files_data)
        except requests.RequestException as e:
            logger.error(f"Failed to extract text from file: {str(e)}")
            raise Exception(e)

    def upload_file(self, sha1_file, filename, content, mimetype, description, overwrite="false") -> requests.Response:
        try:
            data = {
                "literal.id": sha1_file,
                "commitWithin": 5000,
                "literal.description": description,
                "literal.resource_name": filename,
                "overwrite": overwrite
            }
            files_data = {"file": (filename, content, mimetype)}

            # response = requests.post(f"{self.base_url}/update/extract", data=data, files=files_data)
            return self.session.post(f"{self.base_url}/update/extract", data=data, files=files_data)
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
            self.solr_client.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to commit changes to Solr: {str(e)}")
            raise Exception(e)

    def delete_file(self, sha1_file: str) -> bool:
        try:
            # Format the delete request properly
            self.solr_client.delete(id=sha1_file)
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from Solr: {str(e)}")
            raise Exception(f"Error deleting file from Solr: {str(e)}")


