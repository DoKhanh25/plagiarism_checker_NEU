import re
import logging
import requests
from flask import request
from flask_restful import Resource
from ..config import Config
from ..services.sorl_service import SolrService
from ..utils import Utils
import openai
import os


logger = logging.getLogger(__name__)

class FileSearchAI(Resource):
    def __init__(self):
        self.solr_service = SolrService()

    def post(self):
        data = request.json
        filename = data.get('filename', '')
        content = data.get('content', '')
        mimetype = data.get('mimetype', '')

        expmin = 5
        expmax = 7
        multisource = True

        if(not filename or not content or not mimetype):
            return {
                "status": 0,
                "data": None,
                "message": "Thiếu thông tin tệp"
            }, 400

        try:
            # Extract text from the file content
            response = self.solr_service.extract_text(
                filename=filename,
                content=content,
                mimetype=mimetype
            )

            if response.status_code != 200:
                error_msg = f"Không thể kết nối đến máy chủ Solr cho tệp {filename}. Status code: {response.status_code}"
                logger.error(error_msg)
                return {
                    "status": 0,
                    "data": None,
                    "message": error_msg
                }, 500

            result = response.json()

            if result.get("responseHeader", {}).get("status", 0) != 0:
                error_msg = f"Không thể trích xuất văn bản từ {filename}"
                logger.error(
                    f"{error_msg}. Solr response status: {result.get('responseHeader', {}).get('status', 'unknown')}")
                return {
                    "status": 0,
                    "data": None,
                    "message": error_msg
                }, 500

            document = result.get('file', "")
            rows = 10 if multisource else 1

            # Initialize metrics
            sources = {}
            words_doctotal = len(document.split())
            words_scanned = 0
            words_copied = 0
            chars_doctotal = len(document)
            chars_scanned = 0
            chars_copied = 0
            samples_scanned = 0
            samples_copied = 0

            # Split document into lines
            lines = [line.strip() for line in document.split('\n') if line.strip()]

            for line_num, text in enumerate(lines, 1):
                while True:
                    match = re.search(r'(\S*\w\S*([\s.,-]+|$)+){' + str(expmin) + ',' + str(expmax) + '}', text)
                    if not match:
                        break
                    sample, possample = match.group(0), match.start()
                    text = text[possample + len(sample):]

                    samples_scanned += 1
                    words_in_sample = len(sample.split())
                    words_scanned += words_in_sample
                    chars_scanned += len(sample)

                    # Search for sample in Solr
                    logger.debug(f"Searching for sample {samples_scanned} in Solr database")
                    data = {
                        "q": f'"{Utils.escape_solr_text(sample)}"',
                        "fl": "id,resource_name,description",
                        "rows": rows
                    }
                    response = requests.post(f"{Config.SORL_URL}/query", data=data)
                    result = response.json()

                    if result.get("response", {}).get("numFound", 0) > 0:
                        samples_copied += 1
                        words_copied += words_in_sample
                        chars_copied += len(sample)
                        new_sources = {}

                        logger.debug(f"Found {result['response']['numFound']} matches for sample {samples_scanned}")

                        for doc in result["response"]["docs"]:
                            source_id = doc["id"]
                            sources[source_id] = sources.get(source_id, {
                                "color": source_id[:6],
                                "name": doc.get("resource_name", ["Unknown"])[0],
                                "description": doc.get("description", [""])[0],
                                "words": 0,
                                "samples": 0
                            })
                            sources[source_id]["words"] += words_in_sample
                            sources[source_id]["samples"] += 1
                            new_sources[source_id] = True
                    else:
                        logger.debug(f"No matches found for sample {samples_scanned}")

            # Calculate ratios
            chars_original = chars_scanned - chars_copied
            chars_original_ratio = chars_original / chars_scanned if chars_scanned else 0
            words_original = words_scanned - words_copied
            words_original_ratio = words_original / words_scanned if words_scanned else 0
            samples_original = samples_scanned - samples_copied
            samples_original_ratio = samples_original / samples_scanned if samples_scanned else 0

            logger.info(f"Plagiarism analysis completed for {filename}")
            logger.info(f"Samples scanned: {samples_scanned}, copied: {samples_copied}, original: {samples_original}")
            logger.info(f"Words scanned: {words_scanned}, copied: {words_copied}, original: {words_original}")
            logger.info(f"Characters scanned: {chars_scanned}, copied: {chars_copied}, original: {chars_original}")
            logger.info(
                f"Originality ratio - Words: {words_original_ratio:.2%}, Characters: {chars_original_ratio:.2%}")

            # Sort sources by words
            sorted_sources = sorted(sources.items(), key=lambda x: x[1]["words"], reverse=True)
            logger.debug(f"Found {len(sorted_sources)} sources for plagiarism matches")

            result = {
                "filename": filename,
                "metrics": {
                    "words_doctotal": words_doctotal,
                    "words_scanned": words_scanned,
                    "words_original": words_original,
                    "words_copied": words_copied,
                    "words_original_ratio": words_original_ratio,
                    "samples_scanned": samples_scanned,
                    "samples_original": samples_original,
                    "samples_copied": samples_copied,
                    "samples_original_ratio": samples_original_ratio
                },
                "sources": [
                    {
                        "id": info["id"],
                        "name": info["name"],
                        "words": info["words"],
                        "samples": info["samples"]
                    } for source_id, info in sorted_sources
                ]
            }

            return result, 200
        except Exception as e:
            logger.error(str(e))
            return {}, 500
