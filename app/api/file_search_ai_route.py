import re
import logging
import requests
from flask import request
from flask_restful import Resource
from ..config import Config
from ..services.solr_service import SolrService
from ..utils import Utils


logger = logging.getLogger(__name__)

class FileSearchAI(Resource):
    def __init__(self):
        self.solr_service = SolrService()

    def post(self):
        data = request.json
        filename = data.get('filename', '')
        content = data.get('content', '')
        mimetype = data.get('mimetype', '')

        expmin = 6
        expmax = 8
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

            samples_scanned = 0
            samples_copied = 0
            current_sources = None
            output = []

            # Split document into lines
            lines = [line.strip() for line in document.split('\n') if line.strip()]

            for line_num, text in enumerate(lines, 1):
                while True:
                    match = re.search(r'(\S*\w\S*([\s.,-]+|$)+){' + str(expmin) + ',' + str(expmax) + '}', text)
                    if not match:
                        break
                    sample, possample = match.group(0), match.start()
                    presample = text[:possample]
                    text = text[possample + len(sample):]

                    sample = self._clean_search_sample(sample)
                    if not sample or len(sample.strip()) < 3:  # Skip very short samples
                        output.append({"type": "text", "content": presample + sample})
                        continue

                    samples_scanned += 1
                    words_in_sample = len(sample.split())
                    words_scanned += words_in_sample

                    output.append({"type": "text", "content": presample})

                    # Search for sample in Solr
                    logger.debug(f"Searching for sample {samples_scanned} in Solr database")
                    data = {
                        "q": f'"{Utils.escape_solr_text(sample)}"',
                        "fl": "id,resource_name,description",
                        "rows": rows
                    }
                    response = requests.post(f"{Config.SOLR_URL}/query", data=data)
                    result = response.json()

                    if result.get("response", {}).get("numFound", 0) > 0:
                        samples_copied += 1
                        words_copied += words_in_sample
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

                        if current_sources != new_sources:
                            current_sources = new_sources
                            for source_id in new_sources:
                                output.append({
                                    "type": "marker",
                                    "id": f"{source_id}",
                                    "color": sources[source_id]["color"],
                                    "name": sources[source_id]["name"]
                                })

                        output.append({
                            "type": "highlight",
                            "content": sample
                        })
                    else:
                        logger.debug(f"No matches found for sample {samples_scanned}")
                        output.append({"type": "text", "content": sample})

                output.append({"type": "text", "content": text})
                output.append({"type": "br"})

            # Calculate ratios
            words_original = words_scanned - words_copied
            words_original_ratio = words_original / words_scanned if words_scanned else 0
            samples_original = samples_scanned - samples_copied
            samples_original_ratio = samples_original / samples_scanned if samples_scanned else 0


            # Sort sources by words
            sorted_sources = sorted(sources.items(), key=lambda x: x[1]["words"], reverse=True)

            markdown_output = self._generate_markdown_output(output, [
                {
                    "id": source_id,
                    "color": info["color"],
                    "name": info["name"],
                } for source_id, info in sorted_sources
            ], {
                "words_doctotal": words_doctotal,
                "words_scanned": words_scanned,
                "words_original": words_original,
                "words_copied": words_copied,
                "words_original_ratio": words_original_ratio,
                "samples_scanned": samples_scanned,
                "samples_original": samples_original,
                "samples_copied": samples_copied,
                "samples_original_ratio": samples_original_ratio
            })

            # result = {
            #     "filename": filename,
            #     "metrics": {
            #         "words_doctotal": words_doctotal,
            #         "words_scanned": words_scanned,
            #         "words_original": words_original,
            #         "words_copied": words_copied,
            #         "words_original_ratio": words_original_ratio,
            #         "samples_scanned": samples_scanned,
            #         "samples_original": samples_original,
            #         "samples_copied": samples_copied,
            #         "samples_original_ratio": samples_original_ratio
            #     },
            #     "sources": [
            #         {
            #             "id": source_id,
            #             "color": info["color"],
            #             "name": info["name"],
            #         } for source_id, info in sorted_sources
            #     ],
            #     "output": output
            # }

            result = {
                "session_id": "abc123",
                "status": "success",
                "content_markdown": markdown_output,
                "meta": {
                    "model": "gpt-4o",
                    "response_time_ms": 1420,
                    "token_used": 312
                }
            }

            return result, 200
        except Exception as e:
            logger.error(str(e))
            return {}, 500




    def _generate_markdown_output(self, output, sources, metrics):
        markdown_content = []
        markdown_content.append("# Báo cáo đánh giá trùng lặp\n")
        markdown_content.append("## Tổng quan\n")
        markdown_content.append(f"- **Tổng số từ đã quét**: {metrics['words_scanned']}")
        markdown_content.append(
            f"- **Số từ không sao chép**: {metrics['words_original']} ({metrics['words_original_ratio']:.1%})")
        markdown_content.append(
            f"- **Số từ sao chép**: {metrics['words_copied']} ({(1 - metrics['words_original_ratio']):.1%})")
        markdown_content.append(f"- **Tổng số mẫu đã quét**: {metrics['samples_scanned']}")
        markdown_content.append(
            f"- **Số mẫu không sao chép**: {metrics['samples_original']} ({metrics['samples_original_ratio']:.1%})")
        markdown_content.append(f"- **Số mẫu sao chép**: {metrics['samples_copied']}\n")

        if sources:
            markdown_content.append("## Nguồn sao chép\n")
            for i, source in enumerate(sources, 1):
                markdown_content.append(f"{i}. **{source['name']}** (ID: {source['id']})")
            markdown_content.append("")

        markdown_content.append("## Phân tích nội dung\n")
        current_sources = set()
        current_color = None  # Track the current active color

        for item in output:
            if item["type"] == "text":
                markdown_content.append(item["content"])
            elif item["type"] == "highlight":
                if current_color:
                    # Apply color background using HTML span with inline CSS
                    markdown_content.append(
                        f'<span style="background-color: #{current_color}; padding: 2px 4px; border-radius: 3px;">**{item["content"]}**</span>')
                else:
                    markdown_content.append(f"**{item['content']}**")
            elif item["type"] == "marker":
                current_color = item.get("color")  # Update the current color
                source_info = f"[Source: {item['name']}]"
                if source_info not in current_sources:
                    markdown_content.append(f"\n> {source_info}\n")
                    current_sources.add(source_info)
            elif item["type"] == "br":
                markdown_content.append("\n")
                current_color = None  # Reset color on line break

        return "\n".join(markdown_content)


    def _clean_search_sample(self, sample):
        """Clean and validate search sample"""
        if not sample:
            return sample

        # Remove problematic characters that can break Solr queries
        sample = re.sub(r'[^\w\s\.,;:!?\-\'\"()]', ' ', sample)  # Keep only safe characters
        sample = re.sub(r'\s+', ' ', sample)  # Normalize whitespace
        sample = sample.strip()

        # Remove very short or very long samples
        if len(sample) < 3 or len(sample) > 1000:
            return ""

        return sample



class MetadataSearchAI(Resource):
    def get(self):
        result = {
            "name": "Plagiarism Assistant",
            "description": "Phát hiện trùng lặp văn bản với kho dữ liệu nội sinh",
            "version": "1.2.0",
            "developer": "Nhóm ThaoP, Khanh, Quang",
            "capabilities": [
                "search"
            ],
            "supported_models": [
                {
                    "model_id": "gpt-4o",
                    "name": "GPT-4o",
                    "description": "Mô hình mạnh cho tóm tắt và giải thích chi tiết",
                    "accepted_file_types": [
                        "pdf",
                        "docx",
                        "txt",
                        "md"
                    ]
                }
            ],
            "sample_prompts": [
                "Kiểm tra trùng lặp văn bản",
                "Check đạo văn"
            ],
            "provided_data_types": [
                {
                    "type": "documents",
                    "description": "Danh sách và thông tin tóm tắt các tài liệu trùng lặp"
                }
            ],
            "contact": "thaop@neu.edu.vn",
            "status": "active"
        }
        return result, 200
