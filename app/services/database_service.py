from typing import List, Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    _instance = None
    _db = None

    def __init__(self, db=None):
        # Ensure db is set if this is first initialization
        if DatabaseService._db is None and db is not None:
            DatabaseService._db = db
        self.db = DatabaseService._db

    def __new__(cls, db=None):
        if cls._instance is None:
            cls._instance = super(DatabaseService, cls).__new__(cls)
            cls._db = db
        return cls._instance

    @property
    def db(self):
        return self._db

    @db.setter
    def db(self, value):
        self._db = value

    def create_document(self, research_name: str, file_name: str, file_hash: str, 
                       description: str = None, file_path: str = None, 
                       mimetype: str = None, file_size: int = None, 
                       author: str = None,
                        is_enable: bool = None,
                        is_included_in_solr: bool = None) -> Optional[Any]:
        """Create a new document record"""
        try:
            from ..models.document import Document
            
            document = Document(
                research_name=research_name,
                file_name=file_name,
                file_hash=file_hash,
                description=description,
                file_path=file_path,
                mimetype=mimetype,
                file_size=file_size,
                author=author,
                is_enable = is_enable if is_enable is not None else True,
                is_included_in_solr=is_included_in_solr if is_included_in_solr is not None else True
            )
            
            self.db.session.add(document)
            self.db.session.commit()
            logger.info(f"Created document with ID: {document.id}")
            return document
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error creating document: {str(e)}")
            raise Exception(f"Database error: {str(e)}")

    def get_document_by_hash(self, file_hash: str) -> Optional[Any]:
        """Get document by file hash"""
        try:
            from ..models.document import Document
            return Document.query.filter_by(file_hash=file_hash).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting document by hash: {str(e)}")
            raise Exception(f"Database error: {str(e)}")

    def create_scan_status(self, document_id: int,
                           status: str = 'pending') -> Optional[Any]:
        """Create a new scan status record"""
        try:
            from ..models.scan_status import ScanStatus
            
            scan_status = ScanStatus(
                document_id=document_id,
                status=status,
            )
            
            self.db.session.add(scan_status)
            self.db.session.commit()
            logger.info(f"Created scan status with ID: {scan_status.id}")
            return scan_status
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error creating scan status: {str(e)}")
            raise Exception(f"Database error: {str(e)}")

    def update_scan_status(self, scan_status_id: int, status: str, finished_date=None) -> bool:
        """Update scan status"""
        try:
            from ..models.scan_status import ScanStatus
            
            scan_status = ScanStatus.query.get(scan_status_id)
            if scan_status:
                scan_status.status = status
                if finished_date:
                    scan_status.finished_scan_date = finished_date
                self.db.session.commit()
                logger.info(f"Updated scan status ID: {scan_status_id}")
                return True
            return False
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error updating scan status: {str(e)}")
            raise Exception(f"Database error: {str(e)}")

    def create_scan_result(self, status_id: int, metrics: Dict[str, Any], 
                          parameters: Dict[str, Any], output_data: Dict = None) -> Optional[Any]:
        """Create a new scan result record"""
        try:
            from ..models.scan_result import ScanResult
            
            scan_result = ScanResult(
                status_id=status_id,
                chars_doctotal=metrics.get('chars_doctotal', 0),
                chars_scanned=metrics.get('chars_scanned', 0),
                chars_copied=metrics.get('chars_copied', 0),
                chars_original=metrics.get('chars_original', 0),
                chars_original_ratio=metrics.get('chars_original_ratio', 0.0),
                words_doctotal=metrics.get('words_doctotal', 0),
                words_scanned=metrics.get('words_scanned', 0),
                words_copied=metrics.get('words_copied', 0),
                words_original=metrics.get('words_original', 0),
                words_original_ratio=metrics.get('words_original_ratio', 0.0),
                samples_scanned=metrics.get('samples_scanned', 0),
                samples_copied=metrics.get('samples_copied', 0),
                samples_original=metrics.get('samples_original', 0),
                samples_original_ratio=metrics.get('samples_original_ratio', 0.0),
                exp_min=parameters.get('exp_min', 3),
                exp_max=parameters.get('exp_max', 5),
                multi_source=parameters.get('multi_source', False),
                output_data=output_data
            )
            
            self.db.session.add(scan_result)
            self.db.session.commit()
            logger.info(f"Created scan result with ID: {scan_result.id}")
            return scan_result
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error creating scan result: {str(e)}")
            raise Exception(f"Database error: {str(e)}")

    def create_scan_resources(self, scan_result_id: int, sources: List[Dict[str, Any]]) -> bool:
        """Create scan resource records"""
        try:
            from ..models.scan_resource import ScanResource
            
            for source in sources:
                scan_resource = ScanResource(
                    scan_result_id=scan_result_id,
                    source_id=source.get('id', ''),
                    color=source.get('color', ''),
                    name=source.get('name', ''),
                    description=source.get('description', ''),
                    words=source.get('words', 0),
                    samples=source.get('samples', 0)
                )
                self.db.session.add(scan_resource)
            
            self.db.session.commit()
            logger.info(f"Created {len(sources)} scan resources for result ID: {scan_result_id}")
            return True
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error creating scan resources: {str(e)}")
            raise Exception(f"Database error: {str(e)}")

    def get_documents(self, limit: int = 100, offset: int = 0) -> List[Any]:
        """Get documents with pagination"""
        try:
            from ..models.document import Document
            return Document.query.offset(offset).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting documents: {str(e)}")
            raise Exception(f"Database error: {str(e)}")

    def get_document_with_scans(self, document_id: int) -> Optional[Any]:
        """Get document with its scan statuses and results"""
        try:
            from ..models.document import Document
            return Document.query.get(document_id)
        except SQLAlchemyError as e:
            logger.error(f"Error getting document with scans: {str(e)}")
            raise Exception(f"Database error: {str(e)}")

    def get_documents_with_scan_status(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get documents with their latest scan statuses"""
        """Get documents with their latest scan status details"""
        try:
            from ..models.document import Document
            from ..models.scan_status import ScanStatus
            from sqlalchemy import desc

            # Query documents with their latest scan status
            results = self.db.session.query(
                Document,
                ScanStatus
            ).outerjoin(
                ScanStatus,
                Document.id == ScanStatus.document_id
            ).order_by(
                Document.upload_date.desc(),
                ScanStatus.created_scan_date.desc()
            ).offset(offset).limit(limit).all()

            # Format the results
            documents = []
            for doc, status in results:
                document_data = {
                    "id": doc.id,
                    "research_name": doc.research_name,
                    "file_name": doc.file_name,
                    "file_hash": doc.file_hash,
                    "description": doc.description,
                    "file_size": doc.file_size,
                    "author": doc.author,
                    "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
                    "is_enable": doc.is_enable,
                    "scan_status": {
                        "id": status.id if status else None,
                        "status": status.status if status else None,
                        "created_scan_date": status.created_scan_date.isoformat() if status and status.created_scan_date else None,
                        "finished_scan_date": status.finished_scan_date.isoformat() if status and status.finished_scan_date else None
                    } if status else None
                }
                documents.append(document_data)

            return documents

        except SQLAlchemyError as e:
            logger.error(f"Error getting documents with scan status: {str(e)}")
            raise Exception(f"Database error: {str(e)}")

    def get_scan_result_by_scan_status_id(self, status_id: int) -> Dict:
        """Get scan result and resources for a given scan status ID"""
        try:
            from ..models.scan_result import ScanResult
            from ..models.scan_resource import ScanResource

            # Get the scan result
            scan_result = ScanResult.query.filter_by(status_id=status_id).first()
            if not scan_result:
                return None

            # Get associated resources
            scan_resources = ScanResource.query.filter_by(scan_result_id=scan_result.id).all()

            # Format the result
            result = {
                "id": scan_result.id,
                "status_id": scan_result.status_id,
                "metrics": {
                    "chars_doctotal": scan_result.chars_doctotal,
                    "chars_scanned": scan_result.chars_scanned,
                    "chars_copied": scan_result.chars_copied,
                    "chars_original": scan_result.chars_original,
                    "chars_original_ratio": scan_result.chars_original_ratio,
                    "words_doctotal": scan_result.words_doctotal,
                    "words_scanned": scan_result.words_scanned,
                    "words_copied": scan_result.words_copied,
                    "words_original": scan_result.words_original,
                    "words_original_ratio": scan_result.words_original_ratio,
                    "samples_scanned": scan_result.samples_scanned,
                    "samples_copied": scan_result.samples_copied,
                    "samples_original": scan_result.samples_original,
                    "samples_original_ratio": scan_result.samples_original_ratio
                },
                "parameters": {
                    "exp_min": scan_result.exp_min,
                    "exp_max": scan_result.exp_max,
                    "multi_source": scan_result.multi_source
                },
                "resources": [
                    {
                        "id": resource.source_id,
                        "color": resource.color,
                        "name": resource.name,
                        "description": resource.description,
                        "words": resource.words,
                        "samples": resource.samples
                    } for resource in scan_resources
                ],
                "output_data": scan_result.output_data
            }

            return result

        except SQLAlchemyError as e:
            logger.error(f"Error getting scan result: {str(e)}")
            raise Exception(f"Database error: {str(e)}")