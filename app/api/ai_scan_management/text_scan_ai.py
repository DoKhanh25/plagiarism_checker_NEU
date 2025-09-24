import re
import logging
from flask import request
from flask_restful import Resource
from ...services.solr_service import SolrService
from .metadata_ai import metadata
import time
logger = logging.getLogger(__name__)

"""
Author: Khanh Trong Do
Created: 20-09-2025
Description: Provides a service connect to AI Agent for text scanning and plagiarism detection.
"""
class TextScanAI(Resource):
    def __init__(self):
        self.solr_service = SolrService()

    def post(self):
        start_time = time.time()

        data = request.json

        content = data.get('prompt', '')
        user = data.get('user', 'unknown')
        session_id = data.get('session_id', '')
        model_id = data.get('model_id', '')

        expmin = 6
        expmax = 9
        multisource = True

        if not model_id:
            return {
                "session_id": session_id,
                "status": "error",
                "content_markdown": None,
                "meta": None,
                "attachments": None
            }, 500

        if not model_id or (model_id not in [m['model_id'] for m in metadata['supported_models']]):
            return {
                "session_id": session_id,
                "status": "error",
                "content_markdown": None,
                "meta": None,
                "attachments": None
            }, 500


        if not content or content == "":
            return {
                "session_id": session_id,
                "status": "error",
                "content_markdown": None,
                "meta": None,
                "attachments": None
            }, 500

        try:
            document = content

            sha1_temp = "temporary_id"
            result = self.process_document_optimized(document, sha1_temp, expmin, expmax, multisource)
            markdown_output = self._generate_markdown_output(result["output"], result["sources"], result["metrics"])

            end_time = time.time()
            response_time = int((end_time - start_time) * 1000)

            response_result = {
                "session_id": session_id,
                "status": "success",
                "content_markdown": markdown_output,
                "meta": {
                    "model": model_id,
                    "response_time_ms": response_time,
                    "tokens_used": 0
                },
                "attachments": None
            }

            return response_result, 200
        except Exception as e:
            logger.error(str(e))
            return {}, 500

    def process_document_optimized(self, document, sha1_file, expmin, expmax, multisource):

        samples_with_positions = []
        lines = [line.strip() for line in document.split('\n') if line.strip()]

        # Extract all samples with proper positioning
        for line_num, text in enumerate(lines, 1):
            line_start = 0
            while True:
                match = re.search(r'(\S*\w\S*([\s.,-]+|$)+){' + str(expmin) + ',' + str(expmax) + '}', text[line_start:])
                if not match:
                    break

                sample = match.group(0).strip()
                sample = self._clean_search_sample(sample)

                if sample and len(sample.strip()) >= 3:
                    samples_with_positions.append({
                        'index': len(samples_with_positions),
                        'sample': sample,
                        'line_num': line_num,
                        'start_pos': line_start + match.start(),
                        'end_pos': line_start + match.end(),
                        'text_context': text
                    })

                line_start += match.end()

        logger.info(f"Found {len(samples_with_positions)} samples to process")

        # Use optimized search method to get all results at once
        samples_for_search = [(item['index'], item['sample']) for item in samples_with_positions]
        search_results = self.solr_service.search_samples(samples_for_search)

        logger.info(f"Completed individual searches, found matches for {len(search_results)} samples")
        return self._build_output_with_results(document, samples_with_positions, search_results, sha1_file, multisource)

    def _build_output_with_results(self, document, samples_with_positions, search_results, sha1_file, multisource):
        sources = {}
        words_doctotal = len(document.split())
        words_scanned = 0
        words_copied = 0
        chars_doctotal = len(document)
        chars_scanned = 0
        chars_copied = 0
        samples_scanned = 0
        samples_copied = 0
        current_sources = None
        output = []

        lines = [line.strip() for line in document.split('\n') if line.strip()]

        for line_num, text in enumerate(lines, 1):
            line_samples = [s for s in samples_with_positions if s['line_num'] == line_num]
            line_samples.sort(key=lambda x: x['start_pos'])

            current_pos = 0

            for sample_info in line_samples:
                sample = sample_info['sample']
                start_pos = sample_info['start_pos']
                end_pos = sample_info['end_pos']
                sample_idx = sample_info['index']

                # Add text before sample
                presample = text[current_pos:start_pos]
                output.append({"type": "text", "content": presample})

                # Update metrics
                samples_scanned += 1
                words_in_sample = len(sample.split())
                words_scanned += words_in_sample
                chars_scanned += len(sample)

                # Check if sample has matches
                if sample_idx in search_results:
                    samples_copied += 1
                    words_copied += words_in_sample
                    chars_copied += len(sample)
                    new_sources = {}

                    docs = search_results[sample_idx][:10 if multisource else 1]

                    for doc in docs:
                        source_id = doc["id"]
                        sources[source_id] = sources.get(source_id, {
                            "color": source_id[:6],
                            "name": doc.get("resource_name", "Unknown"),
                            "description": doc.get("description", ""),
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
                                "id": f"{sha1_file}_{source_id}",
                                "color": sources[source_id]["color"],
                                "name": sources[source_id]["name"]
                            })

                    output.append({"type": "highlight", "content": sample})
                else:
                    output.append({"type": "text", "content": sample})

                current_pos = end_pos

            # Add remaining text in line
            remaining_text = text[current_pos:]
            output.append({"type": "text", "content": remaining_text})
            output.append({"type": "br"})

        # Calculate ratios
        chars_original = chars_scanned - chars_copied
        chars_original_ratio = chars_original / chars_scanned if chars_scanned else 0
        words_original = words_scanned - words_copied
        words_original_ratio = words_original / words_scanned if words_scanned else 0
        samples_original = samples_scanned - samples_copied
        samples_original_ratio = samples_original / samples_scanned if samples_scanned else 0

        # Sort sources by words
        sorted_sources = sorted(sources.items(), key=lambda x: x[1]["words"], reverse=True)

        return {
            "filename": "text",
            "metrics": {
                "chars_doctotal": chars_doctotal,
                "chars_scanned": chars_scanned,
                "chars_original": chars_original,
                "chars_copied": chars_copied,
                "chars_original_ratio": chars_original_ratio,
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
                    "id": source_id,
                    "color": info["color"],
                    "name": info["name"],
                    "description": info["description"],
                    "words": info["words"],
                    "samples": info["samples"]
                } for source_id, info in sorted_sources
            ],
            "output": output
        }



    def _clean_search_sample(self, sample):
        if not sample:
            return sample

        sample = re.sub(r'[^\w\s\.,;:!?\-\'\"()]', ' ', sample)  # Keep only safe characters
        sample = re.sub(r'\s+', ' ', sample)  # Normalize whitespace
        sample = sample.strip()

        if len(sample) < 3 or len(sample) > 1000:
            return ""

        return sample

    def _generate_markdown_output(self, output, sources, metrics):
        sources_list = ""
        if sources:
            for i, source in enumerate(sources, 1):
                sources_list += f"{i}. **{source['name']}** (ID: {source['id']})\n"

        content_analysis = ""
        current_sources = set()
        current_color = None

        for item in output:
            if item["type"] == "text":
                content_analysis += item["content"]
            elif item["type"] == "highlight":
                if current_color:
                    content_analysis += f'<span style="background-color: #{current_color}; padding: 2px 4px; border-radius: 3px;">**{item["content"]}**</span>'
                else:
                    content_analysis += f"**{item['content']}**"
            elif item["type"] == "marker":
                current_color = item.get("color")
                source_info = f"[Source: {item['name']}]"
                if source_info not in current_sources:
                    content_analysis += f"\n\n> {source_info}\n\n"
                    current_sources.add(source_info)
            elif item["type"] == "br":
                content_analysis += "\n"
                current_color = None

        markdown_content = f"""# Báo cáo đánh giá trùng lặp

    ## Tổng quan

    - **Tổng số từ đã quét**: {metrics['words_scanned']}
    - **Số từ không sao chép**: {metrics['words_original']} ({metrics['words_original_ratio']:.1%})
    - **Số từ sao chép**: {metrics['words_copied']} ({(1 - metrics['words_original_ratio']):.1%})
    - **Tổng số mẫu đã quét**: {metrics['samples_scanned']}
    - **Số mẫu không sao chép**: {metrics['samples_original']} ({metrics['samples_original_ratio']:.1%})
    - **Số mẫu sao chép**: {metrics['samples_copied']}

    ## Nguồn sao chép

    {sources_list}
    ## Phân tích nội dung

    {content_analysis}
    """
        return markdown_content
