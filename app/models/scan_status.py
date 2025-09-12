from datetime import datetime
from ..database import db

class ScanStatus(db.Model):
    __tablename__ = 'scan_status'

    id = db.Column(db.BigInteger, primary_key=True)
    document_id = db.Column(db.BigInteger, db.ForeignKey('documents.id'), nullable=False)
    created_scan_date = db.Column(db.DateTime, default=datetime.utcnow)
    finished_scan_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')  # e.g., 'pending', 'in_progress', 'completed', 'failed'

    # Relationships
    scan_result = db.relationship('ScanResult', backref='scan_status', uselist=False, lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'created_scan_date': self.created_scan_date.isoformat() if self.created_scan_date else None,
            'finished_scan_date': self.finished_scan_date.isoformat() if self.finished_scan_date else None,
            'status': self.status
        }