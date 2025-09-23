
import logging
from .file_upload_route import SingleFileUpload
from .file_upload_route import SingleFileSearch
from .file_upload_route import MultipleFileSearch
from .file_management_route import FileScanList
from .file_upload_route import DownloadExcelSample
from .file_management_route import FileScanResult

from .file_management.FileList import FileList
from .file_management.FileDownload import FileDownload
from .ai_scan_management.MetadataAI import MetadataAI
from .ai_scan_management.TextScanAI import TextScanAI
# Configure logger for this module
logger = logging.getLogger(__name__)





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

    # AI Scan Route
    api.add_resource(TextScanAI, '/api/file-search/ai/ask')
    api.add_resource(MetadataAI, '/api/file-search/ai/metadata')


