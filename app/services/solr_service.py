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
            pool_connections=20,
            pool_maxsize=20,
            max_retries=retry_strategy
        )

        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Enable keep-alive connections
        self.session.headers.update({
            'Connection': 'keep-alive',
            'Keep-Alive': 'timeout=60, max=100'
        })

        self.solr_client = pysolr.Solr(Config.SOLR_URL, session=self.session, timeout=30)

    @staticmethod
    def escape_solr_text(text):
        return re.sub(r'([+\-&|!(){}\[\]^"\'~*?:/])', r'\\\1', text)


    async def async_search_samples(self, samples, sha1_file, concurrent_limit=20):
        """Async individual searches with connection pooling"""
        results = {}
        semaphore = asyncio.Semaphore(concurrent_limit)

        connector = aiohttp.TCPConnector(
            limit=50,
            limit_per_host=20,
            ttl_dns_cache=300,
            use_dns_cache=True
        )

        timeout = aiohttp.ClientTimeout(total=30, connect=10)

        async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'Connection': 'keep-alive'}
        ) as session:

            tasks = []
            for idx, sample in samples:
                task = self._search_single_sample_async(session, semaphore, idx, sample, sha1_file)
                tasks.append(task)

            # Execute searches in batches to avoid overwhelming Solr
            batch_size = 50
            all_results = {}

            for i in range(0, len(tasks), batch_size):
                batch_tasks = tasks[i:i + batch_size]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                for result in batch_results:
                    if isinstance(result, dict):
                        all_results.update(result)

            return all_results


    async def _search_single_sample_async(self, session, semaphore, idx, sample, sha1_file):
        """Single async search with semaphore limiting"""
        async with semaphore:
            escaped_sample = Utils.escape_solr_text(sample)
            query = f'"{escaped_sample}" AND NOT id:"{sha1_file}"'

            data = {
                "q": query,
                "fl": "id,resource_name,description",
                "rows": 1,
                "wt": "json"
            }

            try:
                async with session.post(f"{self.base_url}/query", data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        docs = result.get("response", {}).get("docs", [])

                        if docs:
                            return {idx: [{
                                "id": doc["id"],
                                "resource_name": doc.get("resource_name", ["Unknown"])[0] if isinstance(
                                    doc.get("resource_name"), list) else doc.get("resource_name", "Unknown"),
                                "description": doc.get("description", [""])[0] if isinstance(
                                    doc.get("description"), list) else doc.get("description", "")
                            } for doc in docs]}

            except Exception as e:
                logger.warning(f"Async search failed for sample {idx}: {e}")

            return {}

    def search_samples_async_wrapper(self, samples, sha1_file):
        """Wrapper to run async search from synchronous context"""
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, use ThreadPoolExecutor
                with ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.async_search_samples(samples, sha1_file))
                    return future.result()
            else:
                # If no loop is running, run directly
                return loop.run_until_complete(self.async_search_samples(samples, sha1_file))
        except RuntimeError:
            # No event loop exists, create new one
            return asyncio.run(self.async_search_samples(samples, sha1_file))


    def batch_search_samples(self, samples, sha1_file):
        return self.search_samples_individual(samples, sha1_file)

    def search_samples_individual(self, samples, sha1_file):
        """Search samples individually with accurate results"""
        results = {}

        for idx, sample in samples:
            try:
                escaped_sample = Utils.escape_solr_text(sample)
                query = f'"{escaped_sample}" AND NOT id:"{sha1_file}"'

                # Use pysolr with session reuse for individual searches
                search_results = self.solr_client.search(
                    query,
                    fl="id,resource_name,description",
                    rows=1
                )

                if search_results:
                    results[idx] = [{
                        "id": doc["id"],
                        "resource_name": doc.get("resource_name", ["Unknown"])[0] if isinstance(
                            doc.get("resource_name"), list) else doc.get("resource_name", "Unknown"),
                        "description": doc.get("description", [""])[0] if isinstance(
                            doc.get("description"), list) else doc.get("description", "")
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
                "literal.resource_name": filename
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


