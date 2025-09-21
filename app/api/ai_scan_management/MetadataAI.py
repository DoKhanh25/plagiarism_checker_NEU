from flask_restful import Resource


"""
Author: Khanh Trong Do
Created: 20-09-2025
Description: Provides metadata information about the AI service.
"""
class MetadataAI(Resource):
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
                    "model_id": "TEXT",
                    "name": "TEXT",
                    "description": "Truyền vào một đoạn văn bản, kiểm tra độ trùng lặp",
                    "accepted_file_types": [
                        "pdf",
                        "docx",
                        "txt",
                        "md"
                    ]
                },
                {
                    "model_id": "FILE",
                    "name": "FILE",
                    "description": "Truyền vào một đoạn một file, trả ra mức độ trùng lặp của file",
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
